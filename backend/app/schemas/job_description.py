"""
Job Description Pydantic Schemas
Phase 6 | Feature 33: Job Description Input
"""

from datetime import datetime
from typing import Annotated, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

JD_MIN_LENGTH = 50
JD_MAX_LENGTH = 15000

ALLOWED_EMPLOYMENT_TYPES = (
    "Full-time",
    "Part-time",
    "Contract",
    "Internship",
    "Temporary",
    "Freelance",
)

_EMPLOYMENT_TYPE_LOOKUP = {item.lower(): item for item in ALLOWED_EMPLOYMENT_TYPES}


class JobDescriptionCreateRequest(BaseModel):
    """Request payload for creating a job description."""

    job_title: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=2, max_length=255),
    ] = Field(..., description="Target job title (2-255 characters)")

    company_name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=2, max_length=255),
    ] = Field(..., description="Hiring company name (2-255 characters)")

    description: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=JD_MIN_LENGTH,
            max_length=JD_MAX_LENGTH,
        ),
    ] = Field(
        ...,
        description=f"Full job description text ({JD_MIN_LENGTH}-{JD_MAX_LENGTH} characters)",
    )

    location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional job location (e.g., Remote, San Francisco, CA)",
    )

    employment_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional employment type",
    )

    source_url: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Optional source URL when imported from a job posting",
    )

    source_type: Literal["manual", "url"] = Field(
        default="manual",
        description="Origin of the job description (manual or url)",
    )

    experience_required: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional experience requirement extracted from posting",
    )

    salary_info: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional salary information extracted from posting",
    )

    mandatory_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)

    @field_validator("location", "source_url", "experience_required", "salary_info", mode="before")
    @classmethod
    def normalize_optional_str(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @field_validator("employment_type", mode="before")
    @classmethod
    def validate_employment_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        canonical = _EMPLOYMENT_TYPE_LOOKUP.get(cleaned.lower())
        if not canonical:
            allowed = ", ".join(ALLOWED_EMPLOYMENT_TYPES)
            raise ValueError(f"Invalid employment type. Allowed values: {allowed}")
        return canonical


class JobDescriptionData(BaseModel):
    """Serialized job description record structured for Features #34-#38."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    job_title: str
    company_name: str
    description: str
    character_count: int
    location: Optional[str] = None
    employment_type: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "manual"
    analysis_status: str = "PENDING"
    experience_required: Optional[str] = None
    salary_info: Optional[str] = None
    mandatory_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class JobDescriptionImportRequest(BaseModel):
    """Request payload for importing a job description from a public URL."""

    url: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2048),
    ] = Field(..., description="Public HTTP/HTTPS URL of the job posting")


class JobDescriptionImportPreviewData(BaseModel):
    """Extracted job fields previewed before saving."""

    source_url: str
    source_platform: str
    extraction_method: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_required: Optional[str] = None
    salary_info: Optional[str] = None
    description: str
    character_count: int
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)


class JobDescriptionImportResponse(BaseModel):
    success: bool = True
    message: str
    data: JobDescriptionImportPreviewData


class JobDescriptionCreateResponse(BaseModel):
    success: bool = True
    message: str
    data: JobDescriptionData


class JobDescriptionDetailResponse(BaseModel):
    success: bool = True
    message: str
    data: JobDescriptionData


class JobDescriptionListResponse(BaseModel):
    success: bool = True
    message: str
    total: int
    data: List[JobDescriptionData]
