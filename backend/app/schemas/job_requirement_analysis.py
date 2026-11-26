"""
Job Requirement Extraction Pydantic Schemas
Phase 6 | Feature 36: Job Requirement Extraction
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

IMPORTANCE_LEVELS = ("Mandatory", "Preferred", "Optional", "Unspecified")
SOURCE_TYPES = ("explicit", "inferred")
TECHNICAL_SKILL_CATEGORIES = (
    "Programming Language",
    "AI & Machine Learning",
    "Framework & Library",
    "Tool & Platform",
    "Database",
    "Other",
)

_IMPORTANCE_LOOKUP = {item.lower(): item for item in IMPORTANCE_LEVELS}
_SOURCE_TYPE_LOOKUP = {item.lower(): item for item in SOURCE_TYPES}
_TECH_CATEGORY_ALIASES = {
    "programming language": "Programming Language",
    "programming languages": "Programming Language",
    "language": "Programming Language",
    "ai & machine learning": "AI & Machine Learning",
    "ai and machine learning": "AI & Machine Learning",
    "ai/ml": "AI & Machine Learning",
    "machine learning": "AI & Machine Learning",
    "framework": "Framework & Library",
    "frameworks": "Framework & Library",
    "framework & library": "Framework & Library",
    "frameworks and libraries": "Framework & Library",
    "ai framework": "Framework & Library",
    "library": "Framework & Library",
    "tool & platform": "Tool & Platform",
    "tools & platforms": "Tool & Platform",
    "tools and platforms": "Tool & Platform",
    "tool": "Tool & Platform",
    "platform": "Tool & Platform",
    "cloud": "Tool & Platform",
    "database": "Database",
    "databases": "Database",
    "other": "Other",
}
_NULL_SENTINELS = {"", "null", "none", "n/a", "na", "not specified", "unspecified"}


def _clean_text(value: Any, max_len: int = 300) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _NULL_SENTINELS:
        return None
    return text[:max_len]


def _clean_str_list(value: Any, max_items: int = 20) -> List[str]:
    if not isinstance(value, list):
        return []
    seen = set()
    items: List[str] = []
    for entry in value:
        cleaned = _clean_text(entry, max_len=160)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            items.append(cleaned)
        if len(items) >= max_items:
            break
    return items


class ExtractedRequirementItem(BaseModel):
    """Single extracted requirement with importance classification and evidence."""

    name: str = Field(..., min_length=1, max_length=160)
    category: str = Field(default="Other", max_length=100)
    importance: str = Field(default="Unspecified", max_length=30)
    evidence: Optional[str] = Field(default=None, max_length=500)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    source_type: str = Field(default="explicit", max_length=20)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: Any) -> str:
        cleaned = _clean_text(value, max_len=160)
        if not cleaned:
            raise ValueError("Requirement name cannot be empty.")
        return cleaned

    @field_validator("category", mode="before")
    @classmethod
    def clean_category(cls, value: Any) -> str:
        cleaned = _clean_text(value, max_len=100)
        if not cleaned:
            return "Other"
        return _TECH_CATEGORY_ALIASES.get(cleaned.lower(), cleaned)

    @field_validator("importance", mode="before")
    @classmethod
    def normalize_importance(cls, value: Any) -> str:
        cleaned = _clean_text(value, max_len=30)
        if not cleaned:
            return "Unspecified"
        return _IMPORTANCE_LOOKUP.get(cleaned.lower(), "Unspecified")

    @field_validator("evidence", mode="before")
    @classmethod
    def clean_evidence(cls, value: Any) -> Optional[str]:
        return _clean_text(value, max_len=500)

    @field_validator("source_type", mode="before")
    @classmethod
    def normalize_source_type(cls, value: Any) -> str:
        cleaned = _clean_text(value, max_len=20)
        if not cleaned:
            return "explicit"
        return _SOURCE_TYPE_LOOKUP.get(cleaned.lower(), "explicit")


def _dedupe_items(items: List[ExtractedRequirementItem], max_items: int = 40) -> List[ExtractedRequirementItem]:
    seen = set()
    result: List[ExtractedRequirementItem] = []
    for item in items:
        key = (item.name.lower(), item.category.lower())
        if key not in seen:
            seen.add(key)
            result.append(item)
        if len(result) >= max_items:
            break
    return result


class EducationRequirementSchema(BaseModel):
    """Structured educational and certification requirements."""

    minimum_level: Optional[str] = Field(default=None, max_length=120)
    required_degree: Optional[str] = Field(default=None, max_length=160)
    preferred_degree: Optional[str] = Field(default=None, max_length=160)
    required_fields: List[str] = Field(default_factory=list)
    required_certifications: List[str] = Field(default_factory=list)
    preferred_certifications: List[str] = Field(default_factory=list)

    @field_validator("minimum_level", "required_degree", "preferred_degree", mode="before")
    @classmethod
    def clean_degree_fields(cls, value: Any) -> Optional[str]:
        return _clean_text(value, max_len=160)

    @field_validator(
        "required_fields",
        "required_certifications",
        "preferred_certifications",
        mode="before",
    )
    @classmethod
    def clean_list_fields(cls, value: Any) -> List[str]:
        return _clean_str_list(value)


class ExperienceRequirementSchema(BaseModel):
    """Structured experience requirements."""

    minimum_years: Optional[int] = Field(default=None, ge=0, le=50)
    maximum_years: Optional[int] = Field(default=None, ge=0, le=50)
    professional_experience: Optional[str] = Field(default=None, max_length=255)
    internship_experience: Optional[str] = Field(default=None, max_length=255)
    project_experience: Optional[str] = Field(default=None, max_length=255)
    fresher_eligible: Optional[bool] = Field(default=None)
    domain_experience: Optional[str] = Field(default=None, max_length=255)
    requirements: List[ExtractedRequirementItem] = Field(default_factory=list)

    @field_validator(
        "professional_experience",
        "internship_experience",
        "project_experience",
        "domain_experience",
        mode="before",
    )
    @classmethod
    def clean_exp_text(cls, value: Any) -> Optional[str]:
        return _clean_text(value, max_len=255)

    @model_validator(mode="after")
    def normalize_years(self) -> "ExperienceRequirementSchema":
        if (
            self.minimum_years is not None
            and self.maximum_years is not None
            and self.maximum_years < self.minimum_years
        ):
            self.minimum_years, self.maximum_years = self.maximum_years, self.minimum_years
        self.requirements = _dedupe_items(self.requirements, max_items=20)
        return self


class JobRequirementAIStructuredOutput(BaseModel):
    """Validated structured output returned by Ollama for job requirement extraction."""

    technical_skills: List[ExtractedRequirementItem] = Field(default_factory=list)
    education: EducationRequirementSchema = Field(default_factory=EducationRequirementSchema)
    experience: ExperienceRequirementSchema = Field(default_factory=ExperienceRequirementSchema)
    soft_skills: List[ExtractedRequirementItem] = Field(default_factory=list)
    domain_knowledge: List[ExtractedRequirementItem] = Field(default_factory=list)
    other_requirements: List[ExtractedRequirementItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def deduplicate_all(self) -> "JobRequirementAIStructuredOutput":
        self.technical_skills = _dedupe_items(self.technical_skills, max_items=40)
        self.soft_skills = _dedupe_items(self.soft_skills, max_items=20)
        self.domain_knowledge = _dedupe_items(self.domain_knowledge, max_items=20)
        self.other_requirements = _dedupe_items(self.other_requirements, max_items=20)
        return self


class RequirementSummaryCounts(BaseModel):
    mandatory_count: int = 0
    preferred_count: int = 0
    optional_count: int = 0
    unspecified_count: int = 0
    total_requirements: int = 0


class JobRequirementAnalysisData(BaseModel):
    """API representation of persisted job requirement extraction results."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    job_description_id: str
    technical_skills: List[ExtractedRequirementItem] = Field(default_factory=list)
    education: EducationRequirementSchema = Field(default_factory=EducationRequirementSchema)
    experience: ExperienceRequirementSchema = Field(default_factory=ExperienceRequirementSchema)
    soft_skills: List[ExtractedRequirementItem] = Field(default_factory=list)
    domain_knowledge: List[ExtractedRequirementItem] = Field(default_factory=list)
    other_requirements: List[ExtractedRequirementItem] = Field(default_factory=list)
    summary_counts: RequirementSummaryCounts = Field(default_factory=RequirementSummaryCounts)
    analysis_status: str = "COMPLETED"
    model_used: str
    cached: bool = False
    created_at: datetime
    updated_at: datetime


class JobRequirementAnalysisResponse(BaseModel):
    success: bool = True
    message: str
    data: JobRequirementAnalysisData
