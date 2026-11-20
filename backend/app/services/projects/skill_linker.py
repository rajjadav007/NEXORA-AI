"""
Project Skill Linker
Phase 3 | Feature 18: Project Intelligence
Integrates with Feature #17 Skill Normalization Dictionary to link project technologies
to standardized canonical skill IDs and names without creating redundant normalization systems.
"""

from typing import List, Dict, Any, Tuple
from app.schemas.projects import ProjectSkillLinkData
from app.services.skills.dictionary import skill_dictionary


def link_technologies_to_canonical_skills(
    raw_technologies: List[str],
    evidence_text: str = "",
) -> Tuple[List[str], List[ProjectSkillLinkData]]:
    """
    Takes raw technology names identified in a project, maps them against Feature #17
    canonical dictionary, and returns:
    1. Standardized technology names list (canonical names where available)
    2. List of ProjectSkillLinkData with canonical IDs, categories, and evidence
    """
    canonical_tech_names: List[str] = []
    linked_skills: List[ProjectSkillLinkData] = []
    seen_canonical = set()

    for raw in raw_technologies:
        if not raw or not raw.strip():
            continue

        clean_raw = raw.strip()
        match = skill_dictionary.lookup(clean_raw)

        if match:
            spec, match_method, conf = match
            canon_name = spec["name"]
            canon_id = spec.get("id")
            cat = spec.get("category", "Other")

            if canon_name not in seen_canonical:
                seen_canonical.add(canon_name)
                canonical_tech_names.append(canon_name)
                linked_skills.append(
                    ProjectSkillLinkData(
                        original_name=clean_raw,
                        canonical_id=canon_id,
                        canonical_name=canon_name,
                        category=cat,
                        confidence=conf,
                        is_explicit=True,
                    )
                )
        else:
            # Uncatalogued technology: preserve verbatim
            if clean_raw not in seen_canonical:
                seen_canonical.add(clean_raw)
                canonical_tech_names.append(clean_raw)
                linked_skills.append(
                    ProjectSkillLinkData(
                        original_name=clean_raw,
                        canonical_id=None,
                        canonical_name=clean_raw,
                        category="Other",
                        confidence=0.6,
                        is_explicit=True,
                    )
                )

    return canonical_tech_names, linked_skills
