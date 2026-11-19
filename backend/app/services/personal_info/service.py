"""
Personal Information Extraction Orchestration Service
Phase 3 | Feature 13: Personal Information Extraction
Coordinates deterministic rules, AI extraction, fallback heuristics, normalization, validation, and database persistence.
"""

import uuid
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.resume import Resume, ResumeVersion
from app.models.personal_information import ResumePersonalInformation
from app.schemas.personal_information import (
    PersonalInformationData,
    PersonalInformationUpdateRequest,
    LocationData,
)
from app.services.preview_service import preview_service
from app.services.cleaning import cleaning_service
from app.services.storage import staging_service
from app.services.personal_info.deterministic_extractor import extract_deterministic_info
from app.services.personal_info.ai_extractor import ai_extractor
from app.services.personal_info.fallback_extractor import (
    extract_fallback_name,
    extract_fallback_location,
)
from app.services.personal_info.normalizer import (
    normalize_name,
    normalize_email,
    normalize_phone,
    normalize_country_code,
    normalize_url,
    normalize_urls_list,
    normalize_location,
)
from app.services.personal_info.validator import (
    validate_email,
    validate_phone,
    validate_country_code,
    validate_name,
    validate_url,
    validate_urls_list,
    validate_location,
)
from app.services.personal_info.confidence_scorer import compute_confidence_scores

logger = logging.getLogger(__name__)


