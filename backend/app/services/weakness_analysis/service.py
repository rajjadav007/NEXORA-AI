"""
Resume Weakness Analysis Service
Phase 4 | Feature 23: Resume Weakness Analysis
Orchestrates resume data gathering, LangChain ChatOllama weakness evaluation,
ranking by severity, category synthesis, and PostgreSQL persistence.
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
from app.models.weakness_analysis import ResumeWeaknessAnalysis
from app.schemas.weakness_analysis import (
    WeaknessAnalysisData,
    WeaknessItem,
    MissingInformationItem,
    CategoryWeaknessSummary,
    PriorityBreakdown,
    ResumeWeaknessAIStructuredOutput,
    WEAKNESS_CATEGORIES,
)
from app.services.preview_service import preview_service
from app.services.weakness_analysis.ai_evaluator import (
    WeaknessAIEvaluator,
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)

PRIORITY_WEIGHTS = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


class WeaknessAnalysisService:
    """Service for identifying, ranking, and managing candidate resume weaknesses and missing information."""

    def __init__(self, ai_evaluator: Optional[WeaknessAIEvaluator] = None):
        self.ai_evaluator = ai_evaluator or WeaknessAIEvaluator()

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
        """Formats structured resume sections for the AI evaluator."""
        lines = []

        if personal_info:
            name = getattr(personal_info, "full_name", None) or getattr(personal_info, "name", "Candidate")
            headline = getattr(personal_info, "headline", "") or ""
            summary = getattr(personal_info, "summary", "") or ""
            email = getattr(personal_info, "email", "") or ""
            phone = getattr(personal_info, "phone", "") or ""
            loc = getattr(personal_info, "location", "") or ""
            contact_parts = [p for p in [email, phone, loc] if p]
            contact_str = f" ({', '.join(contact_parts)})" if contact_parts else ""
            lines.append(f"Candidate: {name}{contact_str} | {headline}")
            if summary:
                lines.append(f"Professional Summary: {summary}")
            else:
                lines.append("Professional Summary: [NONE PROVIDED]")

        if resume_skills:
            skill_list = [getattr(s, "canonical_name", None) or getattr(s, "original_name", str(s)) for s in resume_skills[:40]]
            lines.append(f"Technical & Soft Skills ({len(resume_skills)}): {', '.join(skill_list)}")
        else:
            lines.append("Technical & Soft Skills: [NONE LISTED]")

        if experience_records:
            lines.append(f"Experience ({len(experience_records)} roles):")
            for exp in experience_records[:6]:
                title = getattr(exp, "job_title", None) or getattr(exp, "title", "Position")
                comp = getattr(exp, "company_name", None) or getattr(exp, "company", "Company")
                start = getattr(exp, "start_date", "") or ""
                end = getattr(exp, "end_date", "") or "Present"
                desc = getattr(exp, "description", "") or ""
                bullets = getattr(exp, "key_responsibilities", []) or []
                bullet_str = " | ".join(bullets[:3]) if isinstance(bullets, list) else str(bullets)
                lines.append(f"- {title} at {comp} ({start} - {end}): {desc[:150]} {bullet_str[:250]}")
        else:
            lines.append("Experience: [NO WORK OR INTERNSHIP ROLES LISTED]")

        if projects:
            lines.append(f"Projects ({len(projects)}):")
            for p in projects[:5]:
                p_title = getattr(p, "project_title", None) or getattr(p, "title", "Project")
                p_desc = getattr(p, "description", "") or ""
                tech = getattr(p, "skills_used", []) or getattr(p, "technologies", []) or []
                tech_str = f" [Tech: {', '.join(tech[:5])}]" if tech else " [Tech: unspecified]"
                live = getattr(p, "live_url", None)
                repo = getattr(p, "github_url", None)
                links = [l for l in [live, repo] if l]
                links_str = f" [Links: {', '.join(links)}]" if links else " [No demo/repo link]"
                lines.append(f"- {p_title}{tech_str}{links_str}: {p_desc[:200]}")
        else:
            lines.append("Projects: [NO PROJECTS LISTED]")

        if education_records:
            lines.append(f"Education ({len(education_records)}):")
            for edu in education_records[:3]:
                deg = getattr(edu, "degree_name", None) or getattr(edu, "degree", "Degree")
                inst = getattr(edu, "institution_name", None) or getattr(edu, "institution", "Institution")
                grad = getattr(edu, "end_date", None) or getattr(edu, "graduation_year", "")
                gpa = getattr(edu, "grade", "") or getattr(edu, "gpa", "")
                gpa_str = f" (GPA/Grade: {gpa})" if gpa else ""
                lines.append(f"- {deg} - {inst} {grad}{gpa_str}")
        else:
            lines.append("Education: [NO EDUCATION RECORDS LISTED]")

        if certifications or achievements:
            val_items = []
            for c in (certifications or [])[:4]:
                c_name = getattr(c, "certification_name", "Certification")
                val_items.append(f"Cert: {c_name}")
            for a in (achievements or [])[:4]:
                a_name = getattr(a, "achievement_name", None) or getattr(a, "title", "Achievement")
                val_items.append(f"Honor: {a_name}")
            lines.append(f"Achievements & Credentials: {'; '.join(val_items)}")
        else:
            lines.append("Achievements & Credentials: [NONE LISTED]")

        return "\n".join(lines) if lines else "No structured resume information available."

    def _to_weakness_analysis_data(self, record: ResumeWeaknessAnalysis) -> WeaknessAnalysisData:
        """Transforms SQLAlchemy database record into validated Pydantic schema."""
        raw_weaknesses = record.weaknesses or []
        weaknesses_list = [WeaknessItem(**w) for w in raw_weaknesses]

        raw_missing = record.missing_information or []
        missing_list = [MissingInformationItem(**m) for m in raw_missing]

        category_summaries_dict = {
            k: CategoryWeaknessSummary(**v) for k, v in (record.category_summaries or {}).items()
        }

        crit = sum(1 for w in weaknesses_list if w.priority == "Critical")
        high = sum(1 for w in weaknesses_list if w.priority == "High")
        med = sum(1 for w in weaknesses_list if w.priority == "Medium")
        low = sum(1 for w in weaknesses_list if w.priority == "Low")

        return WeaknessAnalysisData(
            id=str(record.id),
            resume_id=str(record.resume_id),
            total_weaknesses_count=len(weaknesses_list),
            priority_breakdown=PriorityBreakdown(
                critical=crit,
                high=high,
                medium=med,
                low=low,
            ),
            overall_summary=record.overall_summary or "",
            weaknesses=weaknesses_list,
            missing_information=missing_list,
            category_summaries=category_summaries_dict,
            analysis_metadata=record.analysis_metadata or {},
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else "",
        )

    def get_weakness_analysis(self, resume_id: str, db: Session) -> Optional[WeaknessAnalysisData]:
        """Retrieves cached weakness analysis for a given resume."""
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        query = select(ResumeWeaknessAnalysis).where(ResumeWeaknessAnalysis.resume_id == parsed_id)
        record = db.execute(query).scalar_one_or_none()
        if not record:
            return None

        return self._to_weakness_analysis_data(record)

    async def calculate_weakness_analysis(
        self,
        resume_id: str,
        force_recalculate: bool = False,
        db: Session = None,
    ) -> WeaknessAnalysisData:
        """
        Extracts, ranks, and saves candidate weaknesses and missing information from resume data.
        Ranks weaknesses by severity, categorizes across 7 domains, and stores in PostgreSQL.
        """
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        # 1. Check cache
        if not force_recalculate:
            existing = self.get_weakness_analysis(resume_id, db)
            if existing:
                logger.info("Returning cached weakness analysis for resume %s", resume_id)
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

        # 4. Format structured resume sections
        resume_summary = self._build_resume_summary(
            personal_info=personal_info,
            education_records=education_records,
            experience_records=experience_records,
            resume_skills=resume_skills,
            projects=projects,
            certifications=certifications,
            achievements=achievements,
        )

        # 5. Run LLM weakness evaluation
        start_time = time.time()
        ai_output: ResumeWeaknessAIStructuredOutput = await self.ai_evaluator.evaluate_weaknesses(
            resume_summary=resume_summary,
            cleaned_text=cleaned_text,
        )
        duration = round(time.time() - start_time, 2)

        # 6. Rank weaknesses by priority importance
        # Critical -> High -> Medium -> Low
        sorted_ai_weaknesses = sorted(
            ai_output.weaknesses,
            key=lambda w: PRIORITY_WEIGHTS.get(w.priority.capitalize(), 2),
            reverse=True,
        )

        ranked_weaknesses: List[Dict[str, Any]] = []
        for idx, w in enumerate(sorted_ai_weaknesses, start=1):
            category_key = w.category if w.category in WEAKNESS_CATEGORIES else "clarity_relevance"
            ranked_weaknesses.append({
                "title": w.title,
                "category": category_key,
                "category_name": WEAKNESS_CATEGORIES.get(category_key, "General Content"),
                "explanation": w.explanation,
                "evidence": w.evidence or [],
                "why_it_matters": w.why_it_matters,
                "suggested_improvement": w.suggested_improvement,
                "priority": w.priority.capitalize() if w.priority.capitalize() in PRIORITY_WEIGHTS else "Medium",
                "relevance_rank": idx,
                "weakness_type": w.weakness_type or "vague_description",
            })

        # 7. Format separate missing information items
        formatted_missing_info: List[Dict[str, Any]] = []
        for m in (ai_output.missing_information or []):
            formatted_missing_info.append({
                "section": m.section,
                "item": m.item,
                "relevance": m.relevance,
                "impact_level": m.impact_level.capitalize() if m.impact_level.capitalize() in PRIORITY_WEIGHTS else "Medium",
                "is_optional": bool(m.is_optional),
            })

        # 8. Build category summaries
        category_summaries: Dict[str, Dict[str, Any]] = {}
        for cat_key, cat_name in WEAKNESS_CATEGORIES.items():
            cat_weaknesses = [w for w in ranked_weaknesses if w["category"] == cat_key]
            rec = (ai_output.category_recommendations or {}).get(
                cat_key,
                f"Review and strengthen your {cat_name.lower()} with specific details and metrics."
            )
            category_summaries[cat_key] = {
                "category_key": cat_key,
                "category_name": cat_name,
                "total_weaknesses": len(cat_weaknesses),
                "critical_count": sum(1 for w in cat_weaknesses if w["priority"] == "Critical"),
                "high_count": sum(1 for w in cat_weaknesses if w["priority"] == "High"),
                "medium_count": sum(1 for w in cat_weaknesses if w["priority"] == "Medium"),
                "low_count": sum(1 for w in cat_weaknesses if w["priority"] == "Low"),
                "key_recommendation": rec,
            }

        metadata = {
            "model": self.ai_evaluator.model,
            "duration_seconds": duration,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "total_weaknesses": len(ranked_weaknesses),
            "total_missing_items": len(formatted_missing_info),
        }

        # 9. Upsert into database
        existing_record = db.execute(
            select(ResumeWeaknessAnalysis).where(ResumeWeaknessAnalysis.resume_id == parsed_id)
        ).scalar_one_or_none()

        if existing_record:
            existing_record.weaknesses = ranked_weaknesses
            existing_record.missing_information = formatted_missing_info
            existing_record.category_summaries = category_summaries
            existing_record.overall_summary = ai_output.overall_summary
            existing_record.analysis_metadata = metadata
            db.commit()
            db.refresh(existing_record)
            saved_record = existing_record
        else:
            new_record = ResumeWeaknessAnalysis(
                resume_id=parsed_id,
                user_id=resume.user_id,
                weaknesses=ranked_weaknesses,
                missing_information=formatted_missing_info,
                category_summaries=category_summaries,
                overall_summary=ai_output.overall_summary,
                analysis_metadata=metadata,
            )
            db.add(new_record)
            db.commit()
            db.refresh(new_record)
            saved_record = new_record

        return self._to_weakness_analysis_data(saved_record)


weakness_analysis_service = WeaknessAnalysisService()
