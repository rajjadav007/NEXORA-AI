"""
Project Intelligence Orchestration Service
Phase 3 | Feature 18: Project Intelligence
Coordinates project section detection, deterministic extraction, AI narrative analysis,
Feature #17 skill linking, deduplication, confidence scoring, and database persistence.
"""

import uuid
import logging
from typing import Optional, List, Dict, Any, Tuple, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.resume import Resume
from app.models.project import Project
from app.schemas.projects import (
    ProjectEntryData,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectSummaryData,
    ProjectSkillLinkData,
    ProjectLinkData,
)
from app.services.preview_service import preview_service
from app.services.cleaning import cleaning_service
from app.services.storage import staging_service
from app.services.projects.section_detector import (
    extract_project_sections,
    split_section_into_project_blocks,
)
from app.services.projects.deterministic_extractor import extract_deterministic_project
from app.services.projects.ai_extractor import project_ai_extractor
from app.services.projects.skill_linker import link_technologies_to_canonical_skills
from app.services.projects.deduplicator import deduplicate_projects
from app.services.projects.confidence_scorer import compute_project_confidence

logger = logging.getLogger(__name__)


class ProjectIntelligenceService:
    """Manages the lifecycle, extraction, and analysis of candidate project intelligence records."""

    def __init__(self):
        # In-memory staging cache for preview sessions prior to permanent save
        self._staging_cache: Dict[str, List[ProjectEntryData]] = {}

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

    async def extract_and_structure_projects(
        self,
        resume_id: str,
        reprocess: bool = False,
        force_overwrite: bool = False,
        db: Optional[Session] = None,
    ) -> List[ProjectEntryData]:
        """
        Extracts, structures, validates, and stores project intelligence records.
        """
        # 1. Check existing records in DB if not reprocessing
        existing_records: List[Project] = []
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                stmt = select(Project).where(Project.resume_id == parsed_uuid).order_by(Project.created_at)
                existing_records = list(db.execute(stmt).scalars().all())
                if existing_records and not reprocess:
                    return [self._model_to_schema(p) for p in existing_records]
            except (ValueError, Exception) as exc:
                logger.warning("Error fetching existing resume projects: %s", exc)

        # Check in-memory staging cache if no DB records
        if resume_id in self._staging_cache and not reprocess:
            return self._staging_cache[resume_id]

        # 2. Resolve cleaned resume text
        cleaned_text = self._resolve_cleaned_text(resume_id, db)
        if not cleaned_text:
            return []

        # 3. Detect project sections and chunk into blocks
        sections = extract_project_sections(cleaned_text)
        candidate_blocks: List[Tuple[str, str]] = []

        if sections:
            for sec in sections:
                blocks = split_section_into_project_blocks(sec["text"])
                for b in blocks:
                    candidate_blocks.append((b, sec["section_name"]))
        else:
            # Fallback: scan whole text for isolated project block patterns
            blocks = split_section_into_project_blocks(cleaned_text)
            for b in blocks:
                if any(kw in b.lower() for kw in ("github.com", "built a", "developed a", "project", "technologies:")):
                    candidate_blocks.append((b, "General"))

        if not candidate_blocks:
            return []

        # 4. Extract raw projects deterministically
        raw_projects: List[Dict[str, Any]] = []
        for block_text, sec_name in candidate_blocks:
            extracted = extract_deterministic_project(block_text, section_name=sec_name)
            if extracted and extracted.get("normalized_title"):
                raw_projects.append(extracted)

        # 5. Deduplicate candidates across sections
        deduped = deduplicate_projects(raw_projects)

        # 6. Contextual AI Narrative Enrichment via local Ollama
        enriched_entries: List[ProjectEntryData] = []
        for proj in deduped:
            block_sample = proj.get("detailed_description") or proj.get("short_description") or ""
            ai_data = await project_ai_extractor.analyze_project_narrative(block_sample)

            if ai_data:
                if ai_data.get("problem_statement"):
                    proj["problem_statement"] = ai_data["problem_statement"]
                if ai_data.get("proposed_solution"):
                    proj["proposed_solution"] = ai_data["proposed_solution"]
                if ai_data.get("domain"):
                    proj["domain"] = ai_data["domain"]
                if ai_data.get("candidate_role") and not proj.get("project_role"):
                    proj["project_role"] = ai_data["candidate_role"]
                if ai_data.get("individual_contribution") and ai_data["individual_contribution"] != "Specific individual contribution not specified.":
                    if ai_data["individual_contribution"] not in proj["responsibilities"]:
                        proj["responsibilities"].append(ai_data["individual_contribution"])
                if ai_data.get("project_category") and proj.get("project_category") == "other":
                    proj["project_category"] = ai_data["project_category"]

                proj["extraction_method"] = "hybrid"

            # Compute evidence-based confidence
            confidence = compute_project_confidence(proj)
            proj["confidence"] = confidence

            # Convert to ProjectEntryData
            links_models = [ProjectLinkData(**l) if isinstance(l, dict) else l for l in proj.get("project_links", [])]
            skills_models = [ProjectSkillLinkData(**s) if isinstance(s, dict) else s for s in proj.get("skills", [])]

            review_status = "confirmed" if confidence >= 0.85 else "pending"

            entry = ProjectEntryData(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                project_title=proj["project_title"],
                normalized_title=proj["normalized_title"],
                project_category=proj["project_category"],
                short_description=proj["short_description"],
                detailed_description=proj["detailed_description"],
                problem_statement=proj.get("problem_statement"),
                proposed_solution=proj.get("proposed_solution"),
                domain=proj.get("domain"),
                project_role=proj.get("project_role"),
                team_type=proj.get("team_type", "unknown"),
                team_size=proj.get("team_size"),
                start_date=proj.get("start_date"),
                end_date=proj.get("end_date"),
                is_ongoing=proj.get("is_ongoing", False),
                technologies=proj.get("technologies", []),
                skills=skills_models,
                responsibilities=proj.get("responsibilities", []),
                achievements=proj.get("achievements", []),
                measurable_outcomes=proj.get("measurable_outcomes", []),
                project_links=links_models,
                source_section=proj.get("source_section", "projects"),
                source_evidence=proj.get("source_evidence", []),
                confidence=confidence,
                extraction_method=proj.get("extraction_method", "hybrid"),
                review_status=review_status,
                is_manually_edited=False,
                manually_edited_fields=[],
            )
            enriched_entries.append(entry)

        # 7. Preserve Manual User Edits
        if existing_records and not force_overwrite:
            matched_manual_ids = set()
            for entry in enriched_entries:
                entry_title_lower = entry.normalized_title.lower()
                entry_links = {l.url.lower().rstrip("/") for l in entry.project_links if hasattr(l, "url")}

                for m in existing_records:
                    if not m.is_manually_edited or m.id in matched_manual_ids:
                        continue

                    m_title_lower = (m.normalized_title or m.project_title or "").lower()
                    m_links = {
                        l.get("url", "").lower().rstrip("/")
                        for l in (m.project_links or [])
                        if isinstance(l, dict)
                    }

                    # Match by exact or substring title or link overlap
                    is_match = (
                        m_title_lower == entry_title_lower
                        or entry_title_lower in m_title_lower
                        or m_title_lower in entry_title_lower
                        or bool(entry_links and m_links and entry_links.intersection(m_links))
                    )

                    if is_match:
                        matched_manual_ids.add(m.id)
                        entry.id = str(m.id)
                        entry.is_manually_edited = True
                        entry.manually_edited_fields = m.manually_edited_fields or []
                        entry.review_status = m.review_status
                        entry.project_title = m.project_title
                        entry.normalized_title = m.normalized_title
                        if m.project_category:
                            entry.project_category = m.project_category
                        if m.domain:
                            entry.domain = m.domain
                        if m.project_role:
                            entry.project_role = m.project_role
                        if m.team_size is not None:
                            entry.team_size = m.team_size
                        if m.team_type:
                            entry.team_type = m.team_type
                        if m.short_description:
                            entry.short_description = m.short_description
                        if m.detailed_description:
                            entry.detailed_description = m.detailed_description
                        if m.technologies:
                            entry.technologies = m.technologies
                        break

            # Append unmatched manual records so manually added projects are never lost
            for m in existing_records:
                if m.is_manually_edited and m.id not in matched_manual_ids:
                    enriched_entries.append(self._model_to_schema(m))

        # 8. Database Persistence
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                if force_overwrite:
                    db.execute(delete(Project).where(Project.resume_id == parsed_uuid))
                else:
                    db.execute(
                        delete(Project).where(
                            Project.resume_id == parsed_uuid,
                            Project.is_manually_edited == False,
                        )
                    )

                for entry in enriched_entries:
                    existing = None
                    if entry.id:
                        try:
                            existing = db.execute(
                                select(Project).where(
                                    Project.id == uuid.UUID(entry.id),
                                    Project.resume_id == parsed_uuid,
                                )
                            ).scalar_one_or_none()
                        except (ValueError, Exception):
                            existing = None

                    if existing:
                        existing.project_title = entry.project_title
                        existing.normalized_title = entry.normalized_title
                        existing.project_category = entry.project_category
                        existing.domain = entry.domain
                        existing.project_role = entry.project_role
                        existing.team_size = entry.team_size
                        existing.team_type = entry.team_type
                        existing.is_manually_edited = entry.is_manually_edited
                        existing.manually_edited_fields = entry.manually_edited_fields
                        existing.review_status = entry.review_status
                        continue

                    new_row = Project(
                        id=uuid.UUID(entry.id) if entry.id else uuid.uuid4(),
                        resume_id=parsed_uuid,
                        user_id=None,
                        project_title=entry.project_title,
                        normalized_title=entry.normalized_title,
                        project_category=entry.project_category,
                        short_description=entry.short_description,
                        detailed_description=entry.detailed_description,
                        problem_statement=entry.problem_statement,
                        proposed_solution=entry.proposed_solution,
                        domain=entry.domain,
                        project_role=entry.project_role,
                        team_type=entry.team_type,
                        team_size=entry.team_size,
                        start_date=entry.start_date,
                        end_date=entry.end_date,
                        is_ongoing=entry.is_ongoing,
                        technologies=entry.technologies,
                        skills=[s.model_dump() for s in entry.skills],
                        responsibilities=entry.responsibilities,
                        achievements=entry.achievements,
                        measurable_outcomes=entry.measurable_outcomes,
                        project_links=[l.model_dump() for l in entry.project_links],
                        source_section=entry.source_section,
                        source_evidence=entry.source_evidence,
                        confidence=entry.confidence,
                        extraction_method=entry.extraction_method,
                        review_status=entry.review_status,
                        is_manually_edited=entry.is_manually_edited,
                        manually_edited_fields=entry.manually_edited_fields,
                    )
                    db.add(new_row)
                    entry.id = str(new_row.id)

                db.commit()
                # Reload final state from DB to guarantee schema alignment
                stmt = select(Project).where(Project.resume_id == parsed_uuid).order_by(Project.created_at)
                rows = list(db.execute(stmt).scalars().all())
                if rows:
                    enriched_entries = [self._model_to_schema(r) for r in rows]
            except Exception as exc:
                db.rollback()
                logger.error("Failed persisting projects to database: %s", exc)
            except Exception as exc:
                db.rollback()
                logger.error("Failed persisting projects to database: %s", exc)

        self._staging_cache[resume_id] = enriched_entries
        return enriched_entries

    def get_projects(self, resume_id: str, db: Optional[Session] = None) -> List[ProjectEntryData]:
        """Retrieves all project records for a resume."""
        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                stmt = select(Project).where(Project.resume_id == parsed_uuid).order_by(Project.created_at)
                rows = list(db.execute(stmt).scalars().all())
                if rows:
                    return [self._model_to_schema(r) for r in rows]
            except Exception as exc:
                logger.warning("Error getting projects from DB: %s", exc)

        return self._staging_cache.get(resume_id, [])

    def get_project_by_id(self, resume_id: str, project_id: str, db: Optional[Session] = None) -> Optional[ProjectEntryData]:
        """Retrieves single project record."""
        projects = self.get_projects(resume_id, db)
        for p in projects:
            if p.id == project_id or p.normalized_title == project_id:
                return p
        return None

    def add_project_manually(
        self,
        resume_id: str,
        payload: ProjectCreateRequest,
        db: Optional[Session] = None,
    ) -> ProjectEntryData:
        """Manually creates a new project entry."""
        from app.services.projects.normalizer import normalize_project_title
        norm_title = normalize_project_title(payload.project_title)

        canonical_techs, linked_skills = link_technologies_to_canonical_skills(
            payload.technologies or []
        )
        links_models = [ProjectLinkData(**l) for l in (payload.project_links or [])]

        entry = ProjectEntryData(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            project_title=payload.project_title,
            normalized_title=norm_title,
            project_category=payload.project_category or "other",
            short_description=payload.short_description,
            detailed_description=payload.detailed_description,
            problem_statement=payload.problem_statement,
            proposed_solution=payload.proposed_solution,
            domain=payload.domain,
            project_role=payload.project_role,
            team_type=payload.team_type or "unknown",
            team_size=payload.team_size,
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_ongoing=payload.is_ongoing or False,
            technologies=canonical_techs,
            skills=linked_skills,
            responsibilities=payload.responsibilities or [],
            achievements=payload.achievements or [],
            measurable_outcomes=payload.measurable_outcomes or [],
            project_links=links_models,
            source_section="User Entry",
            source_evidence=["Manually entered by candidate"],
            confidence=1.0,
            extraction_method="manual",
            review_status="confirmed",
            is_manually_edited=True,
            manually_edited_fields=["all"],
        )

        if resume_id not in self._staging_cache:
            self._staging_cache[resume_id] = []
        self._staging_cache[resume_id].append(entry)

        if db:
            try:
                parsed_uuid = uuid.UUID(resume_id)
                new_row = Project(
                    id=uuid.UUID(entry.id),
                    resume_id=parsed_uuid,
                    user_id=None,
                    project_title=entry.project_title,
                    normalized_title=entry.normalized_title,
                    project_category=entry.project_category,
                    short_description=entry.short_description,
                    detailed_description=entry.detailed_description,
                    problem_statement=entry.problem_statement,
                    proposed_solution=entry.proposed_solution,
                    domain=entry.domain,
                    project_role=entry.project_role,
                    team_type=entry.team_type,
                    team_size=entry.team_size,
                    start_date=entry.start_date,
                    end_date=entry.end_date,
                    is_ongoing=entry.is_ongoing,
                    technologies=entry.technologies,
                    skills=[s.model_dump() for s in entry.skills],
                    responsibilities=entry.responsibilities,
                    achievements=entry.achievements,
                    measurable_outcomes=entry.measurable_outcomes,
                    project_links=[l.model_dump() for l in entry.project_links],
                    source_section=entry.source_section,
                    source_evidence=entry.source_evidence,
                    confidence=entry.confidence,
                    extraction_method=entry.extraction_method,
                    review_status=entry.review_status,
                    is_manually_edited=True,
                    manually_edited_fields=entry.manually_edited_fields,
                )
                db.add(new_row)
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error("Failed adding project to DB: %s", exc)

        return entry

    def update_project_manually(
        self,
        resume_id: str,
        project_id: str,
        payload: ProjectUpdateRequest,
        db: Optional[Session] = None,
    ) -> Optional[ProjectEntryData]:
        """Manually updates an existing project."""
        projects = self.get_projects(resume_id, db)
        for p in projects:
            if p.id == project_id or p.normalized_title == project_id:
                edited_fields = list(p.manually_edited_fields)

                if payload.project_title is not None:
                    p.project_title = payload.project_title
                    from app.services.projects.normalizer import normalize_project_title
                    p.normalized_title = normalize_project_title(payload.project_title)
                    edited_fields.append("project_title")
                if payload.project_category is not None:
                    p.project_category = payload.project_category
                    edited_fields.append("project_category")
                if payload.short_description is not None:
                    p.short_description = payload.short_description
                    edited_fields.append("short_description")
                if payload.detailed_description is not None:
                    p.detailed_description = payload.detailed_description
                    edited_fields.append("detailed_description")
                if payload.problem_statement is not None:
                    p.problem_statement = payload.problem_statement
                    edited_fields.append("problem_statement")
                if payload.proposed_solution is not None:
                    p.proposed_solution = payload.proposed_solution
                    edited_fields.append("proposed_solution")
                if payload.domain is not None:
                    p.domain = payload.domain
                    edited_fields.append("domain")
                if payload.project_role is not None:
                    p.project_role = payload.project_role
                    edited_fields.append("project_role")
                if payload.team_type is not None:
                    p.team_type = payload.team_type
                    edited_fields.append("team_type")
                if payload.team_size is not None:
                    p.team_size = payload.team_size
                    edited_fields.append("team_size")
                if payload.start_date is not None:
                    p.start_date = payload.start_date
                    edited_fields.append("start_date")
                if payload.end_date is not None:
                    p.end_date = payload.end_date
                    edited_fields.append("end_date")
                if payload.is_ongoing is not None:
                    p.is_ongoing = payload.is_ongoing
                    edited_fields.append("is_ongoing")
                if payload.technologies is not None:
                    canonical_techs, linked_skills = link_technologies_to_canonical_skills(payload.technologies)
                    p.technologies = canonical_techs
                    p.skills = linked_skills
                    edited_fields.append("technologies")
                if payload.responsibilities is not None:
                    p.responsibilities = payload.responsibilities
                    edited_fields.append("responsibilities")
                if payload.achievements is not None:
                    p.achievements = payload.achievements
                    edited_fields.append("achievements")
                if payload.measurable_outcomes is not None:
                    p.measurable_outcomes = payload.measurable_outcomes
                    edited_fields.append("measurable_outcomes")
                if payload.project_links is not None:
                    p.project_links = [ProjectLinkData(**l) for l in payload.project_links]
                    edited_fields.append("project_links")
                if payload.review_status is not None:
                    p.review_status = payload.review_status
                    edited_fields.append("review_status")

                p.is_manually_edited = True
                p.manually_edited_fields = list(set(edited_fields))

                if db:
                    try:
                        parsed_pid = uuid.UUID(p.id)
                        row = db.execute(select(Project).where(Project.id == parsed_pid)).scalar_one_or_none()
                        if row:
                            row.project_title = p.project_title
                            row.normalized_title = p.normalized_title
                            row.project_category = p.project_category
                            row.short_description = p.short_description
                            row.detailed_description = p.detailed_description
                            row.problem_statement = p.problem_statement
                            row.proposed_solution = p.proposed_solution
                            row.domain = p.domain
                            row.project_role = p.project_role
                            row.team_type = p.team_type
                            row.team_size = p.team_size
                            row.start_date = p.start_date
                            row.end_date = p.end_date
                            row.is_ongoing = p.is_ongoing
                            row.technologies = p.technologies
                            row.skills = [s.model_dump() for s in p.skills]
                            row.responsibilities = p.responsibilities
                            row.achievements = p.achievements
                            row.measurable_outcomes = p.measurable_outcomes
                            row.project_links = [l.model_dump() for l in p.project_links]
                            row.review_status = p.review_status
                            row.is_manually_edited = True
                            row.manually_edited_fields = p.manually_edited_fields
                            db.commit()
                    except Exception as exc:
                        db.rollback()
                        logger.error("Failed updating project in DB: %s", exc)

                return p
        return None

    def confirm_project(
        self,
        resume_id: str,
        project_id: str,
        db: Optional[Session] = None,
    ) -> Optional[ProjectEntryData]:
        """Confirms an extracted project mapping."""
        update_req = ProjectUpdateRequest(review_status="confirmed")
        return self.update_project_manually(resume_id, project_id, update_req, db)

    def delete_project(self, resume_id: str, project_id: str, db: Optional[Session] = None) -> bool:
        """Deletes a project record."""
        deleted = False
        if resume_id in self._staging_cache:
            initial_len = len(self._staging_cache[resume_id])
            self._staging_cache[resume_id] = [
                p for p in self._staging_cache[resume_id] if p.id != project_id and p.normalized_title != project_id
            ]
            deleted = len(self._staging_cache[resume_id]) < initial_len

        if db:
            try:
                parsed_pid = uuid.UUID(project_id)
                res = db.execute(delete(Project).where(Project.id == parsed_pid))
                db.commit()
                deleted = (res.rowcount > 0) or deleted
            except ValueError:
                try:
                    res = db.execute(
                        delete(Project).where(
                            Project.resume_id == uuid.UUID(resume_id),
                            Project.normalized_title == project_id,
                        )
                    )
                    db.commit()
                    deleted = (res.rowcount > 0) or deleted
                except Exception:
                    pass
            except Exception as exc:
                db.rollback()
                logger.error("Failed deleting project from DB: %s", exc)

        return deleted

    def get_project_summary(self, resume_id: str, db: Optional[Session] = None) -> ProjectSummaryData:
        """Computes aggregate analytics and metrics for candidate projects."""
        projects = self.get_projects(resume_id, db)
        if not projects:
            return ProjectSummaryData()

        cat_dist: Dict[str, int] = {}
        domain_dist: Dict[str, int] = {}
        unique_techs: Set[str] = set()

        github_count = 0
        demo_count = 0
        measurable_count = 0
        pending_count = 0
        team_count = 0
        solo_count = 0

        for p in projects:
            cat_dist[p.project_category] = cat_dist.get(p.project_category, 0) + 1
            if p.domain:
                domain_dist[p.domain] = domain_dist.get(p.domain, 0) + 1

            for t in p.technologies:
                unique_techs.add(t)

            has_gh = any(l.type == "github" or "github.com" in l.url.lower() for l in p.project_links)
            if has_gh:
                github_count += 1

            has_dm = any(l.type == "demo" for l in p.project_links)
            if has_dm:
                demo_count += 1

            if len(p.measurable_outcomes) > 0 or len(p.achievements) > 0:
                measurable_count += 1

            if p.review_status == "pending" or p.review_status == "needs_review":
                pending_count += 1

            if p.team_type == "team":
                team_count += 1
            elif p.team_type == "individual":
                solo_count += 1

        tech_list = sorted(list(unique_techs))
        return ProjectSummaryData(
            total_projects=len(projects),
            projects_by_category=cat_dist,
            projects_by_domain=domain_dist,
            unique_technologies=tech_list,
            unique_technologies_count=len(tech_list),
            projects_with_github=github_count,
            projects_with_demo=demo_count,
            projects_with_measurable_outcomes=measurable_count,
            pending_reviews=pending_count,
            team_projects_count=team_count,
            solo_projects_count=solo_count,
        )

    def _model_to_schema(self, p: Project) -> ProjectEntryData:
        """Maps SQLAlchemy Project model to ProjectEntryData schema."""
        links = [ProjectLinkData(**l) if isinstance(l, dict) else l for l in (p.project_links or [])]
        skills = [ProjectSkillLinkData(**s) if isinstance(s, dict) else s for s in (p.skills or [])]

        return ProjectEntryData(
            id=str(p.id),
            resume_id=str(p.resume_id),
            project_title=p.project_title,
            normalized_title=p.normalized_title,
            project_category=p.project_category,
            short_description=p.short_description,
            detailed_description=p.detailed_description,
            problem_statement=p.problem_statement,
            proposed_solution=p.proposed_solution,
            domain=p.domain,
            project_role=p.project_role,
            team_type=p.team_type,
            team_size=p.team_size,
            start_date=p.start_date,
            end_date=p.end_date,
            is_ongoing=p.is_ongoing,
            technologies=p.technologies or [],
            skills=skills,
            responsibilities=p.responsibilities or [],
            achievements=p.achievements or [],
            measurable_outcomes=p.measurable_outcomes or [],
            project_links=links,
            source_section=p.source_section,
            source_evidence=p.source_evidence or [],
            confidence=p.confidence,
            extraction_method=p.extraction_method,
            review_status=p.review_status,
            is_manually_edited=p.is_manually_edited,
            manually_edited_fields=p.manually_edited_fields or [],
        )


# Global singleton instance
project_intelligence_service = ProjectIntelligenceService()
