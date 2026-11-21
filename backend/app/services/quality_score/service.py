"""
Resume Quality Score Orchestration Service
Phase 4 | Feature 21: Resume Quality Score Engine
Coordinates Phase 3 data retrieval, deterministic scoring, LangChain ChatOllama evaluation,
rubric synthesis, and persistent database storage.
"""

import uuid
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.security import verify_resume_access, validate_resume_id
from app.models.resume import Resume
from app.models.quality_score import ResumeQualityScore
from app.schemas.quality_score import (
    QualityScoreData,
    CategoryScoreDetail,
    ResumeQualityAIStructuredOutput,
)
from app.services.preview_service import preview_service
from app.services.quality_score.rubric import (
    RUBRIC_CATEGORIES,
    get_rating_level,
)
from app.services.quality_score.deterministic_scorer import evaluate_deterministic_baseline
from app.services.quality_score.ai_evaluator import (
    QualityScoreAIEvaluator,
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)


class QualityScoreService:
    """Manages analysis, calculation, persistence, and retrieval of resume quality scores."""

    def __init__(self, ai_evaluator: Optional[QualityScoreAIEvaluator] = None):
        self.ai_evaluator = ai_evaluator or QualityScoreAIEvaluator()

    def _resolve_cleaned_text(self, resume: Resume, resume_id: str, db: Session) -> str:
        """Retrieves cleaned resume text from database version or preview service."""
        if resume and resume.versions and len(resume.versions) > 0:
            latest = resume.versions[0]
            if latest.cleaned_text:
                return latest.cleaned_text

        try:
            preview_data = preview_service.get_preview(resume_id, db=db)
            if preview_data and preview_data.cleaned_text:
                return preview_data.cleaned_text
        except Exception:
            pass

        return ""

    def _build_resume_summary(
        self,
        personal_info: Optional[Any],
        education_records: List[Any],
        experience_records: List[Any],
        resume_skills: List[Any],
        projects: List[Any],
        certifications: List[Any],
        achievements: List[Any],
    ) -> str:
        """Constructs a clean summary of structured resume data for AI evaluation."""
        lines = []

        # Personal Info
        if personal_info:
            name = getattr(personal_info, "full_name", None) or getattr(personal_info, "name", "Not specified")
            email = getattr(personal_info, "email", "Not specified")
            phone = getattr(personal_info, "phone", "Not specified")
            summary = getattr(personal_info, "summary", "None provided")
            lines.append(f"- Name: {name}")
            lines.append(f"- Contact: Email: {email}, Phone: {phone}")
            lines.append(f"- Professional Summary: {summary}")
        else:
            lines.append("- Personal Information: None recorded")

        # Skills
        if resume_skills:
            skill_names = [getattr(s, "canonical_name", None) or getattr(s, "original_name", str(s)) for s in resume_skills[:30]]
            lines.append(f"- Skills ({len(resume_skills)} total): {', '.join(skill_names)}")
        else:
            lines.append("- Skills: No skills extracted")

        # Experience
        if experience_records:
            lines.append(f"- Work Experience ({len(experience_records)} positions):")
            for exp in experience_records[:5]:
                title = getattr(exp, "job_title", None) or getattr(exp, "title", "Position")
                company = getattr(exp, "company_name", None) or getattr(exp, "company", "Company")
                start = getattr(exp, "start_date", "") or ""
                end = getattr(exp, "end_date", "") or "Present"
                desc = getattr(exp, "description", "") or ""
                lines.append(f"  * {title} at {company} ({start} - {end}): {desc[:200]}")
        else:
            lines.append("- Work Experience: None recorded")

        # Education
        if education_records:
            lines.append(f"- Education ({len(education_records)} entries):")
            for edu in education_records[:3]:
                deg = getattr(edu, "degree_name", None) or getattr(edu, "degree", "Degree")
                inst = getattr(edu, "institution_name", None) or getattr(edu, "institution", "Institution")
                grad = getattr(edu, "end_date", None) or getattr(edu, "graduation_year", "")
                lines.append(f"  * {deg} from {inst} ({grad})")
        else:
            lines.append("- Education: None recorded")

        # Projects
        if projects:
            lines.append(f"- Projects ({len(projects)} projects):")
            for p in projects[:4]:
                p_title = getattr(p, "project_title", None) or getattr(p, "title", "Project")
                p_desc = getattr(p, "description", "") or ""
                lines.append(f"  * {p_title}: {p_desc[:150]}")
        else:
            lines.append("- Projects: None recorded")

        # Certifications & Achievements
        validations = []
        if certifications:
            for c in certifications[:3]:
                c_name = getattr(c, "certification_name", "Certification")
                validations.append(f"Cert: {c_name}")
        if achievements:
            for a in achievements[:3]:
                a_name = getattr(a, "achievement_name", None) or getattr(a, "title", "Achievement")
                validations.append(f"Award: {a_name}")
        if validations:
            lines.append(f"- Certifications & Achievements: {', '.join(validations)}")
        else:
            lines.append("- Certifications & Achievements: None recorded")

        return "\n".join(lines)

    def _to_quality_score_data(self, record: ResumeQualityScore) -> QualityScoreData:
        """Converts database model into validated Pydantic schema."""
        category_scores_mapped: Dict[str, CategoryScoreDetail] = {}
        for k, v in (record.category_scores or {}).items():
            if isinstance(v, dict):
                category_scores_mapped[k] = CategoryScoreDetail(**v)

        return QualityScoreData(
            id=str(record.id),
            resume_id=str(record.resume_id),
            overall_score=round(record.overall_score, 1),
            rating_level=record.rating_level,
            category_scores=category_scores_mapped,
            category_explanations=record.category_explanations or {},
            strengths=record.strengths or [],
            missing_information=record.missing_information or [],
            improvement_suggestions=record.improvement_suggestions or [],
            rubric_version=record.rubric_version or "1.0.0",
            analysis_metadata=record.analysis_metadata or {},
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else "",
        )

    def get_quality_score(self, resume_id: str, db: Session) -> Optional[QualityScoreData]:
        """Retrieves previously generated quality score from database."""
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        query = select(ResumeQualityScore).where(ResumeQualityScore.resume_id == parsed_id)
        record = db.execute(query).scalar_one_or_none()
        if not record:
            return None

        return self._to_quality_score_data(record)

    async def calculate_quality_score(
        self,
        resume_id: str,
        force_recalculate: bool = False,
        db: Session = None,
    ) -> QualityScoreData:
        """
        Calculates or retrieves the Resume Quality Score.
        Evaluates 8 structured categories, computes overall score,
        validates with Pydantic, and stores in database.
        """
        # 1. Verify access and existence
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        # 2. Check for existing score unless force_recalculate is requested
        if not force_recalculate:
            existing = self.get_quality_score(resume_id, db)
            if existing:
                logger.info("Returning cached quality score for resume %s", resume_id)
                return existing

        # 3. Load full resume record with Phase 3 structured relations
        resume = db.execute(select(Resume).where(Resume.id == parsed_id)).scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found for ID: {resume_id}",
            )

        personal_info = resume.personal_information
        education_records = resume.education_records or []
        experience_records = resume.experience_records or []
        resume_skills = resume.resume_skills or []
        projects = resume.projects or []
        certifications = resume.certifications or []
        achievements = resume.achievements or []
        cleaned_text = self._resolve_cleaned_text(resume, resume_id, db)

        # 4. Compute deterministic baseline metrics
        deterministic_results = evaluate_deterministic_baseline(
            personal_info=personal_info,
            education_records=education_records,
            experience_records=experience_records,
            resume_skills=resume_skills,
            projects=projects,
            certifications=certifications,
            achievements=achievements,
            cleaned_text=cleaned_text,
        )

        # 5. Build resume summary and invoke LangChain ChatOllama evaluator
        resume_summary = self._build_resume_summary(
            personal_info=personal_info,
            education_records=education_records,
            experience_records=experience_records,
            resume_skills=resume_skills,
            projects=projects,
            certifications=certifications,
            achievements=achievements,
        )

        start_time = time.time()
        ai_output: ResumeQualityAIStructuredOutput = await self.ai_evaluator.evaluate_resume(
            resume_summary=resume_summary,
            deterministic_findings=deterministic_results,
            cleaned_text=cleaned_text,
        )
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # 6. Synthesize category scores based on 100-point transparent rubric
        category_scores: Dict[str, Dict[str, Any]] = {}
        category_explanations: Dict[str, str] = {}
        total_calculated_score = 0.0

        for cat_key, rubric in RUBRIC_CATEGORIES.items():
            det_info = deterministic_results.get(cat_key, {})
            det_ratio = det_info.get("ratio", 0.5)

            ai_cat_eval = getattr(ai_output, cat_key, None)
            if ai_cat_eval:
                ai_ratio = float(ai_cat_eval.score_ratio)
                explanation = ai_cat_eval.explanation
                strengths = ai_cat_eval.strengths or []
                improvements = ai_cat_eval.improvements or []
            else:
                ai_ratio = det_ratio
                explanation = f"Evaluated based on structural analysis for {rubric.name}."
                strengths = []
                improvements = []

            # Blending: For structural categories 50/50, for narrative/impact 35/65
            if cat_key in ["completeness", "education", "achievements"]:
                blended_ratio = (0.5 * det_ratio) + (0.5 * ai_ratio)
            else:
                blended_ratio = (0.35 * det_ratio) + (0.65 * ai_ratio)

            # Clamp ratio between 0.0 and 1.0
            blended_ratio = max(0.0, min(1.0, blended_ratio))
            raw_score = round(blended_ratio * rubric.max_score, 1)
            score_percentage = round((raw_score / rubric.max_score) * 100.0, 1) if rubric.max_score > 0 else 0.0
            rating = get_rating_level(score_percentage)

            category_scores[cat_key] = {
                "category_name": rubric.name,
                "category_key": cat_key,
                "score": raw_score,
                "max_score": rubric.max_score,
                "weight_percentage": rubric.weight,
                "score_percentage": score_percentage,
                "rating": rating,
                "explanation": explanation,
                "strengths": strengths,
                "improvements": improvements,
            }
            category_explanations[cat_key] = explanation
            total_calculated_score += raw_score

        # Invariant check: overall score clamped to 0.0 - 100.0
        final_overall_score = round(max(0.0, min(100.0, total_calculated_score)), 1)
        final_rating = get_rating_level(final_overall_score)

        # Missing information extraction: combine deterministic and AI suggestions
        combined_missing = list(ai_output.missing_critical_information or [])
        det_missing = deterministic_results.get("completeness", {}).get("missing_sections", [])
        for dm in det_missing:
            msg = f"Missing core section: {dm}"
            if msg not in combined_missing:
                combined_missing.append(msg)

        # 7. Persist or update in database (prevent duplicates)
        existing_record = db.execute(
            select(ResumeQualityScore).where(ResumeQualityScore.resume_id == parsed_id)
        ).scalar_one_or_none()

        metadata_dict = {
            "model": self.ai_evaluator.model,
            "base_url": self.ai_evaluator.base_url,
            "duration_ms": duration_ms,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
        }

        if existing_record:
            existing_record.overall_score = final_overall_score
            existing_record.rating_level = final_rating
            existing_record.category_scores = category_scores
            existing_record.category_explanations = category_explanations
            existing_record.strengths = ai_output.top_strengths or []
            existing_record.missing_information = combined_missing
            existing_record.improvement_suggestions = ai_output.priority_improvements or []
            existing_record.analysis_metadata = metadata_dict
            existing_record.updated_at = datetime.now(timezone.utc)
            record = existing_record
        else:
            record = ResumeQualityScore(
                resume_id=parsed_id,
                user_id=resume.user_id,
                overall_score=final_overall_score,
                rating_level=final_rating,
                category_scores=category_scores,
                category_explanations=category_explanations,
                strengths=ai_output.top_strengths or [],
                missing_information=combined_missing,
                improvement_suggestions=ai_output.priority_improvements or [],
                rubric_version="1.0.0",
                analysis_metadata=metadata_dict,
            )
            db.add(record)

        db.commit()
        db.refresh(record)

        logger.info(
            "Successfully evaluated quality score for resume %s: %s/100 (%s)",
            resume_id,
            final_overall_score,
            final_rating,
        )
        return self._to_quality_score_data(record)


# Global singleton service
quality_score_service = QualityScoreService()
