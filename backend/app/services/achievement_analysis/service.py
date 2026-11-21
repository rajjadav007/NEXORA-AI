"""
Resume Achievement Analysis Service
Phase 4 | Feature 26: Achievement Analysis
Orchestrates structured resume data gathering, LangChain ChatOllama achievement
extraction, metric detection, Google X-Y-Z rewrites, rubric scoring, and PostgreSQL persistence.
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
from app.models.achievement_analysis import ResumeAchievementAnalysis
from app.schemas.achievement_analysis import (
    AchievementAnalysisData,
    AchievementItem,
    MeasurableMetrics,
    CategoryAchievementSummary,
    RubricBreakdown,
    ResumeAchievementAIStructuredOutput,
    ACHIEVEMENT_CATEGORIES,
)
from app.services.preview_service import preview_service
from app.services.achievement_analysis.rubric import calculate_achievement_rubric
from app.services.achievement_analysis.ai_evaluator import (
    achievement_ai_evaluator,
    AchievementAIEvaluator,
)

logger = logging.getLogger(__name__)


class AchievementAnalysisService:
    """Service managing candidate achievement extraction, metric analysis, and impact scoring."""

    def __init__(self, ai_evaluator: Optional[AchievementAIEvaluator] = None):
        self.ai_evaluator = ai_evaluator or achievement_ai_evaluator

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
        """Formats all structured sections for achievement analysis."""
        lines = []

        if personal_info:
            name = getattr(personal_info, "full_name", None) or getattr(personal_info, "name", "Candidate")
            headline = getattr(personal_info, "headline", "") or ""
            summary = getattr(personal_info, "summary", "") or ""
            lines.append(f"Candidate: {name} | {headline}")
            if summary:
                lines.append(f"Summary Statement: {summary}")

        if experience_records:
            lines.append(f"Work Experience ({len(experience_records)} roles):")
            for exp in experience_records[:6]:
                title = getattr(exp, "job_title", None) or getattr(exp, "title", "Role")
                comp = getattr(exp, "company_name", None) or getattr(exp, "company", "Company")
                start = getattr(exp, "start_date", "") or ""
                end = getattr(exp, "end_date", "") or "Present"
                desc = getattr(exp, "description", "") or ""
                bullets = getattr(exp, "key_responsibilities", []) or []
                bullet_str = " | ".join(bullets[:4]) if isinstance(bullets, list) else str(bullets)
                lines.append(f"- {title} at {comp} ({start} - {end}): {desc[:150]} Bullets: {bullet_str[:300]}")

        if projects:
            lines.append(f"Projects ({len(projects)}):")
            for p in projects[:6]:
                p_title = getattr(p, "project_title", None) or getattr(p, "title", "Project")
                p_desc = getattr(p, "description", "") or ""
                tech = getattr(p, "skills_used", []) or getattr(p, "technologies", []) or []
                tech_str = f" [Tech: {', '.join(tech[:5])}]" if tech else ""
                lines.append(f"- {p_title}{tech_str}: {p_desc[:250]}")

        if achievements:
            lines.append(f"Recorded Awards & Honors ({len(achievements)}):")
            for a in achievements[:6]:
                a_name = getattr(a, "achievement_name", None) or getattr(a, "title", "Award")
                a_desc = getattr(a, "description", "") or ""
                lines.append(f"- Award: {a_name} - {a_desc[:150]}")

        if certifications:
            lines.append(f"Certifications ({len(certifications)}):")
            for c in certifications[:5]:
                c_name = getattr(c, "certification_name", "Certification")
                c_issuer = getattr(c, "issuing_organization", "")
                lines.append(f"- Cert: {c_name} ({c_issuer})")

        if education_records:
            lines.append(f"Education ({len(education_records)}):")
            for edu in education_records[:3]:
                deg = getattr(edu, "degree_name", None) or getattr(edu, "degree", "Degree")
                inst = getattr(edu, "institution_name", None) or getattr(edu, "institution", "Institution")
                gpa = getattr(edu, "grade", "") or getattr(edu, "gpa", "")
                gpa_str = f" [GPA: {gpa}]" if gpa else ""
                lines.append(f"- {deg} from {inst}{gpa_str}")

        return "\n".join(lines) if lines else "No structured resume information available."

    def _to_achievement_analysis_data(self, record: ResumeAchievementAnalysis) -> AchievementAnalysisData:
        """Transforms SQLAlchemy database record into validated Pydantic schema."""
        raw_achieves = record.achievements or []
        achievements_list: List[AchievementItem] = []
        for a in raw_achieves:
            m = a.get("measurable_metrics", {})
            metrics = MeasurableMetrics(
                percentages=m.get("percentages", []),
                numbers=m.get("numbers", []),
                time_saved=m.get("time_saved", []),
                users_impacted=m.get("users_impacted", []),
                performance_gain=m.get("performance_gain", []),
            )
            item_data = dict(a)
            item_data["measurable_metrics"] = metrics
            achievements_list.append(AchievementItem(**item_data))

        raw_cat = record.category_breakdown or {}
        cat_dict = {k: CategoryAchievementSummary(**v) for k, v in raw_cat.items()}

        raw_rubric = record.rubric_breakdown or {}
        rubric = RubricBreakdown(
            quantification_rate_score=raw_rubric.get("quantification_rate_score", 0.0),
            impact_magnitude_score=raw_rubric.get("impact_magnitude_score", 0.0),
            cross_category_diversity_score=raw_rubric.get("cross_category_diversity_score", 0.0),
            action_clarity_score=raw_rubric.get("action_clarity_score", 0.0),
            metric_verification_fidelity_score=raw_rubric.get("metric_verification_fidelity_score", 0.0),
            total_score=raw_rubric.get("total_score", record.achievement_score),
        )

        return AchievementAnalysisData(
            id=str(record.id),
            resume_id=str(record.resume_id),
            achievement_score=record.achievement_score,
            score_grade=record.score_grade,
            executive_summary=record.executive_summary or "",
            total_achievements_count=record.total_achievements_count,
            quantified_count=record.quantified_count,
            unquantified_count=record.unquantified_count,
            quantification_rate=record.quantification_rate,
            achievements=achievements_list,
            category_breakdown=cat_dict,
            rubric_breakdown=rubric,
            analysis_metadata=record.analysis_metadata or {},
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else "",
        )

    def get_achievement_analysis(self, resume_id: str, db: Session) -> Optional[AchievementAnalysisData]:
        """Retrieves cached achievement analysis for a given resume."""
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        query = select(ResumeAchievementAnalysis).where(ResumeAchievementAnalysis.resume_id == parsed_id)
        record = db.execute(query).scalar_one_or_none()
        if not record:
            return None

        return self._to_achievement_analysis_data(record)

    async def calculate_achievement_analysis(
        self,
        resume_id: str,
        force_recalculate: bool = False,
        db: Session = None,
    ) -> AchievementAnalysisData:
        """
        Executes AI achievement extraction across all sections, classifies quantifiable metrics,
        computes transparent rubric scores, generates Google X-Y-Z rewrites, and persists to PostgreSQL.
        """
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        # 1. Check cache
        if not force_recalculate:
            existing = self.get_achievement_analysis(resume_id, db)
            if existing:
                logger.info("Returning cached achievement analysis for resume %s", resume_id)
                return existing

        # 2. Retrieve resume record
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

        # 3. Resolve cleaned text
        cleaned_text = self._resolve_cleaned_text(resume, resume_id, db)

        # 4. Format structured summary
        resume_summary = self._build_resume_summary(
            personal_info=personal_info,
            education_records=education_records,
            experience_records=experience_records,
            resume_skills=resume_skills,
            projects=projects,
            certifications=certifications,
            achievements=achievements,
        )

        # 5. Run AI achievement evaluation
        start_time = time.time()
        ai_output: ResumeAchievementAIStructuredOutput = await self.ai_evaluator.evaluate_achievements(
            resume_summary=resume_summary,
            cleaned_text=cleaned_text,
        )
        duration = round(time.time() - start_time, 2)

        # 6. Format achievements and extract category keys
        formatted_achievements: List[Dict[str, Any]] = []
        active_category_keys: List[str] = []

        quantified_cnt = 0
        unquantified_cnt = 0

        for idx, item in enumerate(ai_output.achievements, start=1):
            cat = item.category if item.category in ACHIEVEMENT_CATEGORIES else "experience"
            active_category_keys.append(cat)

            is_quant = bool(item.is_quantified)
            if is_quant:
                quantified_cnt += 1
            else:
                unquantified_cnt += 1

            formatted_achievements.append({
                "id": f"achieve_{idx}",
                "title": item.title,
                "category": cat,
                "category_name": ACHIEVEMENT_CATEGORIES.get(cat, "Experience"),
                "original_statement": item.original_statement,
                "is_quantified": is_quant,
                "measurable_metrics": {
                    "percentages": item.percentages or [],
                    "numbers": item.numbers or [],
                    "time_saved": item.time_saved or [],
                    "users_impacted": item.users_impacted or [],
                    "performance_gain": item.performance_gain or [],
                },
                "has_verified_metrics": bool(item.has_verified_metrics),
                "missing_metrics_note": item.missing_metrics_note,
                "evidence": item.evidence or [],
                "impact_level": item.impact_level.capitalize() if item.impact_level.capitalize() in ["High", "Medium", "Low"] else "Medium",
                "professional_relevance": item.professional_relevance.capitalize() if item.professional_relevance.capitalize() in ["High", "Medium", "Low"] else "High",
                "quality_rating": item.quality_rating.capitalize() if item.quality_rating.capitalize() in ["Strong", "Moderate", "Weak"] else "Moderate",
                "suggested_statement": item.suggested_statement,
                "explanation": item.explanation,
            })

        total_cnt = len(formatted_achievements)
        quant_rate = round((quantified_cnt / total_cnt * 100.0), 1) if total_cnt > 0 else 0.0

        # 7. Compute rubric score
        achievement_score, score_grade, rubric = calculate_achievement_rubric(
            achievements=[AchievementItem(**a) for a in formatted_achievements],
            category_keys=active_category_keys,
        )

        # 8. Compute category breakdown
        category_breakdown: Dict[str, Dict[str, Any]] = {}
        for cat_key, cat_name in ACHIEVEMENT_CATEGORIES.items():
            cat_items = [a for a in formatted_achievements if a["category"] == cat_key]
            q_count = sum(1 for a in cat_items if a["is_quantified"])
            uq_count = len(cat_items) - q_count
            highlight = (ai_output.category_highlights or {}).get(
                cat_key,
                f"{len(cat_items)} accomplishment(s) identified in {cat_name.lower()}."
            )
            category_breakdown[cat_key] = {
                "category_key": cat_key,
                "category_name": cat_name,
                "total_count": len(cat_items),
                "quantified_count": q_count,
                "unquantified_count": uq_count,
                "top_highlight": highlight,
            }

        metadata = {
            "model": self.ai_evaluator.model,
            "duration_seconds": duration,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "total_achievements": total_cnt,
            "quantified_count": quantified_cnt,
        }

        # 9. Upsert into database
        existing_record = db.execute(
            select(ResumeAchievementAnalysis).where(ResumeAchievementAnalysis.resume_id == parsed_id)
        ).scalar_one_or_none()

        if existing_record:
            existing_record.achievement_score = achievement_score
            existing_record.score_grade = score_grade
            existing_record.executive_summary = ai_output.executive_summary
            existing_record.total_achievements_count = total_cnt
            existing_record.quantified_count = quantified_cnt
            existing_record.unquantified_count = unquantified_cnt
            existing_record.quantification_rate = quant_rate
            existing_record.achievements = formatted_achievements
            existing_record.category_breakdown = category_breakdown
            existing_record.rubric_breakdown = rubric.model_dump()
            existing_record.analysis_metadata = metadata
            db.commit()
            db.refresh(existing_record)
            saved_record = existing_record
        else:
            new_record = ResumeAchievementAnalysis(
                resume_id=parsed_id,
                user_id=resume.user_id,
                achievement_score=achievement_score,
                score_grade=score_grade,
                executive_summary=ai_output.executive_summary,
                total_achievements_count=total_cnt,
                quantified_count=quantified_cnt,
                unquantified_count=unquantified_cnt,
                quantification_rate=quant_rate,
                achievements=formatted_achievements,
                category_breakdown=category_breakdown,
                rubric_breakdown=rubric.model_dump(),
                analysis_metadata=metadata,
            )
            db.add(new_record)
            db.commit()
            db.refresh(new_record)
            saved_record = new_record

        return self._to_achievement_analysis_data(saved_record)


achievement_analysis_service = AchievementAnalysisService()
