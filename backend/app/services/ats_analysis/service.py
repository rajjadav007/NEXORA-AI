"""
Resume ATS Compatibility Analysis Service
Phase 4 | Feature 24: ATS Compatibility Analysis
Orchestrates file inspection, deterministic evaluation, AI explanations,
and PostgreSQL persistence.
"""

import uuid
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.security import verify_resume_access, validate_resume_id
from app.core.config import settings
from app.models.resume import Resume
from app.models.ats_analysis import ResumeATSAnalysis
from app.schemas.ats_analysis import (
    ATSAnalysisData,
    ATSCategoryScore,
    ATSIssue,
    SectionDetectionItem,
    KeywordFindings,
    AIFeedback,
    RecommendationItem,
    STANDARD_ATS_DISCLAIMER,
)
from app.services.permanent_storage import permanent_storage
from app.services.preview_service import preview_service
from app.services.ats_analysis.deterministic_scorer import (
    ats_deterministic_scorer,
    ATSDeterministicScorer,
)
from app.services.ats_analysis.ai_evaluator import (
    ats_ai_evaluator,
    ATSAIEvaluator,
)

logger = logging.getLogger(__name__)


class ATSAnalysisService:
    """Service managing deterministic ATS compatibility evaluation and contextual feedback."""

    def __init__(
        self,
        scorer: Optional[ATSDeterministicScorer] = None,
        ai_evaluator: Optional[ATSAIEvaluator] = None,
    ):
        self.scorer = scorer or ats_deterministic_scorer
        self.ai_evaluator = ai_evaluator or ats_ai_evaluator

    def _resolve_resume_file_path(self, resume: Resume, resume_id: str) -> Optional[Path]:
        """Resolves the physical resume document on disk (PDF or DOCX)."""
        # 1. Try permanent storage from resume.storage_key
        if resume and resume.storage_key:
            path = permanent_storage.get_storage_path(resume.storage_key)
            if path and path.exists():
                return path

        # 2. Try latest resume version
        if resume and resume.versions and len(resume.versions) > 0:
            for ver in resume.versions:
                if ver.storage_key:
                    path = permanent_storage.get_storage_path(ver.storage_key)
                    if path and path.exists():
                        return path

        # 3. Check staging directory
        staging_dir = Path(settings.RESUME_UPLOAD_STAGING_DIR).resolve()
        for candidate in staging_dir.glob(f"{resume_id}*"):
            if candidate.is_file():
                return candidate

        return None

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

    def _to_ats_analysis_data(self, record: ResumeATSAnalysis) -> ATSAnalysisData:
        """Transforms SQLAlchemy database record into validated Pydantic schema."""
        category_scores_dict = {
            k: ATSCategoryScore(**v) for k, v in (record.category_scores or {}).items()
        }
        verified_issues = [ATSIssue(**i) for i in (record.verified_issues or [])]
        formatting_risks = [ATSIssue(**r) for r in (record.formatting_risks or [])]
        detected_sections = [SectionDetectionItem(**s) for s in (record.detected_sections or [])]

        raw_kw = record.keyword_findings or {}
        keyword_findings = KeywordFindings(
            total_detected_keywords=raw_kw.get("total_detected_keywords", 0),
            top_technical_keywords=raw_kw.get("top_technical_keywords", []),
            top_action_verbs=raw_kw.get("top_action_verbs", []),
            recommended_keywords=raw_kw.get("recommended_keywords", []),
            keyword_density_note=raw_kw.get("keyword_density_note", ""),
        )

        raw_ai = record.ai_feedback or {}
        ai_recs = [RecommendationItem(**r) for r in raw_ai.get("tailored_recommendations", [])]
        ai_feedback = AIFeedback(
            executive_summary=raw_ai.get("executive_summary", ""),
            tailored_recommendations=ai_recs,
            keyword_optimization_advice=raw_ai.get("keyword_optimization_advice", ""),
        )

        # Interpretation based on score
        score = record.ats_score
        if score >= 85:
            interpretation = "Excellent ATS compatibility. High probability of accurate field parsing and recruiter indexing."
        elif score >= 70:
            interpretation = "Good ATS parseability with a few minor formatting or content gaps to resolve."
        elif score >= 50:
            interpretation = "Moderate parsing risks. Multiple sections or formatting structures may fail ATS extraction."
        else:
            interpretation = "High risk of ATS rejection. Critical sections or layout structures severely impair automated parsing."

        return ATSAnalysisData(
            id=str(record.id),
            resume_id=str(record.resume_id),
            ats_score=record.ats_score,
            score_grade=record.score_grade,
            score_interpretation=interpretation,
            category_scores=category_scores_dict,
            verified_issues=verified_issues,
            formatting_risks=formatting_risks,
            detected_sections=detected_sections,
            missing_sections=record.missing_sections or [],
            keyword_findings=keyword_findings,
            ai_feedback=ai_feedback,
            disclaimer=record.disclaimer or STANDARD_ATS_DISCLAIMER,
            analysis_metadata=record.analysis_metadata or {},
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else "",
        )

    def get_ats_analysis(self, resume_id: str, db: Session) -> Optional[ATSAnalysisData]:
        """Retrieves cached ATS compatibility analysis for a given resume."""
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        query = select(ResumeATSAnalysis).where(ResumeATSAnalysis.resume_id == parsed_id)
        record = db.execute(query).scalar_one_or_none()
        if not record:
            return None

        return self._to_ats_analysis_data(record)

    async def calculate_ats_analysis(
        self,
        resume_id: str,
        force_recalculate: bool = False,
        db: Session = None,
    ) -> ATSAnalysisData:
        """
        Executes deterministic ATS scoring engine, obtains contextual AI recommendations,
        and persists results in PostgreSQL.
        """
        verify_resume_access(resume_id, db)
        parsed_id = validate_resume_id(resume_id)

        # 1. Check cache
        if not force_recalculate:
            existing = self.get_ats_analysis(resume_id, db)
            if existing:
                logger.info("Returning cached ATS analysis for resume %s", resume_id)
                return existing

        # 2. Retrieve resume record
        resume = db.execute(select(Resume).where(Resume.id == parsed_id)).scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found for ID: {resume_id}",
            )

        # 3. Resolve file and cleaned text
        file_path = self._resolve_resume_file_path(resume, resume_id)
        cleaned_text = self._resolve_cleaned_text(resume, resume_id, db)

        # 4. Run deterministic scoring
        start_time = time.time()
        audit_results = self.scorer.evaluate(
            resume=resume,
            file_path=file_path,
            cleaned_text=cleaned_text,
        )

        ats_score = audit_results["ats_score"]
        score_grade = audit_results["score_grade"]
        category_scores = audit_results["category_scores"]
        verified_issues = audit_results["verified_issues"]
        formatting_risks = audit_results["formatting_risks"]
        detected_sections = audit_results["detected_sections"]
        missing_sections = audit_results["missing_sections"]
        keyword_findings = audit_results["keyword_findings"]

        # 5. Run AI contextual feedback generator (Ollama + LangChain)
        ai_feedback: AIFeedback = await self.ai_evaluator.generate_feedback(
            ats_score=ats_score,
            score_grade=score_grade,
            category_scores=category_scores,
            verified_issues=verified_issues,
            formatting_risks=formatting_risks,
            keywords=keyword_findings.top_technical_keywords,
            cleaned_text=cleaned_text,
        )
        duration = round(time.time() - start_time, 2)

        metadata = {
            "file_inspected": str(file_path.name) if file_path else "text_only",
            "scoring_engine": "deterministic_v1",
            "duration_seconds": duration,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

        # 6. Serialize for PostgreSQL storage
        cat_scores_dump = {k: v.model_dump() for k, v in category_scores.items()}
        issues_dump = [i.model_dump() for i in verified_issues]
        risks_dump = [r.model_dump() for r in formatting_risks]
        sections_dump = [s.model_dump() for s in detected_sections]
        kw_dump = keyword_findings.model_dump()
        ai_dump = ai_feedback.model_dump()

        # 7. Upsert into database
        existing_record = db.execute(
            select(ResumeATSAnalysis).where(ResumeATSAnalysis.resume_id == parsed_id)
        ).scalar_one_or_none()

        if existing_record:
            existing_record.ats_score = ats_score
            existing_record.score_grade = score_grade
            existing_record.category_scores = cat_scores_dump
            existing_record.verified_issues = issues_dump
            existing_record.formatting_risks = risks_dump
            existing_record.detected_sections = sections_dump
            existing_record.missing_sections = missing_sections
            existing_record.keyword_findings = kw_dump
            existing_record.ai_feedback = ai_dump
            existing_record.analysis_metadata = metadata
            db.commit()
            db.refresh(existing_record)
            saved_record = existing_record
        else:
            new_record = ResumeATSAnalysis(
                resume_id=parsed_id,
                user_id=resume.user_id,
                ats_score=ats_score,
                score_grade=score_grade,
                category_scores=cat_scores_dump,
                verified_issues=issues_dump,
                formatting_risks=risks_dump,
                detected_sections=sections_dump,
                missing_sections=missing_sections,
                keyword_findings=kw_dump,
                ai_feedback=ai_dump,
                analysis_metadata=metadata,
                disclaimer=STANDARD_ATS_DISCLAIMER,
            )
            db.add(new_record)
            db.commit()
            db.refresh(new_record)
            saved_record = new_record

        return self._to_ats_analysis_data(saved_record)


ats_analysis_service = ATSAnalysisService()
