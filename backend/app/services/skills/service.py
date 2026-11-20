"""
Skill Normalization Service
Phase 3 | Feature 17: Skill Normalization
Coordinates extraction, format normalization, dictionary alias matching, contextual resolution,
false-merge prevention, duplicate consolidation, AI disambiguation, and database persistence.
"""

import uuid
import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.resume import Resume, ResumeVersion
from app.models.skills import Skill, SkillAlias, ResumeSkill
from app.schemas.skills import (
    SkillEntryData,
    SkillSummaryData,
    SkillManualUpdateRequest,
)
from app.services.preview_service import preview_service
from app.services.cleaning import cleaning_service
from app.services.storage import staging_service
from app.services.skills.formatter import normalize_skill_text, create_lookup_key
from app.services.skills.false_merge_guard import are_distinct_technologies, validate_canonical_assignment
from app.services.skills.context_matcher import disambiguate_token
from app.services.skills.dictionary import skill_dictionary, DICTIONARY_VERSION
from app.services.skills.ai_extractor import skill_ai_extractor
from app.services.skills.consolidator import consolidate_normalized_skills

logger = logging.getLogger(__name__)

SKILL_SECTION_HEADERS = [
    r"(?:technical\s+skills|core\s+skills|skills\s*(?:&|and)\s*competencies|technical\s+proficiencies)",
    r"(?:skills\s*(?:&|and)\s*abilities|professional\s+skills|key\s+skills|skills)",
    r"(?:technologies\s*(?:&|and)\s*tools|technology\s+stack|tech\s+stack|tools\s*(?:&|and)\s*technologies)",
    r"(?:programming\s+languages|competencies|areas\s+of\s+expertise)",
]


