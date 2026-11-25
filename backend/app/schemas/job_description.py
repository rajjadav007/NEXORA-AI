"""
Job Description Pydantic Schemas
Phase 6 | Feature 33: Job Description Input
"""

from datetime import datetime
from typing import Annotated, List, Optional
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

    @field_validator("location", mode="before")
    @classmethod
    def normalize_location(cls, value: Optional[str]) -> Optional[str]:
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
    created_at: datetime
    updated_at: datetime


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
