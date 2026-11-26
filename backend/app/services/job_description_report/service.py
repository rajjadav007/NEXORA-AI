"""
Job Description Report Service
Phase 6 | Feature 38: Job Description Report
Aggregates Features #33-#37, validates prerequisites, generates AI insights, and persists versioned reports.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_description import JobDescription
from app.models.job_description_report import JobDescriptionReport
from app.schemas.job_description_report import (
    JobDescriptionReportData,
    JobReportAIStructuredOutput,
    JobReportEligibilityCriteria,
    JobReportOverview,
    JobReportRoleAnalysis,
    JobReportSkillClassification,
    JobReportTechnicalRequirements,
)
from app.schemas.job_requirement_analysis import ExtractedRequirementItem
from app.services.job_description_report.ai_insights import JobReportAIInsightsGenerator
from app.services.job_requirement_extraction.service import job_requirement_extraction_service
from app.services.job_role_extraction.service import job_role_extraction_service
from app.services.job_skill_classification.service import job_skill_classification_service

logger = logging.getLogger(__name__)

_CLOUD_KEYWORDS = (
    "aws",
    "amazon web services",
    "azure",
    "gcp",
    "google cloud",
    "cloudformation",
    "terraform",
    "cloudflare",
    "vercel",
    "heroku",
)


class PrerequisiteAnalysisMissingError(Exception):
    """Raised when one or more required upstream analyses (#35-#37) are missing."""

    def __init__(self, missing_features: List[str]):
        self.missing_features = missing_features
        super().__init__(
            "Prerequisite analysis missing. Please complete: " + ", ".join(missing_features) + "."
        )


def _is_cloud_skill(item: ExtractedRequirementItem) -> bool:
    name_lower = item.name.lower()
    return any(kw in name_lower for kw in _CLOUD_KEYWORDS)


def _bucket_technical_requirements(
    tech_skills: List[ExtractedRequirementItem],
) -> JobReportTechnicalRequirements:
    buckets = JobReportTechnicalRequirements()
    for item in tech_skills:
        cat = item.category
        if cat == "Programming Language":
            buckets.programming_languages.append(item)
        elif cat == "AI & Machine Learning":
            buckets.ai_and_machine_learning.append(item)
        elif cat in ("Framework & Library", "AI Framework"):
            buckets.frameworks_and_libraries.append(item)
        elif cat == "Database":
            buckets.databases.append(item)
        elif cat == "Tool & Platform":
            if _is_cloud_skill(item):
                buckets.cloud_technologies.append(item)
            else:
                buckets.tools_and_platforms.append(item)
        else:
            if _is_cloud_skill(item):
                buckets.cloud_technologies.append(item)
            else:
                buckets.other_technical_skills.append(item)
    return buckets


def _format_experience_summary(role_data: Any, req_data: Any, record: JobDescription) -> Optional[str]:
    if record.experience_required:
        return record.experience_required
    exp = getattr(req_data, "experience", None)
    if exp:
        if exp.minimum_years is not None and exp.maximum_years is not None:
            return f"{exp.minimum_years}-{exp.maximum_years} years"
        if exp.minimum_years is not None:
            return f"{exp.minimum_years}+ years"
        if exp.professional_experience:
            return exp.professional_experience
        if exp.fresher_eligible:
            return "Fresher eligible"
    role_exp = getattr(role_data, "experience_level", None)
    if role_exp and getattr(role_exp, "description", None):
        return role_exp.description
    return None


def _build_eligibility_criteria(
    req_data: Any,
    skill_data: Any,
    exp_summary: Optional[str],
) -> JobReportEligibilityCriteria:
    edu = req_data.education
    exp = req_data.experience

    required_edu = edu.required_degree or edu.minimum_level
    mandatory_skills = [s for s in skill_data.skills if s.classification == "Mandatory"]

    mandatory_quals: List[str] = []
    if required_edu:
        fields = f" in {', '.join(edu.required_fields)}" if edu.required_fields else ""
        mandatory_quals.append(f"{required_edu}{fields}")
    for cert in edu.required_certifications:
        mandatory_quals.append(f"Certification: {cert}")
    if exp_summary:
        mandatory_quals.append(f"Experience: {exp_summary}")

    important_tech = [s.name for s in mandatory_skills[:10]]

    return JobReportEligibilityCriteria(
        fresher_eligible=exp.fresher_eligible,
        required_experience=exp_summary,
        required_education=required_edu,
        mandatory_qualifications=mandatory_quals,
        important_technical_requirements=important_tech,
    )


def _compute_combined_hash(record: JobDescription, role_data: Any, req_data: Any, skill_data: Any) -> str:
    raw = "|".join([
        record.content_hash,
        str(role_data.updated_at.isoformat()),
        str(req_data.updated_at.isoformat()),
        str(skill_data.updated_at.isoformat()),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _to_data(
    report: JobDescriptionReport,
    record: JobDescription,
    cached: bool = False,
) -> JobDescriptionReportData:
    payload = dict(report.report_payload or {})
    meta = report.analysis_metadata or {}
    payload.update(
        {
            "id": str(report.id),
            "job_id": str(report.job_description_id),
            "job_description_id": str(report.job_description_id),
            "report_version": report.report_version,
            "version_number": report.version_number,
            "analysis_status": record.analysis_status,
            "model_used": meta.get("model_used", ""),
            "cached": cached,
            "generated_at": report.generated_at,
            "created_at": report.created_at,
            "updated_at": report.updated_at,
        }
    )
    return JobDescriptionReportData.model_validate(payload)


class JobDescriptionReportService:
    """Service for aggregating Features #33-#37 into a persisted, versioned Job Description Report."""

    def __init__(self, ai_insights_generator: Optional[JobReportAIInsightsGenerator] = None):
        self.ai_insights_generator = ai_insights_generator or JobReportAIInsightsGenerator()

    def get_saved_report(
        self,
        db: Session,
        record: JobDescription,
    ) -> Optional[JobDescriptionReportData]:
        existing = db.execute(
            select(JobDescriptionReport).where(
                JobDescriptionReport.job_description_id == record.id
            )
        ).scalar_one_or_none()
        if not existing:
            return None
        return _to_data(existing, record, cached=True)

    async def generate_and_save(
        self,
        db: Session,
        record: JobDescription,
        regenerate: bool = False,
    ) -> JobDescriptionReportData:
        # 1. Verify prerequisite analyses (#35, #36, #37)
        role_data = job_role_extraction_service.get_saved_analysis(db=db, record=record)
        req_data = job_requirement_extraction_service.get_saved_analysis(db=db, record=record)
        skill_data = job_skill_classification_service.get_saved_classification(db=db, record=record)

        missing: List[str] = []
        if role_data is None:
            missing.append("Feature #35 (Job Role Extraction)")
        if req_data is None:
            missing.append("Feature #36 (Job Requirement Extraction)")
        if skill_data is None:
            missing.append("Feature #37 (Skill Classification)")

        if missing:
            raise PrerequisiteAnalysisMissingError(missing)

        combined_hash = _compute_combined_hash(record, role_data, req_data, skill_data)
        existing = db.execute(
            select(JobDescriptionReport).where(
                JobDescriptionReport.job_description_id == record.id
            )
        ).scalar_one_or_none()

        if existing and existing.content_hash == combined_hash and not regenerate:
            logger.info("Returning cached job description report for job_description_id=%s", record.id)
            return _to_data(existing, record, cached=True)

        # 2. Aggregate deterministic sections from #33-#37
        exp_summary = _format_experience_summary(role_data, req_data, record)
        overview = JobReportOverview(
            job_title=record.job_title,
            company_name=record.company_name,
            location=record.location,
            employment_type=role_data.employment_type or record.employment_type,
            work_arrangement=role_data.work_arrangement,
            seniority_level=role_data.seniority,
            experience_requirements=exp_summary,
            industry=role_data.industry,
            job_description_summary=role_data.role_summary or record.raw_description[:320],
            source_type=record.source_type,
            source_url=record.source_url,
        )

        role_analysis = JobReportRoleAnalysis(
            standardized_role=role_data.standardized_role,
            department=role_data.department,
            category=role_data.category,
            seniority_level=role_data.seniority,
            role_summary=role_data.role_summary,
            main_responsibilities=role_data.responsibilities,
            industry=role_data.industry,
            confidence_score=role_data.confidence_score,
        )

        technical_requirements = _bucket_technical_requirements(req_data.technical_skills)

        skill_classification = JobReportSkillClassification(
            summary=skill_data.classification_summary,
            mandatory=[s for s in skill_data.skills if s.classification == "Mandatory"],
            preferred=[s for s in skill_data.skills if s.classification == "Preferred"],
            optional=[s for s in skill_data.skills if s.classification == "Optional"],
            unspecified=[s for s in skill_data.skills if s.classification == "Unspecified"],
        )

        eligibility_criteria = _build_eligibility_criteria(req_data, skill_data, exp_summary)

        # 3. Single Ollama call for complexity analysis & AI insights
        context_summary = {
            "role": {
                "standardized_role": role_data.standardized_role,
                "seniority": role_data.seniority,
                "industry": role_data.industry,
                "responsibilities": role_data.responsibilities[:8],
            },
            "skill_counts": skill_data.classification_summary.model_dump(),
            "mandatory_skills": [s.name for s in skill_classification.mandatory[:12]],
            "preferred_skills": [s.name for s in skill_classification.preferred[:10]],
            "education": req_data.education.model_dump(),
            "experience": {
                "minimum_years": req_data.experience.minimum_years,
                "maximum_years": req_data.experience.maximum_years,
                "fresher_eligible": req_data.experience.fresher_eligible,
            },
        }

        ai_output: JobReportAIStructuredOutput = await self.ai_insights_generator.generate_insights(
            job_title=record.job_title,
            company_name=record.company_name,
            context_summary=context_summary,
        )

        report_payload: Dict[str, Any] = {
            "overview": overview.model_dump(),
            "role_analysis": role_analysis.model_dump(),
            "technical_requirements": technical_requirements.model_dump(),
            "skill_classification": skill_classification.model_dump(),
            "education": req_data.education.model_dump(),
            "experience": req_data.experience.model_dump(),
            "soft_skills": [s.model_dump() for s in req_data.soft_skills],
            "responsibilities": role_data.responsibilities,
            "complexity_analysis": ai_output.complexity_analysis.model_dump(),
            "eligibility_criteria": eligibility_criteria.model_dump(),
            "ai_insights": [i.model_dump() for i in ai_output.ai_insights],
        }

        metadata: Dict[str, Any] = {
            "model_used": self.ai_insights_generator.model,
            "prerequisite_ids": {
                "role_analysis_id": role_data.id,
                "requirement_analysis_id": req_data.id,
                "skill_classification_id": skill_data.id,
            },
        }

        if existing:
            next_version_num = (existing.version_number or 1) + 1
            existing.version_number = next_version_num
            existing.report_version = f"{next_version_num}.0"
            existing.report_payload = report_payload
            existing.content_hash = combined_hash
            existing.analysis_metadata = metadata
            existing.generated_at = datetime.now(timezone.utc)
            target = existing
        else:
            target = JobDescriptionReport(
                job_description_id=record.id,
                user_id=record.user_id,
                version_number=1,
                report_version="1.0",
                report_payload=report_payload,
                content_hash=combined_hash,
                analysis_metadata=metadata,
            )
            db.add(target)

        db.commit()
        db.refresh(target)
        return _to_data(target, record, cached=False)


job_description_report_service = JobDescriptionReportService()
