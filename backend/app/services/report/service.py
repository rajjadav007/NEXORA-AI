"""
Service Layer for AI Resume Report Generation & Retrieval
Phase 5 | Feature 31: AI Resume Report
"""

import uuid
import time
import re
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.resume import Resume
from app.models.report import ResumeReport
from app.models.improvement_tracker import ResumeTimelineEvent
from app.schemas.report import (
    ReportSections,
    ResumeReportData,
    ReportHistoryItem,
)
from app.services.report.ai_generator import (
    report_ai_generator,
    OllamaUnavailableError,
    AIOutputValidationError,
)
from app.services.report.pdf_generator import report_pdf_generator

logger = logging.getLogger(__name__)


class ResumeReportService:
    """Coordinates structured data assembly, Ollama invocation, persistence, and history for AI Resume Reports."""

    async def generate_report(
        self,
        resume_id: str,
        force_recalculate: bool = False,
        fallback_to_deterministic: bool = False,
        user_id: Optional[str] = None,
        db: Session = None,
    ) -> ResumeReportData:
        """
        Generates or retrieves a comprehensive AI Resume Report.
        Leverages existing Phase 3, Phase 4, and Phase 5 evaluations.
        Enforces local Ollama execution with fallback options.
        """
        resume = self._get_resume_with_relations(resume_id, db)

        # 1. Check for existing report if not forcing recalculation
        if not force_recalculate:
            latest_report = db.execute(
                select(ResumeReport)
                .where(ResumeReport.resume_id == resume.id)
                .order_by(ResumeReport.created_at.desc())
            ).scalars().first()

            if latest_report:
                logger.info("Returning existing cached AI Resume Report %s for resume %s", latest_report.id, resume_id)
                return self._to_report_data(latest_report)

        # 2. Extract structured analysis data from existing records
        candidate_profile = self._build_candidate_profile(resume)
        scores_summary = self._build_scores_summary(resume)
        skills_summary = self._build_skills_summary(resume)
        experience_and_projects = self._build_experience_and_projects(resume)
        education_and_certifications = self._build_education_and_certifications(resume)
        strengths_and_weaknesses = self._build_strengths_and_weaknesses(resume)
        ats_and_recommendations = self._build_ats_and_recommendations(resume)

        # 3. Invoke Local Ollama model
        start_time = time.time()
        sections: ReportSections

        try:
            sections = await report_ai_generator.generate_report_sections(
                candidate_profile=candidate_profile,
                scores_summary=scores_summary,
                skills_summary=skills_summary,
                experience_and_projects=experience_and_projects,
                education_and_certifications=education_and_certifications,
                strengths_and_weaknesses=strengths_and_weaknesses,
                ats_and_recommendations=ats_and_recommendations,
            )
        except OllamaUnavailableError as oue:
            if fallback_to_deterministic:
                logger.warning("Ollama unavailable, using deterministic report fallback as requested.")
                sections = report_ai_generator.synthesize_deterministic_report(
                    candidate_profile=candidate_profile,
                    scores_summary=scores_summary,
                    skills_summary=skills_summary,
                    experience_and_projects=experience_and_projects,
                    education_and_certifications=education_and_certifications,
                    strengths_and_weaknesses=strengths_and_weaknesses,
                    ats_and_recommendations=ats_and_recommendations,
                )
            else:
                raise oue

        duration = round(time.time() - start_time, 2)

        # 4. Persist in PostgreSQL
        report_record = ResumeReport(
            id=uuid.uuid4(),
            resume_id=resume.id,
            user_id=resume.user_id,
            model_name=settings.OLLAMA_MODEL,
            status="COMPLETED",
            report_data=sections.model_dump(),
            executive_summary=sections.executive_summary.overall_assessment,
            generation_duration_seconds=duration,
            created_at=datetime.now(timezone.utc),
        )
        db.add(report_record)

        # 5. Log milestone in timeline
        evt = ResumeTimelineEvent(
            resume_id=resume.id,
            user_id=resume.user_id,
            event_type="REPORT_GENERATED",
            title="AI Resume Report Generated",
            description=f"Personalized 11-section AI evaluation generated via {settings.OLLAMA_MODEL}.",
            event_metadata={
                "report_id": str(report_record.id),
                "model": settings.OLLAMA_MODEL,
                "duration_seconds": duration,
            },
            created_at=report_record.created_at,
        )
        db.add(evt)
        db.commit()
        db.refresh(report_record)

        return self._to_report_data(report_record)

    def get_latest_report(self, resume_id: str, db: Session) -> Optional[ResumeReportData]:
        """Retrieves the most recent AI Resume Report for a resume, or None if none exist."""
        resume = self._get_resume_with_relations(resume_id, db)
        report = db.execute(
            select(ResumeReport)
            .where(ResumeReport.resume_id == resume.id)
            .order_by(ResumeReport.created_at.desc())
        ).scalars().first()

        if not report:
            return None

        return self._to_report_data(report)

    def get_report_by_id(self, resume_id: str, report_id: str, db: Session) -> ResumeReportData:
        """Retrieves an individual report by its ID."""
        resume = self._get_resume_with_relations(resume_id, db)
        try:
            report_uuid = uuid.UUID(report_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report ID format: {report_id}",
            )

        report = db.execute(
            select(ResumeReport).where(
                and_(
                    ResumeReport.id == report_uuid,
                    ResumeReport.resume_id == resume.id,
                )
            )
        ).scalar_one_or_none()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ID {report_id} not found.",
            )

        return self._to_report_data(report)

    def get_report_history(self, resume_id: str, db: Session) -> List[ReportHistoryItem]:
        """Retrieves history list of all generated reports for a resume."""
        resume = self._get_resume_with_relations(resume_id, db)
        reports = db.execute(
            select(ResumeReport)
            .where(ResumeReport.resume_id == resume.id)
            .order_by(ResumeReport.created_at.desc())
        ).scalars().all()

        history_items = []
        for r in reports:
            ov_score = None
            if r.report_data and "quality_assessment" in r.report_data:
                ov_score = r.report_data["quality_assessment"].get("overall_score")

            history_items.append(
                ReportHistoryItem(
                    report_id=str(r.id),
                    resume_id=str(r.resume_id),
                    generated_at=r.created_at.isoformat() if r.created_at else "",
                    model=r.model_name,
                    status=r.status,
                    executive_summary=r.executive_summary[:200] if r.executive_summary else "",
                    overall_score=ov_score,
                )
            )

        return history_items

    def export_report_pdf(
        self,
        resume_id: str,
        report_id: str,
        db: Session,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exports an existing saved AI Resume Report as a professionally designed PDF.
        Phase 5 | Feature 32: PDF Report Export
        Never regenerates the AI report. Uses saved report and analytics data.
        Returns a dict: {"pdf_bytes": bytes, "filename": str, "report_id": str}
        """
        resume = self._get_resume_with_relations(resume_id, db)

        try:
            report_uuid = uuid.UUID(report_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report ID format: {report_id}",
            )

        report = db.execute(
            select(ResumeReport).where(
                and_(
                    ResumeReport.id == report_uuid,
                    ResumeReport.resume_id == resume.id,
                )
            )
        ).scalar_one_or_none()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ID {report_id} not found.",
            )

        # Construct report_data directly from stored record, robust to optional section omission
        raw_sections = report.report_data.get("sections") if isinstance(report.report_data, dict) and "sections" in report.report_data else (report.report_data or {})
        report_data = {
            "report_id": str(report.id),
            "resume_id": str(report.resume_id),
            "generated_at": report.created_at.isoformat() if report.created_at else "",
            "model": report.model_name or "gemma4:12b",
            "status": report.status or "COMPLETED",
            "sections": raw_sections,
            "generation_duration_seconds": report.generation_duration_seconds,
        }

        # Sanitize resume filename for safe Content-Disposition
        raw_name = resume.original_filename or "resume"
        if "." in raw_name:
            raw_name = raw_name.rsplit(".", 1)[0]
        clean_name = re.sub(r"[^\w\-]", "_", raw_name)
        clean_name = re.sub(r"_+", "_", clean_name).strip("_") or "resume"
        pdf_filename = f"Nexora_AI_Resume_Report_{clean_name}_{str(report.id)[:8]}.pdf"

        # Generate PDF bytes via ReportLab
        try:
            pdf_bytes = report_pdf_generator.generate_pdf(
                report_data=report_data,
                resume_filename=resume.original_filename or "resume.pdf",
            )
        except Exception as exc:
            logger.error("Failed to generate PDF for report %s: %s", report_id, exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate PDF document: {str(exc)}",
            )

        return {
            "pdf_bytes": pdf_bytes,
            "filename": pdf_filename,
            "report_id": str(report.id),
        }

    # --- Structured Payload Extractors ---

    def _build_candidate_profile(self, resume: Resume) -> Dict[str, Any]:
        pi = resume.personal_information
        return {
            "full_name": pi.full_name if pi and pi.full_name else "Candidate",
            "email": pi.email if pi else None,
            "headline": pi.headline if pi and hasattr(pi, "headline") else None,
            "filename": resume.original_filename,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
        }

    def _build_scores_summary(self, resume: Resume) -> Dict[str, Any]:
        qual = resume.quality_score
        ats = resume.ats_analysis
        grammar = resume.grammar_analysis

        comp_score = None
        if qual and qual.category_scores and "content_completeness" in qual.category_scores:
            c_val = qual.category_scores["content_completeness"]
            comp_score = c_val.get("score_percentage") or c_val.get("score")

        return {
            "overall_score": qual.overall_score if qual else None,
            "ats_compatibility_score": ats.overall_score if ats else None,
            "readability_score": grammar.overall_readability_score if grammar else None,
            "content_completeness_score": comp_score,
            "quality_categories": qual.category_scores if qual else {},
        }

    def _build_skills_summary(self, resume: Resume) -> Dict[str, Any]:
        skills = resume.resume_skills or []
        names = [s.canonical_name for s in skills]

        prog_langs = [s.canonical_name for s in skills if s.domain == "Programming Languages"]
        ai_skills = [s.canonical_name for s in skills if s.domain in ["AI and Machine Learning", "Data Science and Analytics"]]
        frameworks = [s.canonical_name for s in skills if s.domain in ["Frameworks and Libraries", "Development Tools", "Databases", "Cloud and DevOps"]]

        return {
            "total_skills_count": len(names),
            "technical_skills": names,
            "ai_ml_skills": ai_skills,
            "programming_languages": prog_langs,
            "frameworks_and_tools": frameworks,
        }

    def _build_experience_and_projects(self, resume: Resume) -> Dict[str, Any]:
        exp_records = resume.experience_records or []
        proj_records = resume.projects or []

        roles = [
            {
                "title": e.job_title,
                "company": e.company_name,
                "duration": f"{e.start_date or ''} - {e.end_date or 'Present'}",
                "description": (e.description or "")[:300],
            }
            for e in exp_records
        ]

        projects = [
            {
                "title": p.title,
                "technologies": p.technologies or [],
                "description": (p.description or "")[:300],
            }
            for p in proj_records
        ]

        return {
            "roles": roles,
            "projects": projects,
        }

    def _build_education_and_certifications(self, resume: Resume) -> Dict[str, Any]:
        edu_records = resume.education_records or []
        cert_records = resume.certifications or []

        degrees = [f"{e.degree_type or ''} in {e.major or ''} at {e.institution_name or ''}".strip() for e in edu_records]
        certs = [c.name for c in cert_records]

        return {
            "degrees": degrees,
            "certifications": certs,
        }

    def _build_strengths_and_weaknesses(self, resume: Resume) -> Dict[str, Any]:
        st = resume.strength_analysis
        wk = resume.weakness_analysis
        qual = resume.quality_score

        strengths = st.strengths if st and st.strengths else (qual.strengths if qual else [])
        weaknesses = wk.weaknesses if wk and wk.weaknesses else (qual.missing_information if qual else [])

        return {
            "strengths": strengths or [],
            "weaknesses": weaknesses or [],
        }

    def _build_ats_and_recommendations(self, resume: Resume) -> Dict[str, Any]:
        ats = resume.ats_analysis
        rec = resume.recommendation_analysis

        recs = rec.recommendations if rec and rec.recommendations else []
        ats_flags = ats.missing_elements if ats and ats.missing_elements else []

        return {
            "ats_score": ats.overall_score if ats else None,
            "formatting_flags": ats_flags,
            "recommendations": recs,
        }

    def _to_report_data(self, record: ResumeReport) -> ResumeReportData:
        """Converts database model to validated Pydantic schema."""
        raw_data = record.report_data or {}
        sections = ReportSections.model_validate(raw_data)

        return ResumeReportData(
            report_id=str(record.id),
            resume_id=str(record.resume_id),
            generated_at=record.created_at.isoformat() if record.created_at else "",
            model=record.model_name,
            status=record.status,
            sections=sections,
            generation_duration_seconds=record.generation_duration_seconds,
        )

    def _get_resume_with_relations(self, resume_id: str, db: Session) -> Resume:
        """Fetches resume with all required relations."""
        try:
            resume_uuid = uuid.UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume ID format: {resume_id}",
            )

        resume = db.execute(
            select(Resume)
            .options(
                joinedload(Resume.personal_information),
                joinedload(Resume.quality_score),
                joinedload(Resume.ats_analysis),
                joinedload(Resume.grammar_analysis),
                joinedload(Resume.strength_analysis),
                joinedload(Resume.weakness_analysis),
                joinedload(Resume.recommendation_analysis),
                joinedload(Resume.resume_skills),
                joinedload(Resume.education_records),
                joinedload(Resume.experience_records),
                joinedload(Resume.projects),
                joinedload(Resume.certifications),
                joinedload(Resume.achievements),
            )
            .where(Resume.id == resume_uuid)
        ).unique().scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found.",
            )

        return resume


resume_report_service = ResumeReportService()
