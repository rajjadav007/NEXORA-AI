"""
Project Deduplicator
Phase 3 | Feature 18: Project Intelligence
Identifies and merges duplicate project records appearing across resume sections
based on normalized titles, repository URLs, and description overlap.
"""

from typing import List, Dict, Any
from app.schemas.projects import ProjectEntryData, ProjectLinkData, ProjectSkillLinkData


def are_projects_duplicates(p1: Dict[str, Any], p2: Dict[str, Any]) -> bool:
    """
    Checks if two candidate project dictionaries refer to the same underlying project.
    """
    # 1. Exact normalized title match
    t1 = p1.get("normalized_title", "").strip().lower()
    t2 = p2.get("normalized_title", "").strip().lower()
    if t1 and t2 and t1 == t2 and len(t1) > 3:
        return True

    # 2. Matching GitHub or project link URLs
    links1 = {l.url.lower().rstrip("/") for l in p1.get("project_links", []) if hasattr(l, "url")}
    links2 = {l.url.lower().rstrip("/") for l in p2.get("project_links", []) if hasattr(l, "url")}
    if links1 and links2 and bool(links1.intersection(links2)):
        return True

    # 3. High title word overlap (e.g. "Smart AI Resume Parser" and "AI Resume Parser")
    words1 = set(t1.split())
    words2 = set(t2.split())
    if len(words1) >= 2 and len(words2) >= 2:
        overlap = words1.intersection(words2)
        if len(overlap) / max(len(words1), len(words2)) >= 0.8:
            return True

    return False


def deduplicate_projects(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Consolidates duplicate project candidate dictionaries, combining evidence,
    technologies, and external URLs.
    """
    if not projects:
        return []

    deduped: List[Dict[str, Any]] = []

    for cand in projects:
        matched_idx = -1
        for i, existing in enumerate(deduped):
            if are_projects_duplicates(cand, existing):
                matched_idx = i
                break

        if matched_idx == -1:
            deduped.append(cand)
        else:
            base = deduped[matched_idx]
            # Merge technologies
            tech_set = set(base.get("technologies", []))
            for t in cand.get("technologies", []):
                if t not in tech_set:
                    base["technologies"].append(t)
                    tech_set.add(t)

            # Merge skills
            existing_skill_keys = {s.canonical_name.lower() for s in base.get("skills", [])}
            for s in cand.get("skills", []):
                if s.canonical_name.lower() not in existing_skill_keys:
                    base["skills"].append(s)
                    existing_skill_keys.add(s.canonical_name.lower())

            # Merge links
            link_urls = {l.url for l in base.get("project_links", [])}
            for l in cand.get("project_links", []):
                if l.url not in link_urls:
                    base["project_links"].append(l)
                    link_urls.add(l.url)

            # Merge evidence
            for ev in cand.get("source_evidence", []):
                if ev not in base.get("source_evidence", []):
                    base["source_evidence"].append(ev)

            # Merge achievements & metrics
            for ach in cand.get("achievements", []):
                if ach not in base.get("achievements", []):
                    base["achievements"].append(ach)

            for m in cand.get("measurable_outcomes", []):
                if m not in base.get("measurable_outcomes", []):
                    base["measurable_outcomes"].append(m)

            # Keep more specific category
            if base.get("project_category") == "other" and cand.get("project_category") != "other":
                base["project_category"] = cand["project_category"]

            # Keep more detailed description
            if len(cand.get("detailed_description") or "") > len(base.get("detailed_description") or ""):
                base["detailed_description"] = cand["detailed_description"]

    return deduped
