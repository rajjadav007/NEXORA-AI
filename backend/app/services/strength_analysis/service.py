"""
Resume Strength Analysis Service
Phase 4 | Feature 22: Resume Strength Analysis
Orchestrates resume data gathering, LangChain ChatOllama strength extraction,
ranking, category synthesis, and PostgreSQL persistence.
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
from app.models.strength_analysis import ResumeStrengthAnalysis
from app.schemas.strength_analysis import (
    StrengthAnalysisData,
    StrengthItem,
    CategoryStrengthSummary,
    ResumeStrengthAIStructuredOutput,
    STRENGTH_CATEGORIES,
)
from app.services.preview_service import preview_service
from app.services.strength_analysis.ai_evaluator import (
    StrengthAIEvaluator,
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)


class StrengthAnalysisService:
    """Service for identifying, ranking, and managing candidate resume strengths."""

    def __init__(self, ai_evaluator: Optional[StrengthAIEvaluator] = None):
        self.ai_evaluator = ai_evaluator or StrengthAIEvaluator()

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
            lines.append(f"Candidate: {name} | {headline}")
            if summary:
                lines.append(f"Summary: {summary}")

        if resume_skills:
            skill_list = [getattr(s, "canonical_name", None) or getattr(s, "original_name", str(s)) for s in resume_skills[:40]]
            lines.append(f"Technical & Soft Skills ({len(resume_skills)}): {', '.join(skill_list)}")

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

        if projects:
            lines.append(f"Projects ({len(projects)}):")
            for p in projects[:5]:
                p_title = getattr(p, "project_title", None) or getattr(p, "title", "Project")
                p_desc = getattr(p, "description", "") or ""
                tech = getattr(p, "skills_used", []) or getattr(p, "technologies", []) or []
                tech_str = f" [Tech: {', '.join(tech[:5])}]" if tech else ""
                lines.append(f"- {p_title}{tech_str}: {p_desc[:200]}")

        if education_records:
            lines.append(f"Education ({len(education_records)}):")
            for edu in education_records[:3]:
                deg = getattr(edu, "degree_name", None) or getattr(edu, "degree", "Degree")
                inst = getattr(edu, "institution_name", None) or getattr(edu, "institution", "Institution")
                grad = getattr(edu, "end_date", None) or getattr(edu, "graduation_year", "")
                gpa = getattr(edu, "grade", "") or getattr(edu, "gpa", "")
                gpa_str = f" (GPA/Grade: {gpa})" if gpa else ""
                lines.append(f"- {deg} - {inst} {grad}{gpa_str}")

        if certifications or achievements:
            val_items = []
            for c in (certifications or [])[:4]:
                c_name = getattr(c, "certification_name", "Certification")
                val_items.append(f"Cert: {c_name}")
            for a in (achievements or [])[:4]:
                a_name = getattr(a, "achievement_name", None) or getattr(a, "title", "Achievement")
                val_items.append(f"Honor: {a_name}")
            lines.append(f"Achievements & Credentials: {'; '.join(val_items)}")

        return "\n".join(lines) if lines else "No structured resume information available."

    def _to_strength_analysis_data(self, record: ResumeStrengthAnalysis) -> StrengthAnalysisData:
        """Transforms SQLAlchemy database record into validated Pydantic schema."""
        strengths_list = [StrengthItem(**s) for s in (record.strengths or [])]
        category_summaries_dict = {
            k: CategoryStrengthSummary(**v) for k, v in (record.category_summaries or {}).items()
        }

        demonstrated_cnt = sum(1 for s in strengths_list if s.strength_type == "demonstrated")
        potential_cnt = sum(1 for s in strengths_list if s.strength_type == "potential")

        return StrengthAnalysisData(
            id=str(record.id),
            resume_id=str(record.resume_id),
            total_strengths_count=len(strengths_list),
            demonstrated_count=demonstrated_cnt,
            potential_count=potential_cnt,
            is_sufficient_evidence=record.is_sufficient_evidence,
            insufficient_evidence_reason=record.insufficient_evidence_reason,
            top_strengths_summary=record.top_strengths_summary or "",
            strengths=strengths_list,
            category_summaries=category_summaries_dict,
            analysis_metadata=record.analysis_metadata or {},
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else "",
        )

    def get_strength_analysis(self, resume_id: str, db: Session) -> Optional[StrengthAnalysisData]:
        """Retrieves cached strength analysis for a given resume."""
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        query = select(ResumeStrengthAnalysis).where(ResumeStrengthAnalysis.resume_id == parsed_id)
        record = db.execute(query).scalar_one_or_none()
        if not record:
            return None

        return self._to_strength_analysis_data(record)

    async def calculate_strength_analysis(
        self,
        resume_id: str,
        force_recalculate: bool = False,
        db: Session = None,
    ) -> StrengthAnalysisData:
        """
        Extracts, ranks, and saves candidate strengths from resume data.
        Distinguishes demonstrated vs potential strengths and enforces evidence grounding.
        """
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        # 1. Check cache
        if not force_recalculate:
            existing = self.get_strength_analysis(resume_id, db)
            if existing:
                logger.info("Returning cached strength analysis for resume %s", resume_id)
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
        cleaned_text = self._resolve_cleaned_text(resume, resume_id, db)

        # Check for empty/insufficient content
        total_data_points = (
            len(education_records)
            + len(experience_records)
            + len(resume_skills)
            + len(projects)
            + len(certifications)
            + len(achievements)
        )
        word_count = len(cleaned_text.split()) if cleaned_text else 0

        # Build summary for LLM
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
        ai_output: ResumeStrengthAIStructuredOutput = await self.ai_evaluator.evaluate_strengths(
            resume_summary=resume_summary,
            cleaned_text=cleaned_text,
        )
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # 3. Check sufficiency: flag if resume is truly too sparse
        is_sufficient = ai_output.is_sufficient_evidence
        insufficient_reason = ai_output.insufficient_evidence_reason
        if len(ai_output.strengths) == 0 or not ai_output.is_sufficient_evidence:
            if total_data_points == 0 and word_count < 30:
                is_sufficient = False
                insufficient_reason = (
                    insufficient_reason
                    or "Resume contains insufficient extracted data points to detect verified strengths."
                )

        # 4. Process and Rank Strengths
        # Rank sorting: demonstrated > potential; High > Medium > Low confidence
        def _rank_key(item):
            type_weight = 0 if item.strength_type.lower() == "demonstrated" else 1
            conf_map = {"high": 0, "medium": 1, "low": 2}
            conf_weight = conf_map.get(item.confidence_level.lower(), 1)
            return (type_weight, conf_weight)

        sorted_ai_strengths = sorted(ai_output.strengths, key=_rank_key)

        processed_strengths: List[Dict[str, Any]] = []
        for idx, s in enumerate(sorted_ai_strengths, start=1):
            cat_key = s.category.strip().lower()
            if cat_key not in STRENGTH_CATEGORIES:
                cat_key = "technical_skills"

            cat_display_name = STRENGTH_CATEGORIES.get(cat_key, "Technical Skills")

            processed_strengths.append({
                "title": s.title.strip(),
                "category": cat_key,
                "category_name": cat_display_name,
                "explanation": s.explanation.strip(),
                "evidence": [e.strip() for e in s.evidence if e.strip()],
                "professional_value": s.professional_value.strip(),
                "confidence_level": s.confidence_level.strip().capitalize(),
                "strength_type": s.strength_type.strip().lower(),
                "relevance_rank": idx,
            })

        # 5. Synthesize Category Summaries
        category_summaries: Dict[str, Dict[str, Any]] = {}
        for cat_key, cat_name in STRENGTH_CATEGORIES.items():
            cat_items = [st for st in processed_strengths if st["category"] == cat_key]
            demo_cnt = sum(1 for st in cat_items if st["strength_type"] == "demonstrated")
            pot_cnt = sum(1 for st in cat_items if st["strength_type"] == "potential")

            takeaway = (ai_output.category_takeaways or {}).get(cat_key)
            if not takeaway:
                if len(cat_items) > 0:
                    takeaway = f"Demonstrates {len(cat_items)} identified strength(s) with focus on core domain competencies."
                else:
                    takeaway = f"Limited specific evidence identified for {cat_name} in current resume."

            category_summaries[cat_key] = {
                "category_key": cat_key,
                "category_name": cat_name,
                "total_strengths": len(cat_items),
                "demonstrated_count": demo_cnt,
                "potential_count": pot_cnt,
                "key_takeaway": takeaway,
            }

        # 6. Database Persistence (idempotent / avoid duplicates)
        existing_record = db.execute(
            select(ResumeStrengthAnalysis).where(ResumeStrengthAnalysis.resume_id == parsed_id)
        ).scalar_one_or_none()

        metadata_dict = {
            "model": getattr(self.ai_evaluator, "model", "local-ai"),
            "base_url": getattr(self.ai_evaluator, "base_url", "http://localhost:11434"),
            "duration_ms": duration_ms,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
        }

        if existing_record:
            existing_record.strengths = processed_strengths
            existing_record.category_summaries = category_summaries
            existing_record.is_sufficient_evidence = is_sufficient
            existing_record.insufficient_evidence_reason = insufficient_reason
            existing_record.top_strengths_summary = ai_output.top_strengths_summary or ""
            existing_record.analysis_metadata = metadata_dict
            existing_record.updated_at = datetime.now(timezone.utc)
            record = existing_record
        else:
            record = ResumeStrengthAnalysis(
                resume_id=parsed_id,
                user_id=resume.user_id,
                strengths=processed_strengths,
                category_summaries=category_summaries,
                is_sufficient_evidence=is_sufficient,
                insufficient_evidence_reason=insufficient_reason,
                top_strengths_summary=ai_output.top_strengths_summary or "",
                analysis_metadata=metadata_dict,
            )
            db.add(record)

        db.commit()
        db.refresh(record)

        logger.info(
            "Successfully analyzed strengths for resume %s: %d total strengths identified",
            resume_id,
            len(processed_strengths),
        )
        return self._to_strength_analysis_data(record)


# Global singleton service
strength_analysis_service = StrengthAnalysisService()
