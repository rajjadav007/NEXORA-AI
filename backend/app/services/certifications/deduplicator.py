"""
Deduplicator for Certifications and Achievements
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Consolidates candidate records mentioned across multiple resume sections,
merging issuer information, dates, credential IDs, URLs, and evidence.
"""

import re
from typing import List, Dict, Any


def _normalize_key(text: str) -> str:
    """Creates a normalized comparison key."""
    if not text:
        return ""
    clean = re.sub(r"[^a-zA-Z0-9]", "", text).lower()
    return clean


def deduplicate_certifications(certs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates certifications by normalized name and issuing organization.
    Merges credential IDs, URLs, dates, and evidence.
    """
    deduped: Dict[str, Dict[str, Any]] = {}

    for c in certs:
        name = c.get("certification_name") or ""
        norm_key = _normalize_key(name)
        if not norm_key:
            continue

        if norm_key not in deduped:
            deduped[norm_key] = dict(c)
        else:
            existing = deduped[norm_key]
            # Merge fields
            if not existing.get("issuing_organization") and c.get("issuing_organization"):
                existing["issuing_organization"] = c["issuing_organization"]
            if not existing.get("credential_id") and c.get("credential_id"):
                existing["credential_id"] = c["credential_id"]
            if not existing.get("credential_url") and c.get("credential_url"):
                existing["credential_url"] = c["credential_url"]
            if not existing.get("issue_date") and c.get("issue_date"):
                existing["issue_date"] = c["issue_date"]
            if not existing.get("expiry_date") and c.get("expiry_date"):
                existing["expiry_date"] = c["expiry_date"]

            # Merge skills
            existing_skills = {s.canonical_name if hasattr(s, "canonical_name") else s.get("canonical_name") for s in existing.get("related_skills", [])}
            for s in c.get("related_skills", []):
                s_name = s.canonical_name if hasattr(s, "canonical_name") else s.get("canonical_name")
                if s_name and s_name not in existing_skills:
                    existing["related_skills"].append(s)
                    existing_skills.add(s_name)

            # Merge evidence
            existing_ev = set(existing.get("source_evidence", []))
            for ev in c.get("source_evidence", []):
                if ev not in existing_ev:
                    existing["source_evidence"].append(ev)
                    existing_ev.add(ev)

    return list(deduped.values())


def deduplicate_achievements(achievements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates achievements by normalized title.
    Merges ranks, events, team info, project links, and evidence.
    """
    deduped: Dict[str, Dict[str, Any]] = {}

    for a in achievements:
        title = a.get("achievement_title") or ""
        norm_key = _normalize_key(title)
        if not norm_key:
            continue

        if norm_key not in deduped:
            deduped[norm_key] = dict(a)
        else:
            existing = deduped[norm_key]
            if not existing.get("event_name") and a.get("event_name"):
                existing["event_name"] = a["event_name"]
            if not existing.get("organization") and a.get("organization"):
                existing["organization"] = a["organization"]
            if not existing.get("rank_or_position") and a.get("rank_or_position"):
                existing["rank_or_position"] = a["rank_or_position"]
            if not existing.get("achievement_date") and a.get("achievement_date"):
                existing["achievement_date"] = a["achievement_date"]
            if not existing.get("related_project_id") and a.get("related_project_id"):
                existing["related_project_id"] = a["related_project_id"]
                existing["related_project_title"] = a.get("related_project_title")
            if not existing.get("achievement_url") and a.get("achievement_url"):
                existing["achievement_url"] = a["achievement_url"]

            existing_ev = set(existing.get("source_evidence", []))
            for ev in a.get("source_evidence", []):
                if ev not in existing_ev:
                    existing["source_evidence"].append(ev)
                    existing_ev.add(ev)

    return list(deduped.values())