class PersonalInfoExtractionService:
    """Manages end-to-end extraction and lifecycle for candidate personal information."""

    def __init__(self):
        # In-memory staging cache for preview sessions prior to permanent save
        self._staging_cache: Dict[str, PersonalInformationData] = {}

    def _resolve_cleaned_text(self, resume_id: str, db: Optional[Session] = None) -> Optional[str]:
        """
        Retrieves cleaned resume text from database version, preview cache, or staging.
        """
        # 1. Try DB lookup if resume_id is a valid UUID
        if db:
            try:
                parsed_id = uuid.UUID(resume_id)
                resume = db.execute(select(Resume).where(Resume.id == parsed_id)).scalar_one_or_none()
                if resume and resume.versions:
                    # Latest version has cleaned text
                    latest = resume.versions[0]
                    if latest.cleaned_text:
                        return latest.cleaned_text
            except (ValueError, Exception):
                pass

        # 2. Try preview service cache
        try:
            preview_data = preview_service.get_preview(resume_id)
            if preview_data and preview_data.cleaned_text:
                return preview_data.cleaned_text
        except Exception:
            pass

        # 3. Try staging file clean
        try:
            staged_path = staging_service.get_staged_path(resume_id)
            if staged_path and staged_path.exists():
                clean_res = cleaning_service.clean_text(
                    raw_text="",
                    resume_id=resume_id,
                )
                if clean_res and clean_res.cleaned_text:
                    return clean_res.cleaned_text
        except Exception:
            pass

        return None

    async def extract_personal_information(
        self,
        resume_id: str,
        cleaned_text_override: Optional[str] = None,
        user_id: Optional[str] = None,
        reprocess: bool = False,
        force_overwrite: bool = False,
        db: Optional[Session] = None,
    ) -> PersonalInformationData:
        """
        Executes hybrid personal information extraction pipeline and persists results.
        """
        # Check if already processed and not reprocessing
        existing_record = None
        parsed_resume_uuid = None
        if db:
            try:
                parsed_resume_uuid = uuid.UUID(resume_id)
                existing_record = db.execute(
                    select(ResumePersonalInformation).where(
                        ResumePersonalInformation.resume_id == parsed_resume_uuid
                    )
                ).scalar_one_or_none()
            except ValueError:
                pass

        if existing_record and not reprocess:
            return self._record_to_schema(existing_record)

        # Also check staging cache if no DB record
        if not existing_record and resume_id in self._staging_cache and not reprocess:
            return self._staging_cache[resume_id]

        # 1. Retrieve cleaned text
        cleaned_text = cleaned_text_override or self._resolve_cleaned_text(resume_id, db)
        if not cleaned_text or not cleaned_text.strip():
            # Handle empty document safely without hallucinating
            empty_data = PersonalInformationData(
                resume_id=resume_id,
                user_id=user_id,
                full_name=None,
                first_name=None,
                last_name=None,
                email=None,
                phone=None,
                country_code=None,
                location=None,
                linkedin_url=None,
                github_url=None,
                portfolio_url=None,
                other_urls=[],
                extraction_status="completed",
                confidence={
                    "full_name": 0.0,
                    "email": 0.0,
                    "phone": 0.0,
                    "location": 0.0,
                },
                is_manually_edited=False,
            )
            return empty_data

        # 2. Deterministic extraction (email, phone, country code, URLs)
        det_info = extract_deterministic_info(cleaned_text)

        # 3. AI-Assisted extraction (name, location) with fallback
        ai_info = await ai_extractor.extract_identity_and_location(cleaned_text)

        source_attribution: Dict[str, str] = {
            "email": "deterministic",
            "phone": "deterministic",
            "country_code": "deterministic",
            "linkedin_url": "deterministic",
            "github_url": "deterministic",
            "portfolio_url": "deterministic",
        }

        full_name = None
        first_name = None
        last_name = None
        location_raw = None

        if ai_info and isinstance(ai_info, dict):
            full_name = ai_info.get("full_name")
            first_name = ai_info.get("first_name")
            last_name = ai_info.get("last_name")
            location_raw = ai_info.get("location")
            if full_name:
                source_attribution["full_name"] = "ai"
            if location_raw:
                source_attribution["location"] = "ai"

        # 4. Fallback heuristic for name/location if AI did not find them or is offline
        if not full_name:
            fb_full, fb_first, fb_last = extract_fallback_name(cleaned_text)
            full_name = fb_full
            first_name = fb_first
            last_name = fb_last
            if full_name:
                source_attribution["full_name"] = "heuristic"

        if not location_raw:
            fb_loc = extract_fallback_location(cleaned_text)
            if fb_loc:
                location_raw = fb_loc
                source_attribution["location"] = "heuristic"

        # 5. Normalization
        norm_full_name = normalize_name(full_name)
        norm_first_name = normalize_name(first_name)
        norm_last_name = normalize_name(last_name)
        norm_email = normalize_email(det_info.get("email"))
        norm_phone = normalize_phone(det_info.get("phone"))
        norm_country_code = normalize_country_code(det_info.get("country_code"))
        norm_linkedin = normalize_url(det_info.get("linkedin_url"))
        norm_github = normalize_url(det_info.get("github_url"))
        norm_portfolio = normalize_url(det_info.get("portfolio_url"))
        norm_other_urls = normalize_urls_list(det_info.get("other_urls"))
        norm_location = normalize_location(location_raw)

        # 6. Validation
        valid_full_name = validate_name(norm_full_name)
        valid_first_name = validate_name(norm_first_name)
        valid_last_name = validate_name(norm_last_name)
        valid_email = validate_email(norm_email)
        valid_phone = validate_phone(norm_phone)
        valid_country_code = validate_country_code(norm_country_code)
        valid_linkedin = validate_url(norm_linkedin)
        valid_github = validate_url(norm_github)
        valid_portfolio = validate_url(norm_portfolio)
        valid_other_urls = validate_urls_list(norm_other_urls)
        valid_location = validate_location(norm_location)

        # 7. Confidence scoring
        interim_data = {
            "full_name": valid_full_name,
            "first_name": valid_first_name,
            "last_name": valid_last_name,
            "email": valid_email,
            "phone": valid_phone,
            "country_code": valid_country_code,
            "location": valid_location,
            "linkedin_url": valid_linkedin,
            "github_url": valid_github,
            "portfolio_url": valid_portfolio,
            "other_urls": valid_other_urls,
        }
        confidence_scores = compute_confidence_scores(interim_data, source_attribution)

        loc_model = LocationData(**valid_location) if valid_location else None

        # 8. Database Persistence / Updates
        if db and parsed_resume_uuid:
            if existing_record:
                # Protect manually edited fields if not force_overwrite
                edited_fields = set(existing_record.manually_edited_fields or [])
                if existing_record.is_manually_edited and not force_overwrite:
                    if "full_name" not in edited_fields:
                        existing_record.full_name = valid_full_name
                        existing_record.first_name = valid_first_name
                        existing_record.last_name = valid_last_name
                    if "email" not in edited_fields:
                        existing_record.email = valid_email
                    if "phone" not in edited_fields:
                        existing_record.phone = valid_phone
                    if "country_code" not in edited_fields:
                        existing_record.country_code = valid_country_code
                    if "location" not in edited_fields:
                        existing_record.location = valid_location
                    if "linkedin_url" not in edited_fields:
                        existing_record.linkedin_url = valid_linkedin
                    if "github_url" not in edited_fields:
                        existing_record.github_url = valid_github
                    if "portfolio_url" not in edited_fields:
                        existing_record.portfolio_url = valid_portfolio
                    if "other_urls" not in edited_fields:
                        existing_record.other_urls = valid_other_urls
                else:
                    existing_record.full_name = valid_full_name
                    existing_record.first_name = valid_first_name
                    existing_record.last_name = valid_last_name
                    existing_record.email = valid_email
                    existing_record.phone = valid_phone
                    existing_record.country_code = valid_country_code
                    existing_record.location = valid_location
                    existing_record.linkedin_url = valid_linkedin
                    existing_record.github_url = valid_github
                    existing_record.portfolio_url = valid_portfolio
                    existing_record.other_urls = valid_other_urls
                    if force_overwrite:
                        existing_record.is_manually_edited = False
                        existing_record.manually_edited_fields = []

                existing_record.confidence = confidence_scores
                existing_record.extraction_status = "completed"
                db.commit()
                db.refresh(existing_record)
                return self._record_to_schema(existing_record)
            else:
                # Check if resume exists in DB before inserting
                resume_exists = db.execute(
                    select(Resume).where(Resume.id == parsed_resume_uuid)
                ).scalar_one_or_none()

                if resume_exists:
                    new_record = ResumePersonalInformation(
                        resume_id=parsed_resume_uuid,
                        user_id=resume_exists.user_id,
                        full_name=valid_full_name,
                        first_name=valid_first_name,
                        last_name=valid_last_name,
                        email=valid_email,
                        phone=valid_phone,
                        country_code=valid_country_code,
                        location=valid_location,
                        linkedin_url=valid_linkedin,
                        github_url=valid_github,
                        portfolio_url=valid_portfolio,
                        other_urls=valid_other_urls,
                        extraction_status="completed",
                        confidence=confidence_scores,
                        is_manually_edited=False,
                        manually_edited_fields=[],
                    )
                    db.add(new_record)
                    db.commit()
                    db.refresh(new_record)
                    return self._record_to_schema(new_record)

        # Staging cache fallback if not permanently stored in DB
        result_payload = PersonalInformationData(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            user_id=user_id,
            full_name=valid_full_name,
            first_name=valid_first_name,
            last_name=valid_last_name,
            email=valid_email,
            phone=valid_phone,
            country_code=valid_country_code,
            location=loc_model,
            linkedin_url=valid_linkedin,
            github_url=valid_github,
            portfolio_url=valid_portfolio,
            other_urls=valid_other_urls,
            extraction_status="completed",
            confidence=confidence_scores,
            is_manually_edited=False,
            manually_edited_fields=[],
        )
        self._staging_cache[resume_id] = result_payload
        return result_payload

    def get_personal_information(
        self, resume_id: str, db: Session
    ) -> Optional[PersonalInformationData]:
        """Retrieves stored personal information for a resume."""
        try:
            parsed_id = uuid.UUID(resume_id)
            record = db.execute(
                select(ResumePersonalInformation).where(
                    ResumePersonalInformation.resume_id == parsed_id
                )
            ).scalar_one_or_none()
            if record:
                return self._record_to_schema(record)
        except ValueError:
            pass

        # Check staging cache
        if resume_id in self._staging_cache:
            return self._staging_cache[resume_id]

        return None

    def update_personal_information(
        self,
        resume_id: str,
        update_data: PersonalInformationUpdateRequest,
        db: Session,
    ) -> Optional[PersonalInformationData]:
        """
        Manually updates candidate personal info, preserving edits against future reprocess runs.
        """
        try:
            parsed_id = uuid.UUID(resume_id)
        except ValueError:
            return None

        record = db.execute(
            select(ResumePersonalInformation).where(
                ResumePersonalInformation.resume_id == parsed_id
            )
        ).scalar_one_or_none()

        if not record:
            return None

        edited_fields = list(record.manually_edited_fields or [])
        conf = dict(record.confidence or {})

        # Apply provided updates
        update_dict = update_data.model_dump(exclude_unset=True)

        for field_name, value in update_dict.items():
            if field_name == "location":
                if value is not None:
                    loc_val = validate_location(normalize_location(value))
                    record.location = loc_val
                    conf["location"] = 1.0
                else:
                    record.location = None
                    conf["location"] = 0.0
                if "location" not in edited_fields:
                    edited_fields.append("location")

            elif field_name == "other_urls":
                if value is not None:
                    record.other_urls = validate_urls_list(normalize_urls_list(value))
                else:
                    record.other_urls = []
                if "other_urls" not in edited_fields:
                    edited_fields.append("other_urls")

            elif hasattr(record, field_name):
                # Normalize & validate string fields
                if field_name == "email":
                    val = validate_email(normalize_email(value))
                    record.email = val
                    conf["email"] = 1.0 if val else 0.0
                elif field_name == "phone":
                    val = validate_phone(normalize_phone(value))
                    record.phone = val
                    conf["phone"] = 1.0 if val else 0.0
                elif field_name == "country_code":
                    val = validate_country_code(normalize_country_code(value))
                    record.country_code = val
                    conf["country_code"] = 1.0 if val else 0.0
                elif field_name in ("linkedin_url", "github_url", "portfolio_url"):
                    val = validate_url(normalize_url(value))
                    setattr(record, field_name, val)
                    conf[field_name] = 1.0 if val else 0.0
                elif field_name in ("full_name", "first_name", "last_name"):
                    val = validate_name(normalize_name(value))
                    setattr(record, field_name, val)
                    conf[field_name] = 1.0 if val else 0.0

                if field_name not in edited_fields:
                    edited_fields.append(field_name)

        record.is_manually_edited = True
        record.manually_edited_fields = edited_fields
        record.confidence = conf

        db.commit()
        db.refresh(record)
        return self._record_to_schema(record)

    def _record_to_schema(self, record: ResumePersonalInformation) -> PersonalInformationData:
        """Converts SQLAlchemy model to Pydantic schema."""
        loc = None
        if record.location and isinstance(record.location, dict):
            loc = LocationData(**record.location)

        return PersonalInformationData(
            id=str(record.id),
            resume_id=str(record.resume_id),
            user_id=str(record.user_id) if record.user_id else None,
            full_name=record.full_name,
            first_name=record.first_name,
            last_name=record.last_name,
            email=record.email,
            phone=record.phone,
            country_code=record.country_code,
            location=loc,
            linkedin_url=record.linkedin_url,
            github_url=record.github_url,
            portfolio_url=record.portfolio_url,
            other_urls=record.other_urls or [],
            extraction_status=record.extraction_status,
            confidence=record.confidence or {},
            is_manually_edited=record.is_manually_edited,
            manually_edited_fields=record.manually_edited_fields or [],
            created_at=record.created_at.isoformat() if record.created_at else None,
            updated_at=record.updated_at.isoformat() if record.updated_at else None,
        )


personal_info_service = PersonalInfoExtractionService()
