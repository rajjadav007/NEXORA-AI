"""
Pydantic Schemas for Personal Information Extraction
Phase 3 | Feature 13: Personal Information Extraction
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class LocationData(BaseModel):
    """Structured location details."""
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class PersonalInformationData(BaseModel):
    """Structured candidate personal information payload."""
    id: Optional[str] = None
    resume_id: str
    user_id: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = None
    location: Optional[LocationData] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    other_urls: List[str] = Field(default_factory=list)
    extraction_status: str = "completed"
    confidence: Dict[str, float] = Field(default_factory=dict)
    is_manually_edited: bool = False
    manually_edited_fields: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "resume_id": "a5e8e821-6893-4a7b-a25d-4f1082c9e7bc",
                "full_name": "Raj Jadav",
                "first_name": "Raj",
                "last_name": "Jadav",
                "email": "raj.jadav@example.com",
                "phone": "+91 9876543210",
                "country_code": "+91",
                "location": {
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "country": "India"
                },
                "linkedin_url": "https://linkedin.com/in/rajjadav",
                "github_url": "https://github.com/rajjadav",
                "portfolio_url": None,
                "other_urls": [],
                "extraction_status": "completed",
                "confidence": {
                    "full_name": 0.98,
                    "email": 1.0,
                    "phone": 0.95,
                    "location": 0.85
                },
                "is_manually_edited": False
            }
        }
    )


class PersonalInformationResponse(BaseModel):
    """Standardized API response envelope for Personal Information."""
    success: bool = True
    message: str = "Personal information retrieved successfully"
    data: PersonalInformationData


class PersonalInformationUpdateRequest(BaseModel):
    """Request payload for manual user edits to personal information."""
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = None
    location: Optional[LocationData] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    other_urls: Optional[List[str]] = None

    model_config = ConfigDict(extra="ignore")
