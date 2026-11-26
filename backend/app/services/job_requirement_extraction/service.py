"""
Job Requirement Extraction Service
Phase 6 | Feature 36: Job Requirement Extraction
Orchestrates caching, Ollama structured extraction, importance counting, and DB persistence.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_description import JobDescription
from app.models.job_requirement_analysis import JobRequirementAnalysis
from app.schemas.job_requirement_analysis import (
    EducationRequirementSchema,
    ExperienceRequirementSchema,
    ExtractedRequirementItem,
    JobRequirementAnalysisData,
    RequirementSummaryCounts,
)
from app.services.job_requirement_extraction.ai_extractor import JobRequirementAIExtractor

logger = logging.getLogger(__name__)


def _compute_summary_counts(
    technical_skills: List[ExtractedRequirementItem],
    exp_requirements: List[ExtractedRequirementItem],
    soft_skills: List[ExtractedRequirementItem],
    domain_knowledge: List[ExtractedRequirementItem],
    other_requirements: List[ExtractedRequirementItem],
) -> RequirementSummaryCounts:
    all_items = technical_skills + exp_requirements + soft_skills + domain_knowledge + other_requirements
    counts = {"Mandatory": 0, "Preferred": 0, "Optional": 0, "Unspecified": 0}
    for item in all_items:
        counts[item.importance] = counts.get(item.importance, 0) + 1
    return RequirementSummaryCounts(
        mandatory_count=counts["Mandatory"],
        preferred_count=counts["Preferred"],
        optional_count=counts["Optional"],
        unspecified_count=counts["Unspecified"],
        total_requirements=len(all_items),
    )


def _to_data(
    analysis: JobRequirementAnalysis,
    record: JobDescription,
    cached: bool = False,
) -> JobRequirementAnalysisData:
    tech = [ExtractedRequirementItem.model_validate(i) for i in (analysis.technical_skills or [])]
    edu = EducationRequirementSchema.model_validate(analysis.education or {})
    exp = ExperienceRequirementSchema.model_validate(analysis.experience or {})
    soft = [ExtractedRequirementItem.model_validate(i) for i in (analysis.soft_skills or [])]
    domain = [ExtractedRequirementItem.model_validate(i) for i in (analysis.domain_knowledge or [])]
    other = [ExtractedRequirementItem.model_validate(i) for i in (analysis.other_requirements or [])]

    meta = analysis.analysis_metadata or {}
    summary_counts = _compute_summary_counts(tech, exp.requirements, soft, domain, other)

    return JobRequirementAnalysisData(
        id=str(analysis.id),
        job_id=str(analysis.job_description_id),
        job_description_id=str(analysis.job_description_id),
        technical_skills=tech,
        education=edu,
        experience=exp,
        soft_skills=soft,
        domain_knowledge=domain,
        other_requirements=other,
        summary_counts=summary_counts,
        analysis_status=record.analysis_status,
        model_used=meta.get("model_used", ""),
        cached=cached,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


class JobRequirementExtractionService:
    """Service for extracting and persisting structured job requirements."""

    def __init__(self, ai_extractor: Optional[JobRequirementAIExtractor] = None):
        self.ai_extractor = ai_extractor or JobRequirementAIExtractor()

    def get_saved_analysis(
        self,
        db: Session,
        record: JobDescription,
    ) -> Optional[JobRequirementAnalysisData]:
        existing = db.execute(
            select(JobRequirementAnalysis).where(
                JobRequirementAnalysis.job_description_id == record.id
            )
        ).scalar_one_or_none()
        if not existing:
            return None
        return _to_data(existing, record, cached=True)

    async def extract_and_save(
        self,
        db: Session,
        record: JobDescription,
        force_recalculate: bool = False,
    ) -> JobRequirementAnalysisData:
        existing = db.execute(
            select(JobRequirementAnalysis).where(
                JobRequirementAnalysis.job_description_id == record.id
            )
        ).scalar_one_or_none()

        if existing and existing.content_hash == record.content_hash and not force_recalculate:
            logger.info(
                "Returning cached job requirement analysis for job_description_id=%s",
                record.id,
            )
            return _to_data(existing, record, cached=True)

        try:
            extracted = await self.ai_extractor.extract_requirements(
                description=record.raw_description,
                job_title=record.job_title,
                company_name=record.company_name,
                employment_type=record.employment_type,
                experience_required=record.experience_required,
            )
        except Exception:
            record.analysis_status = "FAILED"
            db.commit()
            raise

        tech_payload = [item.model_dump() for item in extracted.technical_skills]
        edu_payload = extracted.education.model_dump()
        exp_payload = extracted.experience.model_dump()
        soft_payload = [item.model_dump() for item in extracted.soft_skills]
        domain_payload = [item.model_dump() for item in extracted.domain_knowledge]
        other_payload = [item.model_dump() for item in extracted.other_requirements]
        metadata: Dict[str, Any] = {"model_used": self.ai_extractor.model}

        if existing:
            existing.technical_skills = tech_payload
            existing.education = edu_payload
            existing.experience = exp_payload
            existing.soft_skills = soft_payload
            existing.domain_knowledge = domain_payload
            existing.other_requirements = other_payload
            existing.content_hash = record.content_hash
            existing.analysis_metadata = metadata
            target = existing
        else:
            target = JobRequirementAnalysis(
                job_description_id=record.id,
                user_id=record.user_id,
                technical_skills=tech_payload,
                education=edu_payload,
                experience=exp_payload,
                soft_skills=soft_payload,
                domain_knowledge=domain_payload,
                other_requirements=other_payload,
                content_hash=record.content_hash,
                analysis_metadata=metadata,
            )
            db.add(target)

        # Sync summary fields onto JobDescription for downstream matching (#37+)
        mandatory = [s.name for s in extracted.technical_skills if s.importance == "Mandatory"]
        preferred = [s.name for s in extracted.technical_skills if s.importance == "Preferred"]
        if mandatory:
            record.mandatory_skills = mandatory
        if preferred:
            record.preferred_skills = preferred
        if extracted.education.required_degree or extracted.education.minimum_level:
            record.education_required = (
                extracted.education.required_degree or extracted.education.minimum_level
            )
        record.requirements = [
            item.name
            for item in (
                extracted.technical_skills
                + extracted.experience.requirements
                + extracted.other_requirements
            )
        ]
        record.analysis_status = "COMPLETED"

        db.commit()
        db.refresh(target)
        db.refresh(record)

        return _to_data(target, record, cached=False)


job_requirement_extraction_service = JobRequirementExtractionService()