class SkillNormalizationService:
    """Core domain service for skill normalization, extraction, and management."""

    def __init__(self):
        # In-memory staging cache for preview sessions prior to permanent save
        self._staging_cache: Dict[str, List[SkillEntryData]] = {}

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

    def _extract_raw_skill_candidates(self, resume_text: str) -> List[Dict[str, Any]]:
        """
        Extracts raw candidate skill tokens from resume text across dedicated skill sections
        and contextual mentions in experience/education.
        Returns list of dicts: {'raw_name': str, 'section': str, 'evidence': str}
        """
        candidates: List[Dict[str, Any]] = []
        if not resume_text:
            return candidates

        lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
        current_section = "general"

        for line in lines:
            line_lower = line.lower()
            # Detect section transitions
            is_header = False
            for pat in SKILL_SECTION_HEADERS:
                if re.match(rf"^(?:#+\s*)?{pat}[:\s]*$", line_lower):
                    current_section = "skills"
                    is_header = True
                    break
            if not is_header:
                if any(re.match(rf"^(?:#+\s*)?{kw}[:\s]*$", line_lower) for kw in (
                    "experience", "work experience", "employment", "professional experience"
                )):
                    current_section = "experience"
                    is_header = True
                elif any(re.match(rf"^(?:#+\s*)?{kw}[:\s]*$", line_lower) for kw in (
                    "education", "academic", "qualifications"
                )):
                    current_section = "education"
                    is_header = True
                elif any(re.match(rf"^(?:#+\s*)?{kw}[:\s]*$", line_lower) for kw in (
                    "projects", "personal projects", "academic projects"
                )):
                    current_section = "projects"
                    is_header = True
                elif any(re.match(rf"^(?:#+\s*)?{kw}[:\s]*$", line_lower) for kw in (
                    "certifications", "certificates", "licenses"
                )):
                    current_section = "certifications"
                    is_header = True

            if is_header:
                continue

            # In skill sections, tokenize by commas, semicolons, bullets, slashes, or pipes
            if current_section == "skills":
                # Check for category prefixes like "Languages: Python, JS" or "Frameworks: React"
                content_line = line
                colon_idx = line.find(":")
                if colon_idx != -1 and colon_idx < 30:
                    content_line = line[colon_idx + 1:].strip()

                tokens = re.split(r"[,;•|/]\s*", content_line)
                for tok in tokens:
                    tok_clean = normalize_skill_text(tok)
                    if tok_clean and len(tok_clean) <= 50 and not re.match(r"^\d+$", tok_clean):
                        candidates.append({
                            "raw_name": tok_clean,
                            "section": "skills",
                            "evidence": line[:200],
                        })
            else:
                # Scan line for known taxonomy words or bullet skill mentions
                words = re.findall(r"\b[A-Za-z0-9\+#\.-]{2,30}\b", line)
                for w in words:
                    match = skill_dictionary.lookup(w)
                    if match:
                        candidates.append({
                            "raw_name": w,
                            "section": current_section,
                            "evidence": line[:200],
                        })

        return candidates

    def normalize_single_skill(
        self,
        raw_name: str,
        section_name: str = "skills",
        evidence_snippet: str = "",
        surrounding_skills: Optional[List[str]] = None,
    ) -> SkillEntryData:
        """
        Normalizes a single skill string through the 5-layer pipeline.
        """
        clean_text = normalize_skill_text(raw_name)
        if not clean_text:
            return SkillEntryData(
                original_name=raw_name or "Unknown",
                canonical_name="Unknown",
                category="Other",
                skill_type="technical",
                normalization_method="unknown",
                confidence_score=0.0,
                normalization_status="rejected",
                source_sections=[section_name],
                source_evidence=[evidence_snippet] if evidence_snippet else [],
            )

        # 1. Check ambiguous tokens first (e.g. "R", "Go", "C", "Word")
        ambig_canon, ambig_cat, ambig_conf, ambig_status = disambiguate_token(
            raw_token=clean_text,
            section_name=section_name,
            context_text=evidence_snippet,
            surrounding_skills=surrounding_skills,
        )
        if ambig_canon is not None:
            method = "contextual_match" if ambig_status == "normalized" else "format_normalization"
            return SkillEntryData(
                original_name=clean_text,
                canonical_name=ambig_canon,
                category=ambig_cat or "Programming Languages",
                skill_type="technical",
                normalization_method=method,
                confidence_score=ambig_conf,
                normalization_status=ambig_status,
                source_sections=[section_name],
                source_evidence=[evidence_snippet] if evidence_snippet else [],
                aliases_detected=[clean_text] if clean_text.lower() != ambig_canon.lower() else [],
                dictionary_version=DICTIONARY_VERSION,
            )

        # 2. Exact Canonical & Alias Dictionary Lookup
        dict_match = skill_dictionary.lookup(clean_text)
        if dict_match:
            spec, match_method, conf = dict_match
            canonical_name = spec["name"]

            # Guard against false merge
            if not validate_canonical_assignment(clean_text, canonical_name):
                # Reject illegal false merge, preserve original
                return SkillEntryData(
                    original_name=clean_text,
                    canonical_name=clean_text,
                    category=spec.get("category", "Other"),
                    skill_type=spec.get("skill_type", "technical"),
                    normalization_method="unknown",
                    confidence_score=0.4,
                    normalization_status="pending_review",
                    source_sections=[section_name],
                    source_evidence=[evidence_snippet] if evidence_snippet else [],
                    dictionary_version=DICTIONARY_VERSION,
                )

            aliases_found = [clean_text] if clean_text.lower() != canonical_name.lower() else []
            return SkillEntryData(
                skill_id=spec.get("id"),
                original_name=clean_text,
                canonical_name=canonical_name,
                category=spec["category"],
                skill_type=spec.get("skill_type", "technical"),
                normalization_method=match_method,
                confidence_score=conf,
                normalization_status="normalized",
                source_sections=[section_name],
                source_evidence=[evidence_snippet] if evidence_snippet else [],
                aliases_detected=aliases_found,
                dictionary_version=DICTIONARY_VERSION,
            )

        # 3. Unrecognized Skill: preserve original name, mark as pending review or unknown
        return SkillEntryData(
            original_name=clean_text,
            canonical_name=clean_text,
            category="Other",
            skill_type="technical",
            normalization_method="unknown",
            confidence_score=0.5,
            normalization_status="pending_review",
            source_sections=[section_name],
            source_evidence=[evidence_snippet] if evidence_snippet else [],
            aliases_detected=[],
            dictionary_version=DICTIONARY_VERSION,
        )

    async def normalize_skill_list(
        self,
        raw_skills: List[str],
        context_text: Optional[str] = None,
    ) -> List[SkillEntryData]:
        """
        Normalizes a provided list of raw skill strings, consolidating duplicates and invoking AI if needed.
        """
        surrounding = [normalize_skill_text(s) for s in raw_skills if s]
        preliminary_entries: List[SkillEntryData] = []
        unresolved: List[str] = []

        for raw in raw_skills:
            if not raw or not raw.strip():
                continue
            entry = self.normalize_single_skill(
                raw_name=raw,
                section_name="skills",
                evidence_snippet=context_text or "",
                surrounding_skills=surrounding,
            )
            if entry.normalization_method == "unknown":
                unresolved.append(raw)
            preliminary_entries.append(entry)

        # If any unresolved, attempt AI suggestion via Ollama
        if unresolved:
            ai_suggestions = await skill_ai_extractor.suggest_canonical_mappings(
                unresolved_skills=unresolved,
                context_text=context_text,
            )
            if ai_suggestions:
                # Update preliminary entries with AI suggestions
                suggestion_map = {
                    s["original_name"].strip().lower(): s for s in ai_suggestions if "original_name" in s
                }
                for entry in preliminary_entries:
                    key = entry.original_name.strip().lower()
                    if key in suggestion_map:
                        sug = suggestion_map[key]
                        if sug.get("is_known") and sug.get("canonical_name"):
                            canon = sug["canonical_name"]
                            if validate_canonical_assignment(entry.original_name, canon):
                                entry.canonical_name = canon
                                entry.category = sug.get("category", entry.category)
                                entry.skill_type = sug.get("skill_type", entry.skill_type)
                                entry.normalization_method = "semantic_suggestion"
                                entry.confidence_score = float(sug.get("confidence", 0.7))
                                entry.normalization_status = "pending_review"  # AI suggestions require user review
                                if entry.original_name.lower() != canon.lower():
                                    entry.aliases_detected.append(entry.original_name)

        # Consolidate duplicate records across list
        return consolidate_normalized_skills(preliminary_entries)

    async def extract_and_normalize_skills(
        self,
        resume_id: str,
        reprocess: bool = False,
        force_overwrite: bool = False,
        db: Optional[Session] = None,
    ) -> List[SkillEntryData]:
        """
        Extracts candidate skills from resume, normalizes them, consolidates duplicates,
        preserves manual user edits, and stores records in database / staging cache.
        """
        # Sync DB dictionary if db available
        if db:
            skill_dictionary.sync_from_db(db)

        # 1. Check existing records in DB if not reprocessing
        existing_records: List[ResumeSkill] = []
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                stmt = select(ResumeSkill).where(ResumeSkill.resume_id == parsed_uuid)
                existing_records = list(db.execute(stmt).scalars().all())
                if existing_records and not reprocess:
                    return [
                        SkillEntryData(
                            id=str(r.id),
                            resume_id=str(r.resume_id),
                            skill_id=str(r.skill_id) if r.skill_id else None,
                            original_name=r.original_name,
                            canonical_name=r.canonical_name,
                            category=r.category,
                            skill_type=r.skill_type,
                            normalization_method=r.normalization_method,
                            confidence_score=r.confidence_score,
                            normalization_status=r.normalization_status,
                            source_sections=r.source_sections or [],
                            source_evidence=r.source_evidence or [],
                            aliases_detected=r.aliases_detected or [],
                            occurrence_count=r.occurrence_count or 1,
                            is_manually_edited=r.is_manually_edited,
                            manually_edited_fields=r.manually_edited_fields or [],
                            dictionary_version=r.dictionary_version,
                        )
                        for r in existing_records
                    ]
            except (ValueError, Exception) as exc:
                logger.warning("Error fetching existing resume skills: %s", exc)

        # Check in-memory staging cache if no DB records
        if resume_id in self._staging_cache and not reprocess:
            return self._staging_cache[resume_id]

        # 2. Resolve resume cleaned text
        cleaned_text = self._resolve_cleaned_text(resume_id, db)
        if not cleaned_text:
            return []

        # 3. Extract raw candidate mentions
        candidates = self._extract_raw_skill_candidates(cleaned_text)
        if not candidates:
            return []

        surrounding = [c["raw_name"] for c in candidates]
        preliminary: List[SkillEntryData] = []
        unresolved: List[str] = []

        for cand in candidates:
            entry = self.normalize_single_skill(
                raw_name=cand["raw_name"],
                section_name=cand["section"],
                evidence_snippet=cand["evidence"],
                surrounding_skills=surrounding,
            )
            if entry.normalization_method == "unknown":
                unresolved.append(cand["raw_name"])
            preliminary.append(entry)

        # 4. Local Ollama AI Disambiguation for unresolved skills
        if unresolved:
            ai_suggestions = await skill_ai_extractor.suggest_canonical_mappings(
                unresolved_skills=unresolved,
                context_text=cleaned_text[:1500],
            )
            if ai_suggestions:
                suggestion_map = {
                    s["original_name"].strip().lower(): s for s in ai_suggestions if "original_name" in s
                }
                for entry in preliminary:
                    key = entry.original_name.strip().lower()
                    if key in suggestion_map:
                        sug = suggestion_map[key]
                        if sug.get("is_known") and sug.get("canonical_name"):
                            canon = sug["canonical_name"]
                            if validate_canonical_assignment(entry.original_name, canon):
                                entry.canonical_name = canon
                                entry.category = sug.get("category", entry.category)
                                entry.skill_type = sug.get("skill_type", entry.skill_type)
                                entry.normalization_method = "semantic_suggestion"
                                entry.confidence_score = float(sug.get("confidence", 0.7))
                                entry.normalization_status = "pending_review"
                                if entry.original_name.lower() != canon.lower():
                                    entry.aliases_detected.append(entry.original_name)

        # 5. Duplicate Detection and Consolidation
        consolidated = consolidate_normalized_skills(preliminary)

        # Set resume_id on consolidated entries
        for c in consolidated:
            c.resume_id = resume_id

        # 6. Preserve Manual Edits from previous run
        if existing_records and not force_overwrite:
            manual_map = {
                r.canonical_name.lower(): r for r in existing_records if r.is_manually_edited
            }
            for c in consolidated:
                key = c.canonical_name.lower()
                if key in manual_map:
                    m = manual_map[key]
                    c.is_manually_edited = True
                    c.manually_edited_fields = m.manually_edited_fields or []
                    c.normalization_status = m.normalization_status
                    if "category" in c.manually_edited_fields:
                        c.category = m.category
                    if "canonical_name" in c.manually_edited_fields:
                        c.canonical_name = m.canonical_name

        # 7. Persist to DB or Staging Cache
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                # Clear existing unedited records or all if force_overwrite
                if force_overwrite:
                    db.execute(delete(ResumeSkill).where(ResumeSkill.resume_id == parsed_uuid))
                else:
                    # Delete non-manual records
                    db.execute(
                        delete(ResumeSkill).where(
                            ResumeSkill.resume_id == parsed_uuid,
                            ResumeSkill.is_manually_edited == False,
                        )
                    )

                for item in consolidated:
                    # Skip if already exists as manually edited in DB
                    existing = db.execute(
                        select(ResumeSkill).where(
                            ResumeSkill.resume_id == parsed_uuid,
                            ResumeSkill.canonical_name == item.canonical_name,
                        )
                    ).scalar_one_or_none()

                    if existing:
                        item.id = str(existing.id)
                        continue

                    # Try resolve skill_id
                    skill_id_val = None
                    if item.skill_id:
                        try:
                            skill_id_val = uuid.UUID(item.skill_id)
                        except ValueError:
                            pass

                    new_row = ResumeSkill(
                        id=uuid.uuid4(),
                        resume_id=parsed_uuid,
                        skill_id=skill_id_val,
                        original_name=item.original_name,
                        canonical_name=item.canonical_name,
                        category=item.category,
                        skill_type=item.skill_type,
                        normalization_method=item.normalization_method,
                        confidence_score=item.confidence_score,
                        normalization_status=item.normalization_status,
                        source_sections=item.source_sections,
                        source_evidence=item.source_evidence,
                        aliases_detected=item.aliases_detected,
                        occurrence_count=item.occurrence_count,
                        is_manually_edited=item.is_manually_edited,
                        manually_edited_fields=item.manually_edited_fields,
                        dictionary_version=item.dictionary_version,
                    )
                    db.add(new_row)
                    item.id = str(new_row.id)

                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error("Failed persisting normalized skills to DB: %s", exc)

        # Also populate staging cache
        self._staging_cache[resume_id] = consolidated
        return consolidated

    def get_normalized_skills(self, resume_id: str, db: Optional[Session] = None) -> List[SkillEntryData]:
        """Retrieves normalized skills for a resume from DB or staging cache."""
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                stmt = select(ResumeSkill).where(ResumeSkill.resume_id == parsed_uuid).order_by(ResumeSkill.canonical_name)
                rows = list(db.execute(stmt).scalars().all())
                if rows:
                    return [
                        SkillEntryData(
                            id=str(r.id),
                            resume_id=str(r.resume_id),
                            skill_id=str(r.skill_id) if r.skill_id else None,
                            original_name=r.original_name,
                            canonical_name=r.canonical_name,
                            category=r.category,
                            skill_type=r.skill_type,
                            normalization_method=r.normalization_method,
                            confidence_score=r.confidence_score,
                            normalization_status=r.normalization_status,
                            source_sections=r.source_sections or [],
                            source_evidence=r.source_evidence or [],
                            aliases_detected=r.aliases_detected or [],
                            occurrence_count=r.occurrence_count or 1,
                            is_manually_edited=r.is_manually_edited,
                            manually_edited_fields=r.manually_edited_fields or [],
                            dictionary_version=r.dictionary_version,
                        )
                        for r in rows
                    ]
            except Exception as exc:
                logger.warning("Error getting normalized skills from DB: %s", exc)

        return self._staging_cache.get(resume_id, [])

    def get_normalization_summary(self, resume_id: str, db: Optional[Session] = None) -> SkillSummaryData:
        """Computes aggregate analytics and metrics for skill normalization."""
        skills = self.get_normalized_skills(resume_id, db)
        if not skills:
            return SkillSummaryData()

        total_original = sum(s.occurrence_count for s in skills)
        total_normalized = len(skills)
        aliases_matched = sum(1 for s in skills if s.normalization_method == "alias_match" or len(s.aliases_detected) > 0)
        duplicates_consolidated = sum(s.occurrence_count - 1 for s in skills if s.occurrence_count > 1)
        pending_reviews = sum(1 for s in skills if s.normalization_status == "pending_review")
        unknown_skills = sum(1 for s in skills if s.normalization_method == "unknown")

        cat_dist: Dict[str, int] = {}
        type_dist: Dict[str, int] = {}

        for s in skills:
            cat_dist[s.category] = cat_dist.get(s.category, 0) + 1
            type_dist[s.skill_type] = type_dist.get(s.skill_type, 0) + 1

        return SkillSummaryData(
            total_original_skills=total_original,
            total_normalized_skills=total_normalized,
            aliases_matched=aliases_matched,
            duplicates_consolidated=duplicates_consolidated,
            pending_reviews=pending_reviews,
            unknown_skills=unknown_skills,
            category_distribution=cat_dist,
            skill_type_distribution=type_dist,
        )

    def get_pending_reviews(self, resume_id: str, db: Optional[Session] = None) -> List[SkillEntryData]:
        """Returns skills requiring human confirmation."""
        skills = self.get_normalized_skills(resume_id, db)
        return [s for s in skills if s.normalization_status == "pending_review"]

    def confirm_mapping(
        self,
        resume_id: str,
        skill_id: str,
        override_canonical_name: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[SkillEntryData]:
        """User confirms proposed canonical mapping."""
        skills = self.get_normalized_skills(resume_id, db)
        for s in skills:
            if s.id == skill_id or s.canonical_name == skill_id:
                if override_canonical_name:
                    s.canonical_name = override_canonical_name
                    s.manually_edited_fields.append("canonical_name")
                s.normalization_status = "confirmed"
                s.is_manually_edited = True
                s.manually_edited_fields.append("normalization_status")

                if db:
                    try:
                        parsed_sid = uuid.UUID(s.id)
                        row = db.execute(select(ResumeSkill).where(ResumeSkill.id == parsed_sid)).scalar_one_or_none()
                        if row:
                            row.canonical_name = s.canonical_name
                            row.normalization_status = "confirmed"
                            row.is_manually_edited = True
                            row.manually_edited_fields = list(set(s.manually_edited_fields))
                            db.commit()
                    except Exception as exc:
                        db.rollback()
                        logger.error("Error confirming skill in DB: %s", exc)

                return s
        return None

    def reject_mapping(
        self,
        resume_id: str,
        skill_id: str,
        db: Optional[Session] = None,
    ) -> Optional[SkillEntryData]:
        """User rejects proposed mapping; reverts canonical name to original raw form."""
        skills = self.get_normalized_skills(resume_id, db)
        for s in skills:
            if s.id == skill_id or s.canonical_name == skill_id:
                s.canonical_name = s.original_name
                s.normalization_status = "rejected"
                s.is_manually_edited = True
                s.manually_edited_fields.append("normalization_status")
                s.manually_edited_fields.append("canonical_name")

                if db:
                    try:
                        parsed_sid = uuid.UUID(s.id)
                        row = db.execute(select(ResumeSkill).where(ResumeSkill.id == parsed_sid)).scalar_one_or_none()
                        if row:
                            row.canonical_name = s.original_name
                            row.normalization_status = "rejected"
                            row.is_manually_edited = True
                            row.manually_edited_fields = list(set(s.manually_edited_fields))
                            db.commit()
                    except Exception as exc:
                        db.rollback()
                        logger.error("Error rejecting skill in DB: %s", exc)

                return s
        return None

    def update_skill_manually(
        self,
        resume_id: str,
        skill_id: str,
        payload: SkillManualUpdateRequest,
        db: Optional[Session] = None,
    ) -> Optional[SkillEntryData]:
        """Manually updates fields of a normalized skill."""
        skills = self.get_normalized_skills(resume_id, db)
        for s in skills:
            if s.id == skill_id or s.canonical_name == skill_id:
                if payload.canonical_name:
                    s.canonical_name = payload.canonical_name
                    s.manually_edited_fields.append("canonical_name")
                if payload.category:
                    s.category = payload.category
                    s.manually_edited_fields.append("category")
                if payload.skill_type:
                    s.skill_type = payload.skill_type
                    s.manually_edited_fields.append("skill_type")
                if payload.normalization_status:
                    s.normalization_status = payload.normalization_status
                    s.manually_edited_fields.append("normalization_status")

                s.is_manually_edited = True
                s.manually_edited_fields = list(set(s.manually_edited_fields))

                if db:
                    try:
                        parsed_sid = uuid.UUID(s.id)
                        row = db.execute(select(ResumeSkill).where(ResumeSkill.id == parsed_sid)).scalar_one_or_none()
                        if row:
                            row.canonical_name = s.canonical_name
                            row.category = s.category
                            row.skill_type = s.skill_type
                            row.normalization_status = s.normalization_status
                            row.is_manually_edited = True
                            row.manually_edited_fields = s.manually_edited_fields
                            db.commit()
                    except Exception as exc:
                        db.rollback()
                        logger.error("Error updating skill manually in DB: %s", exc)

                return s
        return None

    def delete_skill(self, resume_id: str, skill_id: str, db: Optional[Session] = None) -> bool:
        """Deletes a normalized skill record."""
        deleted = False
        if resume_id in self._staging_cache:
            initial_len = len(self._staging_cache[resume_id])
            self._staging_cache[resume_id] = [
                s for s in self._staging_cache[resume_id] if s.id != skill_id and s.canonical_name != skill_id
            ]
            deleted = len(self._staging_cache[resume_id]) < initial_len

        if db:
            try:
                parsed_sid = uuid.UUID(skill_id)
                res = db.execute(delete(ResumeSkill).where(ResumeSkill.id == parsed_sid))
                db.commit()
                deleted = (res.rowcount > 0) or deleted
            except ValueError:
                try:
                    res = db.execute(
                        delete(ResumeSkill).where(
                            ResumeSkill.resume_id == uuid.UUID(resume_id),
                            ResumeSkill.canonical_name == skill_id,
                        )
                    )
                    db.commit()
                    deleted = (res.rowcount > 0) or deleted
                except Exception as exc:
                    db.rollback()
                    logger.error("Error deleting skill by canonical name: %s", exc)
            except Exception as exc:
                db.rollback()
                logger.error("Error deleting skill from DB: %s", exc)

        return deleted


# Global singleton instance
skill_normalization_service = SkillNormalizationService()
