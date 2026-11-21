"""
Project Linker for Achievements
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Connects hackathon and competition achievements directly with candidate projects
from Feature #18 Project Intelligence.
"""

import uuid
import re
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.project import Project


def link_achievement_to_project(
    achievement_text: str,
    resume_id: str,
    db: Optional[Session] = None,
    staging_projects: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Optional[uuid.UUID], Optional[str]]:
    """
    Scans achievement text for mentions of candidate projects.
    Returns (project_id, project_title) or (None, None).
    """
    if not achievement_text or not resume_id:
        return None, None

    known_projects: List[Tuple[uuid.UUID, str]] = []

    # 1. Fetch from database if session is present
    if db:
        try:
            parsed_resume_id = uuid.UUID(resume_id)
            stmt = select(Project).where(Project.resume_id == parsed_resume_id)
            db_projects = db.execute(stmt).scalars().all()
            for p in db_projects:
                known_projects.append((p.id, p.project_title))
        except (ValueError, Exception):
            pass

    # 2. Add from staging projects if provided
    if staging_projects:
        for sp in staging_projects:
            pid = sp.get("id")
            title = sp.get("project_title")
            if pid and title:
                try:
                    uuid_val = uuid.UUID(str(pid))
                    known_projects.append((uuid_val, title))
                except ValueError:
                    pass

    if not known_projects:
        return None, None

    achieve_lower = achievement_text.lower()

    # Search for project title in achievement text
    for pid, ptitle in known_projects:
        clean_title = ptitle.strip()
        if len(clean_title) < 3:
            continue

        # Look for whole word or exact title match
        pattern = r"\b" + re.escape(clean_title.lower()) + r"\b"
        if re.search(pattern, achieve_lower):
            return pid, ptitle

    return None, None
