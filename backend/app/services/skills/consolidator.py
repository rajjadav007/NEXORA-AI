"""
Skill Duplicate Detector and Evidence Consolidator
Phase 3 | Feature 17: Skill Normalization
Consolidates identical canonical skill mentions across resume sections while strictly preserving all original names,
source sections, and evidence text snippets.
"""

from typing import List, Dict, Any
from app.schemas.skills import SkillEntryData


def consolidate_normalized_skills(raw_entries: List[SkillEntryData]) -> List[SkillEntryData]:
    """
    Groups entries by canonical_name.
    Consolidates multiple mentions into a single normalized skill record:
    - Combines all unique original names
    - Combines all unique source sections
    - Combines all unique source evidence snippets
    - Records all alias variations observed
    - Tracks occurrence_count (evidence volume)
    - Retains highest confidence score
    """
    if not raw_entries:
        return []

    grouped: Dict[str, Dict[str, Any]] = {}

    for entry in raw_entries:
        key = entry.canonical_name.strip().lower()

        if key not in grouped:
            grouped[key] = {
                "base_entry": entry,
                "original_names": [entry.original_name],
                "source_sections": list(entry.source_sections),
                "source_evidence": list(entry.source_evidence),
                "aliases_detected": list(entry.aliases_detected),
                "occurrence_count": entry.occurrence_count or 1,
                "max_confidence": entry.confidence_score,
                "is_manually_edited": entry.is_manually_edited,
                "manually_edited_fields": list(entry.manually_edited_fields),
            }
        else:
            rec = grouped[key]
            # Accumulate original names
            if entry.original_name not in rec["original_names"]:
                rec["original_names"].append(entry.original_name)

            # Accumulate source sections
            for sec in entry.source_sections:
                if sec and sec not in rec["source_sections"]:
                    rec["source_sections"].append(sec)

            # Accumulate source evidence
            for ev in entry.source_evidence:
                if ev and ev not in rec["source_evidence"]:
                    rec["source_evidence"].append(ev)

            # Accumulate aliases detected
            for al in entry.aliases_detected:
                if al and al not in rec["aliases_detected"]:
                    rec["aliases_detected"].append(al)

            # Also add original name to aliases detected if different from canonical
            if entry.original_name != entry.canonical_name and entry.original_name not in rec["aliases_detected"]:
                rec["aliases_detected"].append(entry.original_name)

            rec["occurrence_count"] += (entry.occurrence_count or 1)
            if entry.confidence_score > rec["max_confidence"]:
                rec["max_confidence"] = entry.confidence_score

            if entry.is_manually_edited:
                rec["is_manually_edited"] = True
                for fld in entry.manually_edited_fields:
                    if fld not in rec["manually_edited_fields"]:
                        rec["manually_edited_fields"].append(fld)

    consolidated: List[SkillEntryData] = []
    for key, data in grouped.items():
        base = data["base_entry"]

        # Ensure all detected aliases are present
        aliases = data["aliases_detected"]
        for oname in data["original_names"]:
            if oname != base.canonical_name and oname not in aliases:
                aliases.append(oname)

        # Primary original name can be first seen or canonical
        primary_orig = data["original_names"][0] if data["original_names"] else base.original_name

        consolidated_entry = SkillEntryData(
            id=base.id,
            resume_id=base.resume_id,
            skill_id=base.skill_id,
            original_name=primary_orig,
            canonical_name=base.canonical_name,
            category=base.category,
            skill_type=base.skill_type,
            normalization_method=base.normalization_method,
            confidence_score=round(data["max_confidence"], 3),
            normalization_status=base.normalization_status,
            source_sections=data["source_sections"] or ["skills"],
            source_evidence=data["source_evidence"],
            aliases_detected=aliases,
            occurrence_count=data["occurrence_count"],
            is_manually_edited=data["is_manually_edited"],
            manually_edited_fields=data["manually_edited_fields"],
            dictionary_version=base.dictionary_version,
        )
        consolidated.append(consolidated_entry)

    # Sort alphabetically by canonical name
    consolidated.sort(key=lambda s: s.canonical_name.lower())
    return consolidated
