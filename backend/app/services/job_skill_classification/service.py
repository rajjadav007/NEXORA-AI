"""
Job Skill Classification Service
Phase 6 | Feature 37: Mandatory & Preferred Skills Classification
Orchestrates Feature #36 requirement reuse, Ollama classification, normalization, and DB persistence.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_description import JobDescription
from app.models.job_skill_classification import JobSkillClassification
from app.schemas.job_skill_classification import (
    ClassifiedSkillItem,
    JobSkillClassificationData,
    SkillClassificationSummary,
    compute_classification_summary,
    deduplicate_classified_skills,
)
from app.services.job_requirement_extraction.service import (
    job_requirement_extraction_service,
)
from app.services.job_skill_classification.ai_classifier import SkillClassificationAIExtractor

logger = logging.getLogger(__name__)


def _to_data(
    classification: JobSkillClassification,
    record: JobDescription,
    cached: bool = False,
) -> JobSkillClassificationData:
    skills = deduplicate_classified_skills(
        [ClassifiedSkillItem.model_validate(item) for item in (classification.skills or [])]
    )
    summary = compute_classification_summary(skills)
    meta = classification.analysis_metadata or {}

    return JobSkillClassificationData(
        id=str(classification.id),
        job_id=str(classification.job_description_id),
        job_description_id=str(classification.job_description_id),
        classification_summary=summary,
        skills=skills,
        analysis_status=record.analysis_status,
        model_used=meta.get("model_used", ""),
        cached=cached,
        created_at=classification.created_at,
        updated_at=classification.updated_at,
    )


def _collect_feature_36_skills(req_data: Any) -> List[Dict[str, Any]]:
    """Collect extracted skills from Feature #36 (technical, soft, domain knowledge)."""
    items: List[Dict[str, Any]] = []
    for group in (
        getattr(req_data, "technical_skills", []) or [],
        getattr(req_data, "soft_skills", []) or [],
        getattr(req_data, "domain_knowledge", []) or [],
    ):
        for item in group:
            items.append(
                {
                    "name": item.name,
                    "category": item.category,
                    "importance": item.importance,
                    "evidence": item.evidence,
                    "confidence": item.confidence,
                    "source_type": item.source_type,
                }
            )
    return items


class JobSkillClassificationService:
    """Service for classifying and persisting job skills with priority scoring."""

    def __init__(self, ai_classifier: Optional[SkillClassificationAIExtractor] = None):
        self.ai_classifier = ai_classifier or SkillClassificationAIExtractor()

    def get_saved_classification(
        self,
        db: Session,
        record: JobDescription,
    ) -> Optional[JobSkillClassificationData]:
        existing = db.execute(
            select(JobSkillClassification).where(
                JobSkillClassification.job_description_id == record.id
            )
        ).scalar_one_or_none()
        if not existing:
            return None
        return _to_data(existing, record, cached=True)

    async def classify_and_save(
        self,
        db: Session,
        record: JobDescription,
        force_recalculate: bool = False,
    ) -> JobSkillClassificationData:
        existing = db.execute(
            select(JobSkillClassification).where(
                JobSkillClassification.job_description_id == record.id
            )
        ).scalar_one_or_none()

        if existing and existing.content_hash == record.content_hash and not force_recalculate:
            logger.info(
                "Returning cached skill classification for job_description_id=%s",
                record.id,
            )
            return _to_data(existing, record, cached=True)

        # Reuse Feature #36 extracted requirements (run extraction if not yet persisted)
        req_data = job_requirement_extraction_service.get_saved_analysis(db=db, record=record)
        if req_data is None:
            req_data = await job_requirement_extraction_service.extract_and_save(
                db=db,
                record=record,
                force_recalculate=False,
            )

        extracted_skills = _collect_feature_36_skills(req_data)

        try:
            classified = await self.ai_classifier.classify_skills(
                description=record.raw_description,
                extracted_skills=extracted_skills,
                job_title=record.job_title,
                company_name=record.company_name,
            )
        except Exception:
            record.analysis_status = "FAILED"
            db.commit()
            raise

        deduped_skills = deduplicate_classified_skills(classified.skills)
        summary: SkillClassificationSummary = compute_classification_summary(deduped_skills)
        skills_payload = [item.model_dump() for item in deduped_skills]
        summary_payload = summary.model_dump()
        metadata: Dict[str, Any] = {
            "model_used": self.ai_classifier.model,
            "feature_36_requirement_id": req_data.id,
        }

        if existing:
            existing.classification_summary = summary_payload
            existing.skills = skills_payload
            existing.content_hash = record.content_hash
            existing.analysis_metadata = metadata
            target = existing
        else:
            target = JobSkillClassification(
                job_description_id=record.id,
                user_id=record.user_id,
                classification_summary=summary_payload,
                skills=skills_payload,
                content_hash=record.content_hash,
                analysis_metadata=metadata,
            )
            db.add(target)

        record.analysis_status = "COMPLETED"
        db.commit()
        db.refresh(target)
        db.refresh(record)

        return _to_data(target, record, cached=False)


job_skill_classification_service = JobSkillClassificationService()
