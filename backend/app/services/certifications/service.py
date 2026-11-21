"""
Certifications and Achievements Orchestration Service
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Coordinates section detection, deterministic extraction, AI narrative parsing,
Feature #17 skill linking, Feature #18 project linking, deduplication, confidence scoring,
manual edit protection, and database persistence.
"""

import uuid
import logging
from typing import Optional, List, Dict, Any, Tuple, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.resume import Resume
from app.models.certifications import Certification, Achievement
from app.models.project import Project
from app.schemas.certifications import (
    CertificationEntryData,
    CertificationCreateRequest,
    CertificationUpdateRequest,
    CertificationSummaryData,
    CertificationSkillLinkData,
    AchievementEntryData,
    AchievementCreateRequest,
    AchievementUpdateRequest,
    AchievementSummaryData,
    CertificationsAchievementsCombinedSummary,
)
from app.services.preview_service import preview_service
from app.services.cleaning import cleaning_service
from app.services.storage import staging_service
from app.services.certifications.section_detector import (
    extract_certification_and_achievement_sections,
    split_section_into_blocks,
)
from app.services.certifications.deterministic_extractor import (
    extract_deterministic_certification,
    extract_deterministic_achievement,
)
from app.services.certifications.skill_linker import extract_skills_from_text
from app.services.certifications.project_linker import link_achievement_to_project
from app.services.certifications.confidence_scorer import (
    compute_certification_confidence,
    compute_achievement_confidence,
)
from app.services.certifications.deduplicator import (
    deduplicate_certifications,
    deduplicate_achievements,
)
from app.services.certifications.ai_extractor import certifications_ai_extractor

logger = logging.getLogger(__name__)


