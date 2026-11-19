"""
Education Analysis Orchestration Service
Phase 3 | Feature 14: Education Analysis
Coordinates section detection, deterministic extraction, AI analysis, normalization, validation, timeline generation, and database persistence.
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.resume import Resume, ResumeVersion
from app.models.education import Education
from app.schemas.education import (
    EducationEntryData,
    EducationCreateRequest,
    EducationUpdateRequest,
    GradeData,
)
from app.services.preview_service import preview_service
from app.services.cleaning import cleaning_service
from app.services.storage import staging_service
from app.services.education.section_detector import detect_education_section
from app.services.education.degree_normalizer import normalize_degree
from app.services.education.grade_normalizer import extract_and_normalize_grade
from app.services.education.date_status_detector import extract_dates_and_status
from app.services.education.deterministic_extractor import extract_deterministic_education
from app.services.education.ai_extractor import education_ai_extractor
from app.services.education.validator import validate_academic_entry
from app.services.education.confidence_scorer import compute_education_confidence
from app.services.education.timeline_generator import generate_education_timeline

logger = logging.getLogger(__name__)


class EducationAnalysisService:
    """Manages the lifecycle and extraction of academic education records."""

    def __init__(self):
        # In-memory staging cache for preview sessions prior to permanent save
        self._staging_cache: Dict[str, List[EducationEntryData]] = {}

    def _resolve_cleaned_text(self, resume_id: str, db: Optional[Session] = None) -> Optional[str]:
        """Retrieves cleaned resume text from database version, preview cache, or staging."""
        if db:
            try:
                parsed_id = uuid.UUID(resume_id)
                resume = db.execute(select(Resume).where(Resume.id == parsed_id)).scalar_one_or_none()
                if resume and resume.versions:
                    latest = resume.versions[0]
                    if latest.cleaned_text:
                        return latest.cleaned_text
            except (ValueError, Exception):
                pass

        try:
            preview_data = preview_service.get_preview(resume_id)
            if preview_data and preview_data.cleaned_text:
                return preview_data.cleaned_text
        except Exception:
            pass

        try:
            staged_path = staging_service.get_staged_path(resume_id)
            if staged_path and staged_path.exists():
                clean_res = cleaning_service.clean_text(raw_text="", resume_id=resume_id)
                if clean_res and clean_res.cleaned_text:
                    return clean_res.cleaned_text
        except Exception:
            pass

        return None

    async def extract_education(
        self,
        resume_id: str,
        cleaned_text_override: Optional[str] = None,
        user_id: Optional[str] = None,
        reprocess: bool = False,
        force_overwrite: bool = False,
        db: Optional[Session] = None,
    ) -> List[EducationEntryData]:
        """
        Executes hybrid education extraction pipeline and persists structured records.
        """
        parsed_resume_uuid = None
        existing_records: List[Education] = []

        if db:
            try:
                parsed_resume_uuid = uuid.UUID(resume_id)
                existing_records = list(
                    db.execute(
                        select(Education).where(Education.resume_id == parsed_resume_uuid)
                    ).scalars().all()
                )
            except ValueError:
                pass

        # Return cached records if already present and not reprocessing
        if existing_records and not reprocess:
            return [self._record_to_schema(r) for r in existing_records]

        if not existing_records and resume_id in self._staging_cache and not reprocess:
            return self._staging_cache[resume_id]

        # 1. Retrieve cleaned text
        cleaned_text = cleaned_text_override or self._resolve_cleaned_text(resume_id, db)
        if not cleaned_text or not cleaned_text.strip():
            return []

        # 2. Detect education section
        section_text, is_explicit_section = detect_education_section(cleaned_text)
        if not section_text or not section_text.strip():
            return []

        # 3. AI-Assisted extraction with fallback
        extracted_raw_entries = await education_ai_extractor.extract_education_entries(section_text)

        # 4. Fallback to deterministic rule-based extractor if AI fails or returns empty
        if not extracted_raw_entries:
            extracted_raw_entries = extract_deterministic_education(section_text)

        processed_entries: List[Dict[str, Any]] = []

        # 5. Normalization, Validation, and Confidence Assessment
        for raw in extracted_raw_entries:
            # Degree normalization
            raw_degree = raw.get("degree")
            norm_deg, deg_level = normalize_degree(raw_degree)

            # Grade normalization
            raw_grade_input = raw.get("grade")
            parsed_grade = None
            if isinstance(raw_grade_input, dict):
                # Preserve explicit scale or values
                parsed_grade = raw_grade_input
            elif isinstance(raw_grade_input, str):
                parsed_grade = extract_and_normalize_grade(raw_grade_input)

            # Dates and status
            start_date = raw.get("start_date")
            end_date = raw.get("end_date")
            grad_status = raw.get("graduation_status") or "completed"

            # Validate entry
            entry_dict = {
                "degree": raw_degree or norm_deg,
                "normalized_degree": norm_deg,
                "degree_level": deg_level,
                "field_of_study": raw.get("field_of_study"),
                "specialization": raw.get("specialization"),
                "institution": raw.get("institution"),
                "location": raw.get("location"),
                "start_date": start_date,
                "end_date": end_date,
                "graduation_status": grad_status,
                "grade": parsed_grade,
                "achievements": raw.get("achievements") or [],
                "coursework": raw.get("coursework") or [],
                "honors": raw.get("honors") or [],
                "source_evidence": raw.get("source_evidence") or [],
            }

            validated = validate_academic_entry(entry_dict)
            if validated:
                validated["extraction_confidence"] = compute_education_confidence(
                    validated, is_explicit_section=is_explicit_section
                )
                processed_entries.append(validated)

        # 6. Generate chronological timeline
        timeline_entries = generate_education_timeline(processed_entries)

        # 7. Database Persistence
        if db and parsed_resume_uuid:
            resume_exists = db.execute(
                select(Resume).where(Resume.id == parsed_resume_uuid)
            ).scalar_one_or_none()

            if resume_exists:
                # If reprocessing, preserve manually edited records unless force_overwrite
                if existing_records:
                    if force_overwrite:
                        db.execute(delete(Education).where(Education.resume_id == parsed_resume_uuid))
                    else:
                        # Delete only unedited records
                        db.execute(
                            delete(Education).where(
                                Education.resume_id == parsed_resume_uuid,
                                Education.is_manually_edited == False,  # noqa: E712
                            )
                        )
                    db.flush()

                # Insert new timeline records
                created_models: List[Education] = []
                for item in timeline_entries:
                    new_rec = Education(
                        resume_id=parsed_resume_uuid,
                        user_id=resume_exists.user_id,
                        degree=item.get("degree"),
                        normalized_degree=item.get("normalized_degree"),
                        degree_level=item.get("degree_level"),
                        field_of_study=item.get("field_of_study"),
                        specialization=item.get("specialization"),
                        institution=item.get("institution"),
                        location=item.get("location"),
                        start_date=item.get("start_date"),
                        end_date=item.get("end_date"),
                        graduation_status=item.get("graduation_status", "completed"),
                        grade=item.get("grade"),
                        achievements=item.get("achievements", []),
                        coursework=item.get("coursework", []),
                        honors=item.get("honors", []),
                        source_evidence=item.get("source_evidence", []),
                        extraction_confidence=item.get("extraction_confidence", 0.90),
                        is_manually_edited=False,
                        manually_edited_fields=[],
                    )
                    db.add(new_rec)
                    created_models.append(new_rec)

                db.commit()

                # Return all current records (including preserved manual ones)
                all_current = list(
                    db.execute(
                        select(Education).where(Education.resume_id == parsed_resume_uuid)
                    ).scalars().all()
                )
                return [self._record_to_schema(r) for r in all_current]

        # Staging fallback
        result_schemas: List[EducationEntryData] = []
        for item in timeline_entries:
            grade_obj = GradeData(**item["grade"]) if item.get("grade") else None
            schema = EducationEntryData(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                user_id=user_id,
                degree=item.get("degree"),
                normalized_degree=item.get("normalized_degree"),
                degree_level=item.get("degree_level"),
                field_of_study=item.get("field_of_study"),
                specialization=item.get("specialization"),
                institution=item.get("institution"),
                location=item.get("location"),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
                graduation_status=item.get("graduation_status", "completed"),
                grade=grade_obj,
                achievements=item.get("achievements", []),
                coursework=item.get("coursework", []),
                honors=item.get("honors", []),
                source_evidence=item.get("source_evidence", []),
                extraction_confidence=item.get("extraction_confidence", 0.90),
                is_manually_edited=False,
                manually_edited_fields=[],
            )
            result_schemas.append(schema)

        self._staging_cache[resume_id] = result_schemas
        return result_schemas

    def get_education(self, resume_id: str, db: Session) -> List[EducationEntryData]:
        """Retrieves stored education records for a resume."""
        try:
            parsed_id = uuid.UUID(resume_id)
            records = list(
                db.execute(
                    select(Education).where(Education.resume_id == parsed_id)
                ).scalars().all()
            )
            if records:
                return [self._record_to_schema(r) for r in records]
        except ValueError:
            pass

        if resume_id in self._staging_cache:
            return self._staging_cache[resume_id]

        return []

    def add_education_entry(
        self,
        resume_id: str,
        payload: EducationCreateRequest,
        db: Session,
    ) -> Optional[EducationEntryData]:
        """Adds a new manual education record to a resume."""
        try:
            parsed_id = uuid.UUID(resume_id)
        except ValueError:
            return None

        resume = db.execute(select(Resume).where(Resume.id == parsed_id)).scalar_one_or_none()
        if not resume:
            return None

        norm_deg, deg_level = normalize_degree(payload.degree)

        grade_dict = payload.grade.model_dump(exclude_unset=True) if payload.grade else None

        record = Education(
            resume_id=parsed_id,
            user_id=resume.user_id,
            degree=payload.degree,
            normalized_degree=payload.normalized_degree or norm_deg,
            degree_level=payload.degree_level or deg_level,
            field_of_study=payload.field_of_study,
            specialization=payload.specialization,
            institution=payload.institution,
            location=payload.location,
            start_date=payload.start_date,
            end_date=payload.end_date,
            graduation_status=payload.graduation_status or "completed",
            grade=grade_dict,
            achievements=payload.achievements or [],
            coursework=payload.coursework or [],
            honors=payload.honors or [],
            source_evidence=["User manually added entry"],
            extraction_confidence=1.0,  # User confirmed
            is_manually_edited=True,
            manually_edited_fields=["all"],
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return self._record_to_schema(record)

    def update_education_entry(
        self,
        resume_id: str,
        education_id: str,
        payload: EducationUpdateRequest,
        db: Session,
    ) -> Optional[EducationEntryData]:
        """Updates an existing education record."""
        try:
            parsed_resume_id = uuid.UUID(resume_id)
            parsed_edu_id = uuid.UUID(education_id)
        except ValueError:
            return None

        record = db.execute(
            select(Education).where(
                Education.id == parsed_edu_id,
                Education.resume_id == parsed_resume_id,
            )
        ).scalar_one_or_none()

        if not record:
            return None

        edited_fields = list(record.manually_edited_fields or [])
        update_dict = payload.model_dump(exclude_unset=True)

        for key, val in update_dict.items():
            if key == "grade" and val is not None:
                record.grade = val
            elif hasattr(record, key):
                setattr(record, key, val)
            if key not in edited_fields:
                edited_fields.append(key)

        record.is_manually_edited = True
        record.manually_edited_fields = edited_fields
        record.extraction_confidence = 1.0  # Confirmed by user

        db.commit()
        db.refresh(record)
        return self._record_to_schema(record)

    def delete_education_entry(
        self,
        resume_id: str,
        education_id: str,
        db: Session,
    ) -> bool:
        """Deletes an education record."""
        try:
            parsed_resume_id = uuid.UUID(resume_id)
            parsed_edu_id = uuid.UUID(education_id)
        except ValueError:
            return False

        record = db.execute(
            select(Education).where(
                Education.id == parsed_edu_id,
                Education.resume_id == parsed_resume_id,
            )
        ).scalar_one_or_none()

        if not record:
            return False

        db.delete(record)
        db.commit()
        return True

    def _record_to_schema(self, record: Education) -> EducationEntryData:
        """Converts SQLAlchemy model to Pydantic schema."""
        grade_obj = GradeData(**record.grade) if record.grade and isinstance(record.grade, dict) else None

        return EducationEntryData(
            id=str(record.id),
            resume_id=str(record.resume_id),
            user_id=str(record.user_id) if record.user_id else None,
            degree=record.degree,
            normalized_degree=record.normalized_degree,
            degree_level=record.degree_level,
            field_of_study=record.field_of_study,
            specialization=record.specialization,
            institution=record.institution,
            location=record.location,
            start_date=record.start_date,
            end_date=record.end_date,
            graduation_status=record.graduation_status,
            grade=grade_obj,
            achievements=record.achievements or [],
            coursework=record.coursework or [],
            honors=record.honors or [],
            source_evidence=record.source_evidence or [],
            extraction_confidence=record.extraction_confidence,
            is_manually_edited=record.is_manually_edited,
            manually_edited_fields=record.manually_edited_fields or [],
            created_at=record.created_at.isoformat() if record.created_at else None,
            updated_at=record.updated_at.isoformat() if record.updated_at else None,
        )


education_service = EducationAnalysisService()
EducationExtractionService = EducationAnalysisService
