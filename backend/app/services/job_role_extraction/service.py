"""
Job Role Extraction Service
Phase 6 | Feature 35: Job Role Extraction
Orchestrates caching, Ollama structured extraction, explicit-vs-inferred provenance, and DB persistence.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_description import JobDescription
from app.models.job_role_analysis import JobRoleAnalysis
from app.schemas.job_role_analysis import (
    ExperienceLevelSchema,
    JobRoleAIStructuredOutput,
    JobRoleAnalysisData,
)
from app.services.job_role_extraction.ai_extractor import JobRoleAIExtractor

logger = logging.getLogger(__name__)


def _build_provenance(
    record: JobDescription,
    extracted: JobRoleAIStructuredOutput,
) -> tuple[Dict[str, Any], List[str]]:
    """Distinguish explicit posting facts from AI-inferred classifications."""
    explicit_facts: Dict[str, Any] = {
        "job_title_in_posting": record.job_title or None,
        "employment_type_in_posting": record.employment_type or None,
        "location_in_posting": record.location or None,
        "experience_in_posting": record.experience_required or None,
    }

    inferred_fields: List[str] = [
        "standardized_role",
        "department",
        "category",
        "seniority",
        "industry",
        "role_summary",
    ]
    if not record.employment_type and extracted.employment_type:
        inferred_fields.append("employment_type")
    if not record.experience_required and (
        extracted.experience_level.minimum_years is not None
        or extracted.experience_level.description
    ):
        inferred_fields.append("experience_level")
    if not record.location and extracted.work_arrangement != "Unknown":
        inferred_fields.append("work_arrangement")

    return explicit_facts, inferred_fields


def _to_data(
    analysis: JobRoleAnalysis,
    record: JobDescription,
    cached: bool = False,
) -> JobRoleAnalysisData:
    meta = analysis.analysis_metadata or {}
    return JobRoleAnalysisData(
        id=str(analysis.id),
        job_description_id=str(analysis.job_description_id),
        job_title=analysis.job_title,
        standardized_role=analysis.standardized_role,
        department=analysis.department,
        category=analysis.category,
        seniority=analysis.seniority,
        experience_level=ExperienceLevelSchema.model_validate(analysis.experience_level or {}),
        employment_type=analysis.employment_type,
        work_arrangement=analysis.work_arrangement,
        industry=analysis.industry,
        responsibilities=analysis.responsibilities or [],
        role_summary=analysis.role_summary,
        confidence_score=analysis.confidence_score,
        analysis_status=record.analysis_status,
        explicit_facts=meta.get("explicit_facts", {}),
        inferred_fields=meta.get("inferred_fields", []),
        model_used=meta.get("model_used", ""),
        cached=cached,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


class JobRoleExtractionService:
    """Service for extracting and persisting structured job role intelligence."""

    def __init__(self, ai_extractor: Optional[JobRoleAIExtractor] = None):
        self.ai_extractor = ai_extractor or JobRoleAIExtractor()

    def get_saved_analysis(
        self,
        db: Session,
        record: JobDescription,
    ) -> Optional[JobRoleAnalysisData]:
        existing = db.execute(
            select(JobRoleAnalysis).where(JobRoleAnalysis.job_description_id == record.id)
        ).scalar_one_or_none()
        if not existing:
            return None
        return _to_data(existing, record, cached=True)

    async def extract_and_save(
        self,
        db: Session,
        record: JobDescription,
        force_recalculate: bool = False,
    ) -> JobRoleAnalysisData:
        existing = db.execute(
            select(JobRoleAnalysis).where(JobRoleAnalysis.job_description_id == record.id)
        ).scalar_one_or_none()

        if existing and existing.content_hash == record.content_hash and not force_recalculate:
            logger.info("Returning cached job role analysis for job_description_id=%s", record.id)
            return _to_data(existing, record, cached=True)

        try:
            extracted = await self.ai_extractor.extract_role(
                description=record.raw_description,
                job_title=record.job_title,
                company_name=record.company_name,
                location=record.location,
                employment_type=record.employment_type,
                experience_required=record.experience_required,
            )
        except Exception:
            record.analysis_status = "FAILED"
            db.commit()
            raise

        explicit_facts, inferred_fields = _build_provenance(record, extracted)
        metadata = {
            "explicit_facts": explicit_facts,
            "inferred_fields": inferred_fields,
            "model_used": self.ai_extractor.model,
        }

        resolved_title = extracted.job_title or record.job_title or None
        resolved_employment = extracted.employment_type or record.employment_type or None
        exp_payload = extracted.experience_level.model_dump()

        if existing:
            existing.job_title = resolved_title
            existing.standardized_role = extracted.standardized_role
            existing.department = extracted.department
            existing.category = extracted.category
            existing.seniority = extracted.seniority
            existing.experience_level = exp_payload
            existing.employment_type = resolved_employment
            existing.work_arrangement = extracted.work_arrangement
            existing.industry = extracted.industry
            existing.responsibilities = extracted.responsibilities
            existing.role_summary = extracted.role_summary
            existing.confidence_score = extracted.confidence_score
            existing.content_hash = record.content_hash
            existing.analysis_metadata = metadata
            target = existing
        else:
            target = JobRoleAnalysis(
                job_description_id=record.id,
                user_id=record.user_id,
                job_title=resolved_title,
                standardized_role=extracted.standardized_role,
                department=extracted.department,
                category=extracted.category,
                seniority=extracted.seniority,
                experience_level=exp_payload,
                employment_type=resolved_employment,
                work_arrangement=extracted.work_arrangement,
                industry=extracted.industry,
                responsibilities=extracted.responsibilities,
                role_summary=extracted.role_summary,
                confidence_score=extracted.confidence_score,
                content_hash=record.content_hash,
                analysis_metadata=metadata,
            )
            db.add(target)

        record.analysis_status = "COMPLETED"
        db.commit()
        db.refresh(target)
        db.refresh(record)

        return _to_data(target, record, cached=False)


job_role_extraction_service = JobRoleExtractionService()
