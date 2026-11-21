"""
Skill Linker for Certifications and Achievements
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Connects technologies extracted from certifications and achievements directly with
Feature #17 Skill Normalization Dictionary.
"""

from typing import List, Dict, Any, Tuple
from app.schemas.certifications import CertificationSkillLinkData
from app.services.skills.dictionary import skill_dictionary


def extract_skills_from_text(text: str) -> List[CertificationSkillLinkData]:
    """
    Extracts explicitly mentioned canonical skills from certification or achievement text.
    Looks up tokens and n-grams in Feature #17 skill dictionary.
    """
    if not text or not text.strip():
        return []

    linked: List[CertificationSkillLinkData] = []
    seen = set()

    # Words and phrases
    # Clean text to alphanumeric and common symbols
    cleaned = text.replace(",", " ").replace(";", " ").replace("/", " ").replace("|", " ").replace("(", " ").replace(")", " ")
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]

    # Check 1-gram, 2-gram, 3-grams
    ngrams = []
    for i in range(len(tokens)):
        ngrams.append(tokens[i])
        if i + 1 < len(tokens):
            ngrams.append(f"{tokens[i]} {tokens[i+1]}")
        if i + 2 < len(tokens):
            ngrams.append(f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}")

    for phrase in ngrams:
        match = skill_dictionary.lookup(phrase)
        if match:
            spec, match_method, conf = match
            canon_name = spec["name"]
            canon_id = spec.get("id")
            category = spec.get("category", "Other")

            if canon_name not in seen:
                seen.add(canon_name)
                linked.append(
                    CertificationSkillLinkData(
                        original_name=phrase,
                        canonical_id=canon_id,
                        canonical_name=canon_name,
                        category=category,
                        confidence=conf,
                        is_explicit=True,
                    )
                )

    return linked
