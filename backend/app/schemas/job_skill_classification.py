"""
Job Skill Classification Pydantic Schemas
Phase 6 | Feature 37: Mandatory & Preferred Skills Classification
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.skills.dictionary import skill_dictionary
from app.services.skills.formatter import create_lookup_key, normalize_skill_text

CLASSIFICATION_TYPES = ("Mandatory", "Preferred", "Optional", "Unspecified")
PRIORITY_LEVELS = ("High", "Medium", "Low")
PROFICIENCY_LEVELS = ("Beginner", "Intermediate", "Advanced", "Expert", "Unspecified")
SOURCE_TYPES = ("explicit", "inferred")

_CLASSIFICATION_LOOKUP = {
    "mandatory": "Mandatory",
    "required": "Mandatory",
    "must-have": "Mandatory",
    "must have": "Mandatory",
    "essential": "Mandatory",
    "preferred": "Preferred",
    "good-to-have": "Preferred",
    "good to have": "Preferred",
    "nice to have": "Preferred",
    "bonus": "Preferred",
    "optional": "Optional",
    "additional": "Optional",
    "unspecified": "Unspecified",
}
_PROFICIENCY_LOOKUP = {item.lower(): item for item in PROFICIENCY_LEVELS}
_SOURCE_TYPE_LOOKUP = {item.lower(): item for item in SOURCE_TYPES}
_CATEGORY_ALIASES = {
    "programming language": "Programming Language",
    "programming languages": "Programming Language",
    "language": "Programming Language",
    "ai & machine learning": "AI & Machine Learning",
    "ai and machine learning": "AI & Machine Learning",
    "ai/ml": "AI & Machine Learning",
    "machine learning": "AI & Machine Learning",
    "ai framework": "AI Framework",
    "framework & library": "Framework & Library",
    "frameworks & libraries": "Framework & Library",
    "framework": "Framework & Library",
    "library": "Framework & Library",
    "tool & platform": "Tool & Platform",
    "tools & platforms": "Tool & Platform",
    "cloud": "Tool & Platform",
    "database": "Database",
    "databases": "Database",
    "soft skill": "Soft Skill",
    "soft skills": "Soft Skill",
    "domain knowledge": "Domain Knowledge",
    "other": "Other",
}
_NULL_SENTINELS = {"", "null", "none", "n/a", "na", "not specified", "unspecified"}

_PRIORITY_BOUNDS = {
    "Mandatory": (80, 100, 90),
    "Preferred": (40, 79, 60),
    "Optional": (1, 39, 25),
}
_PRIORITY_LEVEL_MAP = {
    "Mandatory": "High",
    "Preferred": "Medium",
    "Optional": "Low",
    "Unspecified": "Low",
}
_CLASSIFICATION_RANK = {
    "Mandatory": 3,
    "Preferred": 2,
    "Optional": 1,
    "Unspecified": 0,
}


def _clean_text(value: Any, max_len: int = 400) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _NULL_SENTINELS:
        return None
    return text[:max_len]


def normalize_skill_name(raw_name: str) -> tuple[str, Optional[str], Optional[str]]:
    """
    Normalize skill name using the existing Feature 17 skill_dictionary & formatter.
    Returns (normalized_name, original_name_if_different, canonical_category_if_known).
    """
    cleaned = normalize_skill_text(raw_name)
    if not cleaned:
        return raw_name.strip(), None, None

    match = skill_dictionary.lookup(cleaned)
    if match:
        spec, _method, _conf = match
        canon_name = spec["name"]
        canon_cat = spec.get("category")
        orig = cleaned if cleaned.lower() != canon_name.lower() else None
        return canon_name, orig, canon_cat

    return cleaned, None, None


class ClassifiedSkillItem(BaseModel):
    """Single classified skill with priority score, proficiency, and supporting evidence."""

    name: str = Field(..., min_length=1, max_length=160)
    original_name: Optional[str] = Field(default=None, max_length=160)
    category: str = Field(default="Other", max_length=100)
    classification: str = Field(default="Unspecified", max_length=30)
    priority_score: Optional[int] = Field(default=None, ge=0, le=100)
    priority_level: str = Field(default="Low", max_length=20)
    expected_proficiency: str = Field(default="Unspecified", max_length=30)
    evidence: Optional[str] = Field(default=None, max_length=500)
    source_type: str = Field(default="explicit", max_length=20)
    confidence_score: float = Field(default=0.75, ge=0.0, le=1.0)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: Any) -> str:
        cleaned = _clean_text(value, max_len=160)
        if not cleaned:
            raise ValueError("Skill name cannot be empty.")
        return cleaned

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, value: Any) -> str:
        cleaned = _clean_text(value, max_len=100)
        if not cleaned:
            return "Other"
        return _CATEGORY_ALIASES.get(cleaned.lower(), cleaned)

    @field_validator("classification", mode="before")
    @classmethod
    def validate_classification(cls, value: Any) -> str:
        cleaned = _clean_text(value, max_len=30)
        if not cleaned:
            return "Unspecified"
        return _CLASSIFICATION_LOOKUP.get(cleaned.lower(), "Unspecified")

    @field_validator("expected_proficiency", mode="before")
    @classmethod
    def validate_proficiency(cls, value: Any) -> str:
        cleaned = _clean_text(value, max_len=30)
        if not cleaned:
            return "Unspecified"
        return _PROFICIENCY_LOOKUP.get(cleaned.lower(), "Unspecified")

    @field_validator("evidence", mode="before")
    @classmethod
    def validate_evidence(cls, value: Any) -> Optional[str]:
        return _clean_text(value, max_len=500)

    @field_validator("source_type", mode="before")
    @classmethod
    def validate_source_type(cls, value: Any) -> str:
        cleaned = _clean_text(value, max_len=20)
        if not cleaned:
            return "explicit"
        return _SOURCE_TYPE_LOOKUP.get(cleaned.lower(), "explicit")

    @model_validator(mode="after")
    def enforce_classification_and_priority_rules(self) -> "ClassifiedSkillItem":
        # Normalize skill name via existing Feature 17 dictionary
        norm_name, orig_name, canon_cat = normalize_skill_name(self.name)
        self.name = norm_name
        if orig_name and not self.original_name:
            self.original_name = orig_name
        if self.category == "Other" and canon_cat:
            self.category = _CATEGORY_ALIASES.get(canon_cat.lower(), canon_cat)

        # Enforce priority score bounds per classification
        if self.classification == "Unspecified":
            self.priority_score = None
        else:
            low, high, default_score = _PRIORITY_BOUNDS[self.classification]
            if self.priority_score is None:
                self.priority_score = default_score
            else:
                self.priority_score = max(low, min(high, int(self.priority_score)))

        self.priority_level = _PRIORITY_LEVEL_MAP[self.classification]
        return self


def deduplicate_classified_skills(
    items: List[ClassifiedSkillItem],
    max_items: int = 80,
) -> List[ClassifiedSkillItem]:
    """
    Deduplicate skills by normalized lookup key and resolve conflicting statements
    deterministically: explicit beats inferred, and higher classification rank
    (Mandatory > Preferred > Optional > Unspecified) takes precedence.
    """
    by_key: Dict[str, ClassifiedSkillItem] = {}
    order: List[str] = []

    for item in items:
        key = create_lookup_key(item.name) or item.name.lower()
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = item
            order.append(key)
            continue

        existing_score = (
            1 if existing.source_type == "explicit" else 0,
            _CLASSIFICATION_RANK.get(existing.classification, 0),
            existing.priority_score or 0,
            existing.confidence_score,
        )
        candidate_score = (
            1 if item.source_type == "explicit" else 0,
            _CLASSIFICATION_RANK.get(item.classification, 0),
            item.priority_score or 0,
            item.confidence_score,
        )
        if candidate_score > existing_score:
            by_key[key] = item

    return [by_key[k] for k in order[:max_items]]


class SkillClassificationSummary(BaseModel):
    """Counts of classified skills by importance category."""

    mandatory_count: int = 0
    preferred_count: int = 0
    optional_count: int = 0
    unspecified_count: int = 0
    total_skills: int = 0


def compute_classification_summary(skills: List[ClassifiedSkillItem]) -> SkillClassificationSummary:
    counts = {"Mandatory": 0, "Preferred": 0, "Optional": 0, "Unspecified": 0}
    for skill in skills:
        counts[skill.classification] = counts.get(skill.classification, 0) + 1
    return SkillClassificationSummary(
        mandatory_count=counts["Mandatory"],
        preferred_count=counts["Preferred"],
        optional_count=counts["Optional"],
        unspecified_count=counts["Unspecified"],
        total_skills=len(skills),
    )


class SkillClassificationAIStructuredOutput(BaseModel):
    """Strict structured output contract expected from ChatOllama."""

    skills: List[ClassifiedSkillItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def dedupe_skills(self) -> "SkillClassificationAIStructuredOutput":
        self.skills = deduplicate_classified_skills(self.skills)
        return self


class JobSkillClassificationData(BaseModel):
    """API data payload for Feature 37 skill classification."""

    id: str
    job_id: str
    job_description_id: str
    classification_summary: SkillClassificationSummary
    skills: List[ClassifiedSkillItem]
    analysis_status: str
    model_used: str = ""
    cached: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def sync_summary_with_skills(self) -> "JobSkillClassificationData":
        self.classification_summary = compute_classification_summary(self.skills)
        return self


class JobSkillClassificationResponse(BaseModel):
    """Standard API envelope for skill classification."""

    success: bool
    message: str
    data: JobSkillClassificationData
