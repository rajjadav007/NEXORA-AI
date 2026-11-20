"""
Skill Normalization Service Package
Phase 3 | Feature 17: Skill Normalization
"""

from app.services.skills.service import (
    SkillNormalizationService,
    skill_normalization_service,
)
from app.services.skills.dictionary import (
    SkillDictionary,
    skill_dictionary,
    DICTIONARY_VERSION,
)
from app.services.skills.formatter import (
    normalize_skill_text,
    create_lookup_key,
)
from app.services.skills.false_merge_guard import (
    are_distinct_technologies,
    validate_canonical_assignment,
)
from app.services.skills.context_matcher import (
    disambiguate_token,
)
from app.services.skills.consolidator import (
    consolidate_normalized_skills,
)

__all__ = [
    "SkillNormalizationService",
    "skill_normalization_service",
    "SkillDictionary",
    "skill_dictionary",
    "DICTIONARY_VERSION",
    "normalize_skill_text",
    "create_lookup_key",
    "are_distinct_technologies",
    "validate_canonical_assignment",
    "disambiguate_token",
    "consolidate_normalized_skills",
]