class CertificationsAchievementsService:
    """Manages extraction, persistence, editing, and analytics for certifications and achievements."""

    def __init__(self):
        # Staging cache for preview sessions prior to permanent save
        self._staging_certifications: Dict[str, List[CertificationEntryData]] = {}
        self._staging_achievements: Dict[str, List[AchievementEntryData]] = {}

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

    # =========================================================================
    # CERTIFICATIONS EXTRACTION & LIFECYCLE
    # =========================================================================

    async def extract_and_structure_certifications(
        self,
        resume_id: str,
        reprocess: bool = False,
        force_overwrite: bool = False,
        db: Optional[Session] = None,
    ) -> List[CertificationEntryData]:
        """Extracts, structures, validates, and stores candidate certification records."""
        # Check DB if not reprocessing
        existing_records: List[Certification] = []
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                stmt = select(Certification).where(Certification.resume_id == parsed_uuid).order_by(Certification.created_at)
                existing_records = list(db.execute(stmt).scalars().all())
                if existing_records and not reprocess:
                    return [self._cert_model_to_schema(c) for c in existing_records]
            except (ValueError, Exception) as exc:
                logger.warning("Error fetching existing resume certifications: %s", exc)

        # Check in-memory staging cache
        if resume_id in self._staging_certifications and not reprocess:
            return self._staging_certifications[resume_id]

        cleaned_text = self._resolve_cleaned_text(resume_id, db)
        if not cleaned_text:
            return []

        # Detect sections
        sections = extract_certification_and_achievement_sections(cleaned_text)
        cert_sections = sections.get("certifications", [])

        candidate_blocks: List[Tuple[str, str]] = []
        for sec in cert_sections:
            blocks = split_section_into_blocks(sec["text"])
            for b in blocks:
                candidate_blocks.append((b, sec["section_name"]))

        extracted_entries: List[Dict[str, Any]] = []
        for block, sec_name in candidate_blocks:
            cert_data = extract_deterministic_certification(block, sec_name)
            if not cert_data or not cert_data.get("certification_name"):
                continue

            # Link canonical skills
            linked_skills = extract_skills_from_text(block)
            cert_data["related_skills"] = linked_skills

            # Evidence-based confidence
            cert_data["confidence"] = compute_certification_confidence(cert_data)
            cert_data["extraction_method"] = "deterministic"
            extracted_entries.append(cert_data)

        # Deduplicate
        deduped = deduplicate_certifications(extracted_entries)

        # Map manual edits preservation
        manual_edits_map: Dict[str, Certification] = {}
        if existing_records and reprocess and not force_overwrite:
            for ex in existing_records:
                if ex.is_manually_edited:
                    manual_edits_map[ex.normalized_name.lower().strip()] = ex

        final_models: List[Certification] = []
        parsed_resume_uuid = None
        user_uuid = None

        if db:
            try:
                parsed_resume_uuid = uuid.UUID(resume_id)
                res_obj = db.execute(select(Resume).where(Resume.id == parsed_resume_uuid)).scalar_one_or_none()
                if res_obj:
                    user_uuid = res_obj.user_id
            except (ValueError, Exception):
                pass

        for d in deduped:
            name_key = d["normalized_name"].lower().strip()
            if name_key in manual_edits_map:
                final_models.append(manual_edits_map[name_key])
                continue

            skills_dicts = [
                s.model_dump() if hasattr(s, "model_dump") else s
                for s in d.get("related_skills", [])
            ]

            cert_model = Certification(
                id=uuid.uuid4(),
                resume_id=parsed_resume_uuid or uuid.uuid4(),
                user_id=user_uuid,
                certification_name=d["certification_name"],
                normalized_name=d["normalized_name"],
                issuing_organization=d.get("issuing_organization"),
                certification_category=d.get("certification_category", "other"),
                issue_date=d.get("issue_date"),
                expiry_date=d.get("expiry_date"),
                credential_id=d.get("credential_id"),
                credential_url=d.get("credential_url"),
                completion_status=d.get("completion_status", "completed"),
                related_skills=skills_dicts,
                source_section=d.get("source_section", "certifications"),
                source_evidence=d.get("source_evidence", []),
                confidence=d.get("confidence", 1.0),
                extraction_method=d.get("extraction_method", "hybrid"),
                review_status="pending",
                is_manually_edited=False,
                manually_edited_fields=[],
            )
            final_models.append(cert_model)

        # Add remaining protected manual edits
        for ex in manual_edits_map.values():
            if ex not in final_models:
                final_models.append(ex)

        if db and parsed_resume_uuid:
            try:
                db.execute(delete(Certification).where(Certification.resume_id == parsed_resume_uuid))
                for m in final_models:
                    db.add(m)
                db.commit()
                # Reload models
                stmt = select(Certification).where(Certification.resume_id == parsed_resume_uuid).order_by(Certification.created_at)
                reloaded = list(db.execute(stmt).scalars().all())
                return [self._cert_model_to_schema(m) for m in reloaded]
            except Exception as exc:
                db.rollback()
                logger.error("Failed to commit certifications: %s", exc)

        schemas = [self._cert_model_to_schema(m) for m in final_models]
        self._staging_certifications[resume_id] = schemas
        return schemas

    # =========================================================================
    # ACHIEVEMENTS EXTRACTION & LIFECYCLE
    # =========================================================================

    async def extract_and_structure_achievements(
        self,
        resume_id: str,
        reprocess: bool = False,
        force_overwrite: bool = False,
        db: Optional[Session] = None,
    ) -> List[AchievementEntryData]:
        """Extracts, structures, validates, and stores candidate accomplishment records."""
        # Check DB if not reprocessing
        existing_records: List[Achievement] = []
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                stmt = select(Achievement).where(Achievement.resume_id == parsed_uuid).order_by(Achievement.created_at)
                existing_records = list(db.execute(stmt).scalars().all())
                if existing_records and not reprocess:
                    return [self._achieve_model_to_schema(a, db) for a in existing_records]
            except (ValueError, Exception) as exc:
                logger.warning("Error fetching existing resume achievements: %s", exc)

        # Check in-memory staging cache
        if resume_id in self._staging_achievements and not reprocess:
            return self._staging_achievements[resume_id]

        cleaned_text = self._resolve_cleaned_text(resume_id, db)
        if not cleaned_text:
            return []

        # Detect sections
        sections = extract_certification_and_achievement_sections(cleaned_text)
        achieve_sections = sections.get("achievements", [])

        candidate_blocks: List[Tuple[str, str]] = []
        for sec in achieve_sections:
            blocks = split_section_into_blocks(sec["text"])
            for b in blocks:
                candidate_blocks.append((b, sec["section_name"]))

        extracted_entries: List[Dict[str, Any]] = []
        for block, sec_name in candidate_blocks:
            achieve_data = extract_deterministic_achievement(block, sec_name)
            if not achieve_data or not achieve_data.get("achievement_title"):
                continue

            # Link canonical skills
            linked_skills = extract_skills_from_text(block)
            achieve_data["related_skills"] = linked_skills

            # Link to project if mentioned
            proj_id, proj_title = link_achievement_to_project(block, resume_id, db)
            achieve_data["related_project_id"] = proj_id
            achieve_data["related_project_title"] = proj_title

            # Evidence-based confidence
            achieve_data["confidence"] = compute_achievement_confidence(achieve_data)
            achieve_data["extraction_method"] = "deterministic"
            extracted_entries.append(achieve_data)

        # Deduplicate
        deduped = deduplicate_achievements(extracted_entries)

        # Manual edits preservation
        manual_edits_map: Dict[str, Achievement] = {}
        if existing_records and reprocess and not force_overwrite:
            for ex in existing_records:
                if ex.is_manually_edited:
                    manual_edits_map[ex.normalized_title.lower().strip()] = ex

        final_models: List[Achievement] = []
        parsed_resume_uuid = None
        user_uuid = None

        if db:
            try:
                parsed_resume_uuid = uuid.UUID(resume_id)
                res_obj = db.execute(select(Resume).where(Resume.id == parsed_resume_uuid)).scalar_one_or_none()
                if res_obj:
                    user_uuid = res_obj.user_id
            except (ValueError, Exception):
                pass

        for d in deduped:
            title_key = d["normalized_title"].lower().strip()
            if title_key in manual_edits_map:
                final_models.append(manual_edits_map[title_key])
                continue

            skills_dicts = [
                s.model_dump() if hasattr(s, "model_dump") else s
                for s in d.get("related_skills", [])
            ]

            achieve_model = Achievement(
                id=uuid.uuid4(),
                resume_id=parsed_resume_uuid or uuid.uuid4(),
                user_id=user_uuid,
                achievement_title=d["achievement_title"],
                normalized_title=d["normalized_title"],
                achievement_category=d.get("achievement_category", "other"),
                event_name=d.get("event_name"),
                organization=d.get("organization"),
                achievement_type=d.get("achievement_type", "award"),
                rank_or_position=d.get("rank_or_position"),
                achievement_date=d.get("achievement_date"),
                description=d.get("description"),
                team_name=d.get("team_name"),
                team_size=d.get("team_size"),
                candidate_role=d.get("candidate_role"),
                related_project_id=d.get("related_project_id"),
                related_skills=skills_dicts,
                achievement_url=d.get("achievement_url"),
                source_section=d.get("source_section", "achievements"),
                source_evidence=d.get("source_evidence", []),
                confidence=d.get("confidence", 1.0),
                extraction_method=d.get("extraction_method", "hybrid"),
                review_status="pending",
                is_manually_edited=False,
                manually_edited_fields=[],
            )
            final_models.append(achieve_model)

        for ex in manual_edits_map.values():
            if ex not in final_models:
                final_models.append(ex)

        if db and parsed_resume_uuid:
            try:
                db.execute(delete(Achievement).where(Achievement.resume_id == parsed_resume_uuid))
                for m in final_models:
                    db.add(m)
                db.commit()
                stmt = select(Achievement).where(Achievement.resume_id == parsed_resume_uuid).order_by(Achievement.created_at)
                reloaded = list(db.execute(stmt).scalars().all())
                return [self._achieve_model_to_schema(m, db) for m in reloaded]
            except Exception as exc:
                db.rollback()
                logger.error("Failed to commit achievements: %s", exc)

        schemas = [self._achieve_model_to_schema(m, db) for m in final_models]
        self._staging_achievements[resume_id] = schemas
        return schemas

    # =========================================================================
    # CERTIFICATIONS CRUD & MANAGEMENT
    # =========================================================================

    def get_certifications(self, resume_id: str, db: Optional[Session] = None) -> List[CertificationEntryData]:
        """Retrieves structured certification records."""
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                stmt = select(Certification).where(Certification.resume_id == parsed_uuid).order_by(Certification.created_at)
                records = db.execute(stmt).scalars().all()
                if records:
                    return [self._cert_model_to_schema(c) for c in records]
            except (ValueError, Exception):
                pass
        return self._staging_certifications.get(resume_id, [])

    def get_certification_by_id(
        self, resume_id: str, cert_id: str, db: Optional[Session] = None
    ) -> Optional[CertificationEntryData]:
        """Finds certification by UUID."""
        all_certs = self.get_certifications(resume_id, db)
        for c in all_certs:
            if str(c.id) == cert_id:
                return c
        return None

    def add_certification_manually(
        self, resume_id: str, payload: CertificationCreateRequest, db: Optional[Session] = None
    ) -> CertificationEntryData:
        """Manually creates a new certification."""
        parsed_resume_uuid = None
        user_uuid = None
        if db:
            try:
                parsed_resume_uuid = uuid.UUID(resume_id)
                resume = db.execute(select(Resume).where(Resume.id == parsed_resume_uuid)).scalar_one_or_none()
                if resume:
                    user_uuid = resume.user_id
            except (ValueError, Exception):
                pass

        new_id = uuid.uuid4()
        norm_name = payload.normalized_name or payload.certification_name

        linked_skills = []
        if payload.related_skills:
            for s in payload.related_skills:
                linked_skills.append(s)
        else:
            found = extract_skills_from_text(payload.certification_name)
            linked_skills = [s.model_dump() for s in found]

        model = Certification(
            id=new_id,
            resume_id=parsed_resume_uuid or uuid.uuid4(),
            user_id=user_uuid,
            certification_name=payload.certification_name,
            normalized_name=norm_name,
            issuing_organization=payload.issuing_organization,
            certification_category=payload.certification_category or "other",
            issue_date=payload.issue_date,
            expiry_date=payload.expiry_date,
            credential_id=payload.credential_id,
            credential_url=str(payload.credential_url) if payload.credential_url else None,
            completion_status=payload.completion_status or "completed",
            related_skills=linked_skills,
            source_section=payload.source_section or "manual_entry",
            source_evidence=payload.source_evidence or ["User manual entry"],
            confidence=1.0,
            extraction_method="manual",
            review_status="confirmed",
            is_manually_edited=True,
            manually_edited_fields=["certification_name"],
        )

        if db and parsed_resume_uuid:
            db.add(model)
            db.commit()
            db.refresh(model)
            return self._cert_model_to_schema(model)

        schema = self._cert_model_to_schema(model)
        if resume_id not in self._staging_certifications:
            self._staging_certifications[resume_id] = []
        self._staging_certifications[resume_id].append(schema)
        return schema

    def update_certification_manually(
        self, resume_id: str, cert_id: str, payload: CertificationUpdateRequest, db: Optional[Session] = None
    ) -> Optional[CertificationEntryData]:
        """Updates fields of an existing certification and sets manual protection."""
        if db:
            try:
                cert_uuid = uuid.UUID(cert_id)
                model = db.execute(select(Certification).where(Certification.id == cert_uuid)).scalar_one_or_none()
                if model:
                    edited_fields = list(model.manually_edited_fields or [])
                    for field, val in payload.model_dump(exclude_unset=True).items():
                        if val is not None:
                            setattr(model, field, str(val) if field == "credential_url" and val else val)
                            if field not in edited_fields:
                                edited_fields.append(field)

                    model.is_manually_edited = True
                    model.manually_edited_fields = edited_fields
                    db.commit()
                    db.refresh(model)
                    return self._cert_model_to_schema(model)
            except (ValueError, Exception) as exc:
                logger.error("DB update error on certification: %s", exc)

        # Staging fallback
        if resume_id in self._staging_certifications:
            for idx, c in enumerate(self._staging_certifications[resume_id]):
                if str(c.id) == cert_id:
                    data = c.model_dump()
                    for field, val in payload.model_dump(exclude_unset=True).items():
                        if val is not None:
                            data[field] = str(val) if field == "credential_url" and val else val
                    data["is_manually_edited"] = True
                    updated_schema = CertificationEntryData(**data)
                    self._staging_certifications[resume_id][idx] = updated_schema
                    return updated_schema
        return None

    def confirm_certification(
        self, resume_id: str, cert_id: str, db: Optional[Session] = None
    ) -> Optional[CertificationEntryData]:
        """Confirms review status of certification."""
        patch = CertificationUpdateRequest(review_status="confirmed")
        return self.update_certification_manually(resume_id, cert_id, patch, db)

    def delete_certification(
        self, resume_id: str, cert_id: str, db: Optional[Session] = None
    ) -> bool:
        """Deletes certification record."""
        if db:
            try:
                cert_uuid = uuid.UUID(cert_id)
                model = db.execute(select(Certification).where(Certification.id == cert_uuid)).scalar_one_or_none()
                if model:
                    db.delete(model)
                    db.commit()
                    return True
            except (ValueError, Exception):
                pass

        if resume_id in self._staging_certifications:
            initial_len = len(self._staging_certifications[resume_id])
            self._staging_certifications[resume_id] = [
                c for c in self._staging_certifications[resume_id] if str(c.id) != cert_id
            ]
            return len(self._staging_certifications[resume_id]) < initial_len
        return False

    def get_certification_summary(
        self, resume_id: str, db: Optional[Session] = None
    ) -> CertificationSummaryData:
        """Calculates accurate aggregate analytics for certifications."""
        certs = self.get_certifications(resume_id, db)
        summary = CertificationSummaryData()
        summary.total_certifications = len(certs)

        cat_counts: Dict[str, int] = {}
        issuers: Set[str] = set()

        for c in certs:
            if c.completion_status == "completed":
                summary.completed_certifications += 1
            elif c.completion_status == "in_progress":
                summary.in_progress_certifications += 1
            elif c.completion_status == "expired":
                summary.expired_certifications += 1

            cat = c.certification_category or "other"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

            if c.issuing_organization:
                issuers.add(c.issuing_organization)

            if c.review_status == "pending" or c.review_status == "needs_review":
                summary.pending_reviews += 1

        summary.category_counts = cat_counts
        summary.unique_issuers = sorted(list(issuers))
        return summary

    # =========================================================================
    # ACHIEVEMENTS CRUD & MANAGEMENT
    # =========================================================================

    def get_achievements(self, resume_id: str, db: Optional[Session] = None) -> List[AchievementEntryData]:
        """Retrieves structured achievement records."""
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                stmt = select(Achievement).where(Achievement.resume_id == parsed_uuid).order_by(Achievement.created_at)
                records = db.execute(stmt).scalars().all()
                if records:
                    return [self._achieve_model_to_schema(a, db) for a in records]
            except (ValueError, Exception):
                pass
        return self._staging_achievements.get(resume_id, [])

    def get_achievement_by_id(
        self, resume_id: str, achieve_id: str, db: Optional[Session] = None
    ) -> Optional[AchievementEntryData]:
        """Finds achievement by UUID."""
        all_achieves = self.get_achievements(resume_id, db)
        for a in all_achieves:
            if str(a.id) == achieve_id:
                return a
        return None

    def add_achievement_manually(
        self, resume_id: str, payload: AchievementCreateRequest, db: Optional[Session] = None
    ) -> AchievementEntryData:
        """Manually creates a new achievement."""
        parsed_resume_uuid = None
        user_uuid = None
        if db:
            try:
                parsed_resume_uuid = uuid.UUID(resume_id)
                resume = db.execute(select(Resume).where(Resume.id == parsed_resume_uuid)).scalar_one_or_none()
                if resume:
                    user_uuid = resume.user_id
            except (ValueError, Exception):
                pass

        new_id = uuid.uuid4()
        norm_title = payload.normalized_title or payload.achievement_title

        linked_skills = []
        if payload.related_skills:
            for s in payload.related_skills:
                linked_skills.append(s)
        else:
            found = extract_skills_from_text(payload.achievement_title + " " + (payload.description or ""))
            linked_skills = [s.model_dump() for s in found]

        model = Achievement(
            id=new_id,
            resume_id=parsed_resume_uuid or uuid.uuid4(),
            user_id=user_uuid,
            achievement_title=payload.achievement_title,
            normalized_title=norm_title,
            achievement_category=payload.achievement_category or "other",
            event_name=payload.event_name,
            organization=payload.organization,
            achievement_type=payload.achievement_type or "award",
            rank_or_position=payload.rank_or_position,
            achievement_date=payload.achievement_date,
            description=payload.description,
            team_name=payload.team_name,
            team_size=payload.team_size,
            candidate_role=payload.candidate_role,
            related_project_id=payload.related_project_id,
            related_skills=linked_skills,
            achievement_url=str(payload.achievement_url) if payload.achievement_url else None,
            source_section=payload.source_section or "manual_entry",
            source_evidence=payload.source_evidence or ["User manual entry"],
            confidence=1.0,
            extraction_method="manual",
            review_status="confirmed",
            is_manually_edited=True,
            manually_edited_fields=["achievement_title"],
        )

        if db and parsed_resume_uuid:
            db.add(model)
            db.commit()
            db.refresh(model)
            return self._achieve_model_to_schema(model, db)

        schema = self._achieve_model_to_schema(model, db)
        if resume_id not in self._staging_achievements:
            self._staging_achievements[resume_id] = []
        self._staging_achievements[resume_id].append(schema)
        return schema

    def update_achievement_manually(
        self, resume_id: str, achieve_id: str, payload: AchievementUpdateRequest, db: Optional[Session] = None
    ) -> Optional[AchievementEntryData]:
        """Updates fields of an existing achievement and sets manual protection."""
        if db:
            try:
                achieve_uuid = uuid.UUID(achieve_id)
                model = db.execute(select(Achievement).where(Achievement.id == achieve_uuid)).scalar_one_or_none()
                if model:
                    edited_fields = list(model.manually_edited_fields or [])
                    for field, val in payload.model_dump(exclude_unset=True).items():
                        if val is not None:
                            setattr(model, field, str(val) if field == "achievement_url" and val else val)
                            if field not in edited_fields:
                                edited_fields.append(field)

                    model.is_manually_edited = True
                    model.manually_edited_fields = edited_fields
                    db.commit()
                    db.refresh(model)
                    return self._achieve_model_to_schema(model, db)
            except (ValueError, Exception) as exc:
                logger.error("DB update error on achievement: %s", exc)

        # Staging fallback
        if resume_id in self._staging_achievements:
            for idx, a in enumerate(self._staging_achievements[resume_id]):
                if str(a.id) == achieve_id:
                    data = a.model_dump()
                    for field, val in payload.model_dump(exclude_unset=True).items():
                        if val is not None:
                            data[field] = str(val) if field == "achievement_url" and val else val
                    data["is_manually_edited"] = True
                    updated_schema = AchievementEntryData(**data)
                    self._staging_achievements[resume_id][idx] = updated_schema
                    return updated_schema
        return None

    def confirm_achievement(
        self, resume_id: str, achieve_id: str, db: Optional[Session] = None
    ) -> Optional[AchievementEntryData]:
        """Confirms review status of achievement."""
        patch = AchievementUpdateRequest(review_status="confirmed")
        return self.update_achievement_manually(resume_id, achieve_id, patch, db)

    def delete_achievement(
        self, resume_id: str, achieve_id: str, db: Optional[Session] = None
    ) -> bool:
        """Deletes achievement record."""
        if db:
            try:
                achieve_uuid = uuid.UUID(achieve_id)
                model = db.execute(select(Achievement).where(Achievement.id == achieve_uuid)).scalar_one_or_none()
                if model:
                    db.delete(model)
                    db.commit()
                    return True
            except (ValueError, Exception):
                pass

        if resume_id in self._staging_achievements:
            initial_len = len(self._staging_achievements[resume_id])
            self._staging_achievements[resume_id] = [
                a for a in self._staging_achievements[resume_id] if str(a.id) != achieve_id
            ]
            return len(self._staging_achievements[resume_id]) < initial_len
        return False

    def get_achievement_summary(
        self, resume_id: str, db: Optional[Session] = None
    ) -> AchievementSummaryData:
        """Calculates accurate aggregate analytics for achievements."""
        achieves = self.get_achievements(resume_id, db)
        summary = AchievementSummaryData()
        summary.total_achievements = len(achieves)

        cat_counts: Dict[str, int] = {}

        for a in achieves:
            if a.achievement_type == "award":
                summary.total_awards += 1

            if a.achievement_category == "hackathon":
                summary.hackathon_awards += 1
            elif a.achievement_category == "competition":
                summary.competition_achievements += 1
            elif a.achievement_category == "publication":
                summary.publications += 1
            elif a.achievement_category == "scholarship":
                summary.scholarship_awards += 1

            cat = a.achievement_category or "other"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

            if a.related_project_id:
                summary.linked_projects_count += 1

            if a.review_status == "pending" or a.review_status == "needs_review":
                summary.pending_reviews += 1

        summary.category_counts = cat_counts
        return summary

    def get_combined_summary(
        self, resume_id: str, db: Optional[Session] = None
    ) -> CertificationsAchievementsCombinedSummary:
        """Returns comprehensive summary of both certifications and achievements."""
        cert_summary = self.get_certification_summary(resume_id, db)
        achieve_summary = self.get_achievement_summary(resume_id, db)
        total_records = cert_summary.total_certifications + achieve_summary.total_achievements
        total_pending = cert_summary.pending_reviews + achieve_summary.pending_reviews

        return CertificationsAchievementsCombinedSummary(
            certifications=cert_summary,
            achievements=achieve_summary,
            total_combined_records=total_records,
            total_pending_reviews=total_pending,
        )

    # =========================================================================
    # CONVERTER HELPERS
    # =========================================================================

    def _cert_model_to_schema(self, m: Certification) -> CertificationEntryData:
        raw_skills = m.related_skills or []
        skill_links = []
        for s in raw_skills:
            if isinstance(s, dict):
                skill_links.append(
                    CertificationSkillLinkData(
                        original_name=s.get("original_name", ""),
                        canonical_id=s.get("canonical_id"),
                        canonical_name=s.get("canonical_name", ""),
                        category=s.get("category", "Other"),
                        confidence=s.get("confidence", 1.0),
                        is_explicit=s.get("is_explicit", True),
                    )
                )
            elif hasattr(s, "canonical_name"):
                skill_links.append(s)

        return CertificationEntryData(
            id=m.id,
            resume_id=m.resume_id,
            user_id=m.user_id,
            certification_name=m.certification_name,
            normalized_name=m.normalized_name,
            issuing_organization=m.issuing_organization,
            certification_category=m.certification_category,
            issue_date=m.issue_date,
            expiry_date=m.expiry_date,
            credential_id=m.credential_id,
            credential_url=m.credential_url,
            completion_status=m.completion_status,
            related_skills=skill_links,
            source_section=m.source_section,
            source_evidence=m.source_evidence or [],
            confidence=m.confidence,
            extraction_method=m.extraction_method,
            review_status=m.review_status,
            is_manually_edited=m.is_manually_edited,
            manually_edited_fields=m.manually_edited_fields or [],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _achieve_model_to_schema(self, m: Achievement, db: Optional[Session] = None) -> AchievementEntryData:
        raw_skills = m.related_skills or []
        skill_links = []
        for s in raw_skills:
            if isinstance(s, dict):
                skill_links.append(
                    CertificationSkillLinkData(
                        original_name=s.get("original_name", ""),
                        canonical_id=s.get("canonical_id"),
                        canonical_name=s.get("canonical_name", ""),
                        category=s.get("category", "Other"),
                        confidence=s.get("confidence", 1.0),
                        is_explicit=s.get("is_explicit", True),
                    )
                )
            elif hasattr(s, "canonical_name"):
                skill_links.append(s)

        project_title = None
        if m.related_project_id and db:
            try:
                proj = db.execute(select(Project).where(Project.id == m.related_project_id)).scalar_one_or_none()
                if proj:
                    project_title = proj.project_title
            except Exception:
                pass

        return AchievementEntryData(
            id=m.id,
            resume_id=m.resume_id,
            user_id=m.user_id,
            achievement_title=m.achievement_title,
            normalized_title=m.normalized_title,
            achievement_category=m.achievement_category,
            event_name=m.event_name,
            organization=m.organization,
            achievement_type=m.achievement_type,
            rank_or_position=m.rank_or_position,
            achievement_date=m.achievement_date,
            description=m.description,
            team_name=m.team_name,
            team_size=m.team_size,
            candidate_role=m.candidate_role,
            related_project_id=m.related_project_id,
            related_project_title=project_title,
            related_skills=skill_links,
            achievement_url=m.achievement_url,
            source_section=m.source_section,
            source_evidence=m.source_evidence or [],
            confidence=m.confidence,
            extraction_method=m.extraction_method,
            review_status=m.review_status,
            is_manually_edited=m.is_manually_edited,
            manually_edited_fields=m.manually_edited_fields or [],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


certifications_achievements_service = CertificationsAchievementsService()
