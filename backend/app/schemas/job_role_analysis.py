"""
Job Role Extraction Pydantic Schemas
Phase 6 | Feature 35: Job Role Extraction
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.job_description import ALLOWED_EMPLOYMENT_TYPES

STANDARDIZED_ROLES = (
    "AI Engineer",
    "Machine Learning Engineer",
    "Data Scientist",
    "Data Analyst",
    "Data Engineer",
    "Software Engineer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Generative AI Engineer",
    "NLP Engineer",
    "Computer Vision Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Other",
)

SENIORITY_LEVELS = (
    "Internship",
    "Entry Level",
    "Fresher",
    "Junior",
    "Mid-Level",
    "Senior",
    "Lead",
    "Manager",
    "Director",
    "Unknown",
)

WORK_ARRANGEMENTS = (
    "Remote",
    "Hybrid",
    "On-site",
    "Unknown",
)

_STANDARDIZED_ROLE_LOOKUP = {r.lower(): r for r in STANDARDIZED_ROLES}
_SENIORITY_LOOKUP = {s.lower(): s for s in SENIORITY_LEVELS}
_WORK_ARRANGEMENT_LOOKUP = {w.lower(): w for w in WORK_ARRANGEMENTS}
_EMPLOYMENT_LOOKUP = {e.lower(): e for e in ALLOWED_EMPLOYMENT_TYPES}
_NULL_SENTINELS = {"", "null", "none", "n/a", "na", "not specified", "unspecified"}


def _clean_optional_text(value: Any, max_len: int = 255) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _NULL_SENTINELS:
        return None
    return text[:max_len]


class ExperienceLevelSchema(BaseModel):
    """Structured experience requirement extracted from a job description."""

    minimum_years: Optional[int] = Field(default=None, ge=0, le=50)
    maximum_years: Optional[int] = Field(default=None, ge=0, le=50)
    description: Optional[str] = Field(default=None, max_length=120)

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: Any) -> Optional[str]:
        return _clean_optional_text(value, max_len=120)

    @model_validator(mode="after")
    def normalize_bounds(self) -> "ExperienceLevelSchema":
        if (
            self.minimum_years is not None
            and self.maximum_years is not None
            and self.maximum_years < self.minimum_years
        ):
            self.minimum_years, self.maximum_years = self.maximum_years, self.minimum_years
        return self


class JobRoleAIStructuredOutput(BaseModel):
    """Validated structured output returned by the Ollama job role extractor."""

    job_title: Optional[str] = Field(default=None, max_length=255)
    standardized_role: str = Field(default="Other", max_length=120)
    department: Optional[str] = Field(default=None, max_length=120)
    category: Optional[str] = Field(default=None, max_length=120)
    seniority: str = Field(default="Unknown", max_length=60)
    experience_level: ExperienceLevelSchema = Field(default_factory=ExperienceLevelSchema)
    employment_type: Optional[str] = Field(default=None, max_length=60)
    work_arrangement: str = Field(default="Unknown", max_length=40)
    industry: Optional[str] = Field(default=None, max_length=120)
    responsibilities: List[str] = Field(default_factory=list)
    role_summary: Optional[str] = Field(default=None, max_length=1000)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("job_title", mode="before")
    @classmethod
    def clean_job_title(cls, value: Any) -> Optional[str]:
        return _clean_optional_text(value, max_len=255)

    @field_validator("department", "category", "industry", mode="before")
    @classmethod
    def clean_short_optional(cls, value: Any) -> Optional[str]:
        return _clean_optional_text(value, max_len=120)

    @field_validator("role_summary", mode="before")
    @classmethod
    def clean_role_summary(cls, value: Any) -> Optional[str]:
        return _clean_optional_text(value, max_len=1000)

    @field_validator("standardized_role", mode="before")
    @classmethod
    def normalize_standardized_role(cls, value: Any) -> str:
        cleaned = _clean_optional_text(value, max_len=120)
        if not cleaned or cleaned.lower() == "unknown":
            return "Other"
        return _STANDARDIZED_ROLE_LOOKUP.get(cleaned.lower(), cleaned)

    @field_validator("seniority", mode="before")
    @classmethod
    def normalize_seniority(cls, value: Any) -> str:
        cleaned = _clean_optional_text(value, max_len=60)
        if not cleaned:
            return "Unknown"
        return _SENIORITY_LOOKUP.get(cleaned.lower(), "Unknown")

    @field_validator("work_arrangement", mode="before")
    @classmethod
    def normalize_work_arrangement(cls, value: Any) -> str:
        cleaned = _clean_optional_text(value, max_len=40)
        if not cleaned:
            return "Unknown"
        normalized = cleaned.lower().replace("onsite", "on-site")
        return _WORK_ARRANGEMENT_LOOKUP.get(normalized, "Unknown")

    @field_validator("employment_type", mode="before")
    @classmethod
    def normalize_employment_type(cls, value: Any) -> Optional[str]:
        cleaned = _clean_optional_text(value, max_len=60)
        if not cleaned:
            return None
        if cleaned.lower() == "unknown":
            return "Unknown"
        return _EMPLOYMENT_LOOKUP.get(cleaned.lower(), cleaned)

    @field_validator("responsibilities", mode="before")
    @classmethod
    def clean_responsibilities(cls, value: Any) -> List[str]:
        if not isinstance(value, list):
            return []
        seen = set()
        items: List[str] = []
        for entry in value:
            text = str(entry).strip()
            if not text or text.lower() in _NULL_SENTINELS:
                continue
            key = text.lower()
            if key not in seen:
                seen.add(key)
                items.append(text[:300])
            if len(items) >= 15:
                break
        return items


class JobRoleAnalysisData(BaseModel):
    """API representation of persisted job role extraction results."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_description_id: str
    job_title: Optional[str] = None
    standardized_role: str
    department: Optional[str] = None
    category: Optional[str] = None
    seniority: str
    experience_level: ExperienceLevelSchema
    employment_type: Optional[str] = None
    work_arrangement: str
    industry: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    role_summary: Optional[str] = None
    confidence_score: float
    analysis_status: str = "COMPLETED"
    explicit_facts: Dict[str, Any] = Field(default_factory=dict)
    inferred_fields: List[str] = Field(default_factory=list)
    model_used: str
    cached: bool = False
    created_at: datetime
    updated_at: datetime


class JobRoleAnalysisResponse(BaseModel):
    success: bool = True
    message: str
    data: JobRoleAnalysisData
