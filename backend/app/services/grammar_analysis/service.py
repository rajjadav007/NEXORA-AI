"""
Resume Grammar & Clarity Analysis Service
Phase 4 | Feature 25: Grammar & Clarity Analysis
Orchestrates resume text extraction, readability measurements, LangChain
ChatOllama writing quality evaluation, before-and-after sentence comparisons,
and PostgreSQL persistence without overwriting the original resume.
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
from app.models.grammar_analysis import ResumeGrammarAnalysis
from app.schemas.grammar_analysis import (
    GrammarAnalysisData,
    GrammarIssue,
    SentenceComparison,
    ReadabilityMetrics,
    ResumeGrammarAIStructuredOutput,
    GRAMMAR_CATEGORIES,
)
from app.services.preview_service import preview_service
from app.services.grammar_analysis.readability import compute_readability_metrics
from app.services.grammar_analysis.ai_evaluator import (
    grammar_ai_evaluator,
    GrammarAIEvaluator,
)

logger = logging.getLogger(__name__)


class GrammarAnalysisService:
    """Service managing candidate writing quality, grammar, spelling, clarity, and tone analysis."""

    def __init__(self, ai_evaluator: Optional[GrammarAIEvaluator] = None):
        self.ai_evaluator = ai_evaluator or grammar_ai_evaluator

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
                lines.append(f"Professional Summary: {summary}")

        if resume_skills:
            skill_list = [getattr(s, "canonical_name", None) or getattr(s, "original_name", str(s)) for s in resume_skills[:35]]
            lines.append(f"Skills: {', '.join(skill_list)}")

        if experience_records:
            lines.append(f"Work Experience ({len(experience_records)} roles):")
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
                lines.append(f"- {p_title}: {p_desc[:200]}")

        if education_records:
            lines.append(f"Education ({len(education_records)}):")
            for edu in education_records[:3]:
                deg = getattr(edu, "degree_name", None) or getattr(edu, "degree", "Degree")
                inst = getattr(edu, "institution_name", None) or getattr(edu, "institution", "Institution")
                lines.append(f"- {deg} at {inst}")

        return "\n".join(lines) if lines else "No structured resume information available."

    def _to_grammar_analysis_data(self, record: ResumeGrammarAnalysis) -> GrammarAnalysisData:
        """Transforms SQLAlchemy database record into validated Pydantic schema."""
        raw_issues = record.issues or []
        issues_list = [GrammarIssue(**i) for i in raw_issues]

        raw_comparisons = record.sentence_comparisons or []
        comparisons_list = [SentenceComparison(**c) for c in raw_comparisons]

        raw_metrics = record.readability_metrics or {}
        metrics = ReadabilityMetrics(
            readability_score=raw_metrics.get("readability_score", 65.0),
            grade_level=raw_metrics.get("grade_level", "Professional (Grade 10-12)"),
            avg_words_per_sentence=raw_metrics.get("avg_words_per_sentence", 15.0),
            total_words=raw_metrics.get("total_words", 0),
            complexity_assessment=raw_metrics.get("complexity_assessment", "Clear and professional."),
        )

        return GrammarAnalysisData(
            id=str(record.id),
            resume_id=str(record.resume_id),
            writing_score=record.writing_score,
            writing_grade=record.writing_grade,
            overall_assessment=record.overall_assessment or "",
            readability_metrics=metrics,
            category_counts=record.category_counts or {},
            issues=issues_list,
            sentence_comparisons=comparisons_list,
            analysis_metadata=record.analysis_metadata or {},
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else "",
        )

    def get_grammar_analysis(self, resume_id: str, db: Session) -> Optional[GrammarAnalysisData]:
        """Retrieves cached grammar and clarity analysis for a given resume."""
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        query = select(ResumeGrammarAnalysis).where(ResumeGrammarAnalysis.resume_id == parsed_id)
        record = db.execute(query).scalar_one_or_none()
        if not record:
            return None

        return self._to_grammar_analysis_data(record)

    async def calculate_grammar_analysis(
        self,
        resume_id: str,
        force_recalculate: bool = False,
        db: Session = None,
    ) -> GrammarAnalysisData:
        """
        Executes AI grammar, spelling, clarity, tone, and readability audit.
        Generates before-and-after sentence comparisons and saves results without overwriting the resume.
        """
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        # 1. Check cache
        if not force_recalculate:
            existing = self.get_grammar_analysis(resume_id, db)
            if existing:
                logger.info("Returning cached grammar analysis for resume %s", resume_id)
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

        # 5. Compute linguistic readability metrics
        text_for_readability = cleaned_text if len(cleaned_text.strip()) > 50 else resume_summary
        readability_metrics = compute_readability_metrics(text_for_readability)

        # 6. Run LLM writing quality audit
        start_time = time.time()
        ai_output: ResumeGrammarAIStructuredOutput = await self.ai_evaluator.evaluate_grammar(
            resume_summary=resume_summary,
            cleaned_text=cleaned_text,
        )
        duration = round(time.time() - start_time, 2)

        # 7. Process issues and compute category counts
        category_counts: Dict[str, int] = {k: 0 for k in GRAMMAR_CATEGORIES.keys()}
        formatted_issues: List[Dict[str, Any]] = []

        penalty = 0
        for idx, item in enumerate(ai_output.issues, start=1):
            cat = item.category if item.category in GRAMMAR_CATEGORIES else "clarity"
            category_counts[cat] = category_counts.get(cat, 0) + 1

            sev = item.severity.capitalize() if item.severity.capitalize() in ["High", "Medium", "Low"] else "Medium"
            if sev == "High":
                penalty += 6
            elif sev == "Medium":
                penalty += 3
            else:
                penalty += 1

            formatted_issues.append({
                "id": f"grammar_issue_{idx}",
                "category": cat,
                "category_name": GRAMMAR_CATEGORIES.get(cat, "Writing Quality"),
                "original_text": item.original_text,
                "suggested_text": item.suggested_text,
                "explanation": item.explanation,
                "severity": sev,
                "section": item.section or "General",
            })

        # Calculate writing score (100 base minus severity deductions, clamped 45-100)
        writing_score = max(45, min(100, 100 - penalty))

        if writing_score >= 90:
            writing_grade = "Excellent"
        elif writing_score >= 75:
            writing_grade = "Professional"
        elif writing_score >= 60:
            writing_grade = "Needs Polish"
        else:
            writing_grade = "Needs Substantial Revision"

        # 8. Process sentence comparisons
        formatted_comparisons: List[Dict[str, Any]] = []
        for comp in ai_output.sentence_comparisons:
            formatted_comparisons.append({
                "original_sentence": comp.original_sentence,
                "improved_sentence": comp.improved_sentence,
                "reason": comp.reason,
                "section": comp.section or "General",
            })

        metadata = {
            "model": self.ai_evaluator.model,
            "duration_seconds": duration,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "total_issues": len(formatted_issues),
            "total_comparisons": len(formatted_comparisons),
        }

        # 9. Upsert into database
        existing_record = db.execute(
            select(ResumeGrammarAnalysis).where(ResumeGrammarAnalysis.resume_id == parsed_id)
        ).scalar_one_or_none()

        if existing_record:
            existing_record.writing_score = writing_score
            existing_record.writing_grade = writing_grade
            existing_record.overall_assessment = ai_output.overall_assessment
            existing_record.readability_metrics = readability_metrics.model_dump()
            existing_record.category_counts = category_counts
            existing_record.issues = formatted_issues
            existing_record.sentence_comparisons = formatted_comparisons
            existing_record.analysis_metadata = metadata
            db.commit()
            db.refresh(existing_record)
            saved_record = existing_record
        else:
            new_record = ResumeGrammarAnalysis(
                resume_id=parsed_id,
                user_id=resume.user_id,
                writing_score=writing_score,
                writing_grade=writing_grade,
                overall_assessment=ai_output.overall_assessment,
                readability_metrics=readability_metrics.model_dump(),
                category_counts=category_counts,
                issues=formatted_issues,
                sentence_comparisons=formatted_comparisons,
                analysis_metadata=metadata,
            )
            db.add(new_record)
            db.commit()
            db.refresh(new_record)
            saved_record = new_record

        return self._to_grammar_analysis_data(saved_record)


grammar_analysis_service = GrammarAnalysisService()
