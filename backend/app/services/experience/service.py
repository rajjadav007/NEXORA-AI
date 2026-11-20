"""
Experience Analysis Orchestration Service
Phase 3 | Feature 15: Experience Analysis
Coordinates section detection, deterministic extraction, AI analysis, normalization, duration calculation, career progression, and database persistence.
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.resume import Resume, ResumeVersion
from app.models.experience import Experience
from app.schemas.experience import (
    ExperienceEntryData,
    ExperienceSummaryData,
    ExperienceCreateRequest,
    ExperienceUpdateRequest,
    CareerProgressionResponse,
    CareerProgressionItem,
)
from app.services.preview_service import preview_service
from app.services.cleaning import cleaning_service
from app.services.storage import staging_service
from app.services.experience.section_detector import detect_experience_section
from app.services.experience.normalizer import (
    normalize_company,
    normalize_job_title,
    detect_employment_type,
    extract_technologies_from_text,
)
from app.services.experience.date_duration_calculator import (
    normalize_date_string,
    calculate_individual_duration_months,
    calculate_aggregate_experience_months,
    parse_date_to_parts,
    date_to_absolute_month,
)
from app.services.experience.content_extractor import categorize_experience_bullets
from app.services.experience.career_progression import analyze_career_progression
from app.services.experience.confidence_scorer import compute_experience_confidence
from app.services.experience.deterministic_extractor import extract_deterministic_experience
from app.services.experience.ai_extractor import experience_ai_extractor

logger = logging.getLogger(__name__)


class ExperienceAnalysisService:
    """Manages extraction, validation, and lifecycle of work experience records."""

    def __init__(self):
        # In-memory staging cache for preview sessions prior to permanent save
        self._staging_cache: Dict[str, List[ExperienceEntryData]] = {}

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

    def _record_to_schema(self, record: Experience) -> ExperienceEntryData:
        """Converts an Experience SQLAlchemy model into an ExperienceEntryData schema."""
        return ExperienceEntryData(
            id=str(record.id),
            resume_id=str(record.resume_id),
            user_id=str(record.user_id) if record.user_id else None,
            company=record.company,
            job_title=record.job_title,
            employment_type=record.employment_type or "full_time",
            location=record.location,
            start_date=record.start_date,
            end_date=record.end_date,
            is_current=record.is_current,
            duration_months=record.duration_months,
            responsibilities=record.responsibilities or [],
            technical_contributions=record.technical_contributions or [],
            technologies=record.technologies or [],
            achievements=record.achievements or [],
            measurable_impact=record.measurable_impact or [],
            source_evidence=record.source_evidence or [],
            extraction_confidence=record.extraction_confidence,
            is_manually_edited=record.is_manually_edited,
            manually_edited_fields=record.manually_edited_fields or [],
            created_at=record.created_at.isoformat() if record.created_at else None,
            updated_at=record.updated_at.isoformat() if record.updated_at else None,
        )

    async def extract_experience(
        self,
        resume_id: str,
        cleaned_text_override: Optional[str] = None,
        user_id: Optional[str] = None,
        reprocess: bool = False,
        force_overwrite: bool = False,
        db: Optional[Session] = None,
    ) -> List[ExperienceEntryData]:
        """
        Executes hybrid experience extraction pipeline and persists structured records.
        """
        parsed_resume_uuid = None
        existing_records: List[Experience] = []

        if db:
            try:
                parsed_resume_uuid = uuid.UUID(resume_id)
                existing_records = list(
                    db.execute(
                        select(Experience).where(Experience.resume_id == parsed_resume_uuid)
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

        # 2. Detect experience section
        section_text, is_explicit_section = detect_experience_section(cleaned_text)
        if not section_text or not section_text.strip():
            return []

        # 3. AI-Assisted extraction with fallback
        extracted_raw_entries = await experience_ai_extractor.extract_experience_entries(section_text)

        # 4. Fallback to deterministic rule-based extractor if AI fails or returns empty
        if not extracted_raw_entries:
            extracted_raw_entries = extract_deterministic_experience(section_text)

        processed_entries: List[Dict[str, Any]] = []

        # 5. Normalization, Validation, and Confidence Assessment
        for raw in extracted_raw_entries:
            norm_comp = normalize_company(raw.get("company"))
            norm_title = normalize_job_title(raw.get("job_title"))

            # Skip entries where both company and title are missing
            if not norm_comp and not norm_title:
                continue

            raw_start = raw.get("start_date")
            raw_end = raw.get("end_date")
            is_curr = bool(raw.get("is_current", False))

            norm_start = normalize_date_string(raw_start)
            norm_end = None if is_curr else normalize_date_string(raw_end)

            # Detect employment type
            raw_bullets = (raw.get("responsibilities") or []) + (raw.get("technical_contributions") or [])
            all_text = f"{norm_title or ''} {norm_comp or ''} {' '.join(raw_bullets)}"
            emp_type = detect_employment_type(
                job_title=norm_title,
                raw_text=all_text,
                explicit_type=raw.get("employment_type"),
            )

            # Categorize content
            categorized = categorize_experience_bullets(raw_bullets)

            # Technologies
            techs = raw.get("technologies") or []
            if not techs:
                techs = extract_technologies_from_text(all_text)
            else:
                # Merge with any detected from bullets
                inferred = extract_technologies_from_text(" ".join(raw_bullets))
                for inf in inferred:
                    if inf not in techs:
                        techs.append(inf)

            # Achievements and measurable impact
            raw_achievements = raw.get("achievements") or []
            raw_impact = raw.get("measurable_impact") or []
            for ach in categorized["achievements"]:
                if ach not in raw_achievements:
                    raw_achievements.append(ach)
            for imp in categorized["measurable_impact"]:
                if imp not in raw_impact:
                    raw_impact.append(imp)

            # Responsibilities & Technical contributions
            responsibilities = raw.get("responsibilities") or categorized["responsibilities"]
            technical_contributions = raw.get("technical_contributions") or categorized["technical_contributions"]

            # Calculate individual duration
            duration = calculate_individual_duration_months(
                start_date=norm_start,
                end_date=norm_end,
                is_current=is_curr,
            )

            entry_dict = {
                "company": norm_comp,
                "job_title": norm_title,
                "employment_type": emp_type,
                "location": raw.get("location"),
                "start_date": norm_start,
                "end_date": norm_end,
                "is_current": is_curr,
                "duration_months": duration,
                "responsibilities": responsibilities,
                "technical_contributions": technical_contributions,
                "technologies": techs,
                "achievements": raw_achievements,
                "measurable_impact": raw_impact,
                "source_evidence": raw.get("source_evidence") or [f"{norm_title or ''} at {norm_comp or ''}"],
            }

            entry_dict["extraction_confidence"] = compute_experience_confidence(
                entry_dict, is_explicit_section=is_explicit_section
            )
            processed_entries.append(entry_dict)

        # Sort entries chronologically descending (most recent first)
        def get_entry_sort_key(e):
            s_d = e.get("start_date")
            y, m = parse_date_to_parts(s_d)
            if y is None:
                return 0
            return date_to_absolute_month(y, m or 1)

        processed_entries.sort(key=get_entry_sort_key, reverse=True)

        # 6. Database Persistence
        if db and parsed_resume_uuid:
            resume_exists = db.execute(
                select(Resume).where(Resume.id == parsed_resume_uuid)
            ).scalar_one_or_none()

            if resume_exists:
                # If reprocessing, preserve manually edited records unless force_overwrite
                if existing_records:
                    if force_overwrite:
                        db.execute(delete(Experience).where(Experience.resume_id == parsed_resume_uuid))
                    else:
                        db.execute(
                            delete(Experience).where(
                                Experience.resume_id == parsed_resume_uuid,
                                Experience.is_manually_edited == False,  # noqa: E712
                            )
                        )
                    db.flush()

                # Insert new records
                created_models: List[Experience] = []
                for item in processed_entries:
                    new_rec = Experience(
                        resume_id=parsed_resume_uuid,
                        user_id=resume_exists.user_id,
                        company=item.get("company"),
                        job_title=item.get("job_title"),
                        employment_type=item.get("employment_type", "full_time"),
                        location=item.get("location"),
                        start_date=item.get("start_date"),
                        end_date=item.get("end_date"),
                        is_current=item.get("is_current", False),
                        duration_months=item.get("duration_months"),
                        responsibilities=item.get("responsibilities", []),
                        technical_contributions=item.get("technical_contributions", []),
                        technologies=item.get("technologies", []),
                        achievements=item.get("achievements", []),
                        measurable_impact=item.get("measurable_impact", []),
                        source_evidence=item.get("source_evidence", []),
                        extraction_confidence=item.get("extraction_confidence", 0.90),
                        is_manually_edited=False,
                        manually_edited_fields=[],
                    )
                    db.add(new_rec)
                    created_models.append(new_rec)

                db.commit()

                # Re-fetch all active records for resume (including preserved manual edits)
                db_records = list(
                    db.execute(
                        select(Experience)
                        .where(Experience.resume_id == parsed_resume_uuid)
                        .order_by(Experience.created_at)
                    ).scalars().all()
                )
                return [self._record_to_schema(r) for r in db_records]

        # In-memory staging persistence
        staged_schemas = [
            ExperienceEntryData(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                user_id=user_id,
                **item,
                is_manually_edited=False,
                manually_edited_fields=[],
            )
            for item in processed_entries
        ]
        self._staging_cache[resume_id] = staged_schemas
        return staged_schemas

    def get_experience(self, resume_id: str, db: Optional[Session] = None) -> List[ExperienceEntryData]:
        """Retrieves experience entries from database or staging cache."""
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                records = list(
                    db.execute(
                        select(Experience)
                        .where(Experience.resume_id == parsed_uuid)
                        .order_by(Experience.created_at)
                    ).scalars().all()
                )
                if records:
                    return [self._record_to_schema(r) for r in records]
            except ValueError:
                pass

        return self._staging_cache.get(resume_id, [])

    def get_experience_summary(
        self,
        resume_id: str,
        db: Optional[Session] = None,
    ) -> ExperienceSummaryData:
        """
        Calculates aggregate metrics, non-overlapping total duration, and summary observations.
        """
        entries = self.get_experience(resume_id, db)
        if not entries:
            return ExperienceSummaryData(
                total_experience_months=0,
                total_experience_years=0.0,
                employment_count=0,
                extraction_status="completed",
            )

        entries_dicts = [e.model_dump() for e in entries]

        # Calculate non-overlapping aggregate duration
        total_months = calculate_aggregate_experience_months(entries_dicts)
        total_years = round(total_months / 12.0, 1)

        # Count by employment types
        type_counts: Dict[str, int] = {}
        all_techs = []
        for e in entries:
            emp_t = e.employment_type or "full_time"
            type_counts[emp_t] = type_counts.get(emp_t, 0) + 1
            for tech in e.technologies:
                if tech not in all_techs:
                    all_techs.append(tech)

        # Most recent role
        most_recent = entries_dicts[0] if entries_dicts else None
        recent_summary = None
        if most_recent:
            recent_summary = {
                "company": most_recent.get("company"),
                "job_title": most_recent.get("job_title"),
                "employment_type": most_recent.get("employment_type"),
                "start_date": most_recent.get("start_date"),
                "end_date": most_recent.get("end_date"),
                "is_current": most_recent.get("is_current"),
            }

        progression_data = analyze_career_progression(entries_dicts)

        return ExperienceSummaryData(
            total_experience_months=total_months,
            total_experience_years=total_years,
            employment_count=len(entries),
            full_time_count=type_counts.get("full_time", 0),
            part_time_count=type_counts.get("part_time", 0),
            internship_count=type_counts.get("internship", 0),
            freelance_count=type_counts.get("freelance", 0),
            contract_count=type_counts.get("contract", 0),
            apprenticeship_count=type_counts.get("apprenticeship", 0),
            research_count=type_counts.get("research", 0),
            volunteer_count=type_counts.get("volunteer", 0),
            other_count=type_counts.get("other", 0),
            most_recent_role=recent_summary,
            identified_technologies=all_techs,
            career_progression_observations=progression_data.get("observations", []),
            extraction_status="completed",
        )

    def get_career_progression(
        self,
        resume_id: str,
        db: Optional[Session] = None,
    ) -> CareerProgressionResponse:
        """Retrieves chronological progression analysis, transitions, and employment gaps."""
        entries = self.get_experience(resume_id, db)
        entries_dicts = [e.model_dump() for e in entries]

        total_months = calculate_aggregate_experience_months(entries_dicts)
        analysis = analyze_career_progression(entries_dicts)

        timeline_items = [
            CareerProgressionItem(**item) for item in analysis.get("timeline", [])
        ]

        return CareerProgressionResponse(
            success=True,
            message="Career progression retrieved successfully",
            timeline=timeline_items,
            gaps=analysis.get("gaps", []),
            observations=analysis.get("observations", []),
            total_experience_months=total_months,
        )

    def add_experience_entry(
        self,
        resume_id: str,
        payload: ExperienceCreateRequest,
        db: Optional[Session] = None,
    ) -> Optional[ExperienceEntryData]:
        """Manually adds an experience record to a resume."""
        norm_comp = normalize_company(payload.company)
        norm_title = normalize_job_title(payload.job_title)
        norm_start = normalize_date_string(payload.start_date)
        norm_end = normalize_date_string(payload.end_date) if not payload.is_current else None

        duration = payload.duration_months
        if duration is None:
            duration = calculate_individual_duration_months(norm_start, norm_end, payload.is_current or False)

        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                resume = db.execute(select(Resume).where(Resume.id == parsed_uuid)).scalar_one_or_none()
                if not resume:
                    return None

                new_record = Experience(
                    resume_id=parsed_uuid,
                    user_id=resume.user_id,
                    company=norm_comp,
                    job_title=norm_title,
                    employment_type=payload.employment_type or "full_time",
                    location=payload.location,
                    start_date=norm_start,
                    end_date=norm_end,
                    is_current=payload.is_current or False,
                    duration_months=duration,
                    responsibilities=payload.responsibilities or [],
                    technical_contributions=payload.technical_contributions or [],
                    technologies=payload.technologies or [],
                    achievements=payload.achievements or [],
                    measurable_impact=payload.measurable_impact or [],
                    source_evidence=["Manually added by user"],
                    extraction_confidence=1.0,
                    is_manually_edited=True,
                    manually_edited_fields=["all"],
                )
                db.add(new_record)
                db.commit()
                db.refresh(new_record)
                return self._record_to_schema(new_record)
            except ValueError:
                pass

        # Staging fallback
        staged_entry = ExperienceEntryData(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            company=norm_comp,
            job_title=norm_title,
            employment_type=payload.employment_type or "full_time",
            location=payload.location,
            start_date=norm_start,
            end_date=norm_end,
            is_current=payload.is_current or False,
            duration_months=duration,
            responsibilities=payload.responsibilities or [],
            technical_contributions=payload.technical_contributions or [],
            technologies=payload.technologies or [],
            achievements=payload.achievements or [],
            measurable_impact=payload.measurable_impact or [],
            source_evidence=["Manually added by user"],
            extraction_confidence=1.0,
            is_manually_edited=True,
            manually_edited_fields=["all"],
        )
        if resume_id not in self._staging_cache:
            self._staging_cache[resume_id] = []
        self._staging_cache[resume_id].append(staged_entry)
        return staged_entry

    def update_experience_entry(
        self,
        resume_id: str,
        experience_id: str,
        payload: ExperienceUpdateRequest,
        db: Optional[Session] = None,
    ) -> Optional[ExperienceEntryData]:
        """Updates an existing experience record and marks it as user-edited."""
        if db:
            try:
                parsed_res_uuid = uuid.UUID(resume_id)
                parsed_exp_uuid = uuid.UUID(experience_id)
                record = db.execute(
                    select(Experience).where(
                        Experience.id == parsed_exp_uuid,
                        Experience.resume_id == parsed_res_uuid,
                    )
                ).scalar_one_or_none()

                if not record:
                    return None

                edited_fields = list(record.manually_edited_fields or [])

                if payload.company is not None:
                    record.company = normalize_company(payload.company)
                    if "company" not in edited_fields:
                        edited_fields.append("company")

                if payload.job_title is not None:
                    record.job_title = normalize_job_title(payload.job_title)
                    if "job_title" not in edited_fields:
                        edited_fields.append("job_title")

                if payload.employment_type is not None:
                    record.employment_type = payload.employment_type
                    if "employment_type" not in edited_fields:
                        edited_fields.append("employment_type")

                if payload.location is not None:
                    record.location = payload.location
                    if "location" not in edited_fields:
                        edited_fields.append("location")

                if payload.start_date is not None:
                    record.start_date = normalize_date_string(payload.start_date)
                    if "start_date" not in edited_fields:
                        edited_fields.append("start_date")

                if payload.is_current is not None:
                    record.is_current = payload.is_current
                    if payload.is_current:
                        record.end_date = None
                    if "is_current" not in edited_fields:
                        edited_fields.append("is_current")

                if payload.end_date is not None and not record.is_current:
                    record.end_date = normalize_date_string(payload.end_date)
                    if "end_date" not in edited_fields:
                        edited_fields.append("end_date")

                if payload.responsibilities is not None:
                    record.responsibilities = payload.responsibilities
                    if "responsibilities" not in edited_fields:
                        edited_fields.append("responsibilities")

                if payload.technical_contributions is not None:
                    record.technical_contributions = payload.technical_contributions
                    if "technical_contributions" not in edited_fields:
                        edited_fields.append("technical_contributions")

                if payload.technologies is not None:
                    record.technologies = payload.technologies
                    if "technologies" not in edited_fields:
                        edited_fields.append("technologies")

                if payload.achievements is not None:
                    record.achievements = payload.achievements
                    if "achievements" not in edited_fields:
                        edited_fields.append("achievements")

                if payload.measurable_impact is not None:
                    record.measurable_impact = payload.measurable_impact
                    if "measurable_impact" not in edited_fields:
                        edited_fields.append("measurable_impact")

                # Recalculate duration
                if payload.duration_months is not None:
                    record.duration_months = payload.duration_months
                else:
                    record.duration_months = calculate_individual_duration_months(
                        record.start_date, record.end_date, record.is_current
                    )

                record.is_manually_edited = True
                record.manually_edited_fields = edited_fields
                db.commit()
                db.refresh(record)
                return self._record_to_schema(record)
            except ValueError:
                pass

        # Staging fallback
        staged_list = self._staging_cache.get(resume_id, [])
        for entry in staged_list:
            if entry.id == experience_id:
                if payload.company is not None:
                    entry.company = normalize_company(payload.company)
                if payload.job_title is not None:
                    entry.job_title = normalize_job_title(payload.job_title)
                if payload.employment_type is not None:
                    entry.employment_type = payload.employment_type
                if payload.location is not None:
                    entry.location = payload.location
                if payload.start_date is not None:
                    entry.start_date = normalize_date_string(payload.start_date)
                if payload.is_current is not None:
                    entry.is_current = payload.is_current
                    if payload.is_current:
                        entry.end_date = None
                if payload.end_date is not None and not entry.is_current:
                    entry.end_date = normalize_date_string(payload.end_date)
                if payload.responsibilities is not None:
                    entry.responsibilities = payload.responsibilities
                if payload.technical_contributions is not None:
                    entry.technical_contributions = payload.technical_contributions
                if payload.technologies is not None:
                    entry.technologies = payload.technologies
                if payload.achievements is not None:
                    entry.achievements = payload.achievements
                if payload.measurable_impact is not None:
                    entry.measurable_impact = payload.measurable_impact
                entry.duration_months = calculate_individual_duration_months(
                    entry.start_date, entry.end_date, entry.is_current
                )
                entry.is_manually_edited = True
                return entry

        return None

    def delete_experience_entry(
        self,
        resume_id: str,
        experience_id: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Deletes an experience record from database or staging cache."""
        if db:
            try:
                parsed_res_uuid = uuid.UUID(resume_id)
                parsed_exp_uuid = uuid.UUID(experience_id)
                res = db.execute(
                    delete(Experience).where(
                        Experience.id == parsed_exp_uuid,
                        Experience.resume_id == parsed_res_uuid,
                    )
                )
                db.commit()
                if res.rowcount > 0:
                    return True
            except ValueError:
                pass

        # Staging fallback
        if resume_id in self._staging_cache:
            initial_len = len(self._staging_cache[resume_id])
            self._staging_cache[resume_id] = [
                e for e in self._staging_cache[resume_id] if e.id != experience_id
            ]
            return len(self._staging_cache[resume_id]) < initial_len

        return False


experience_service = ExperienceAnalysisService()
