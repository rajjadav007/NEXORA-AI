"""
Pydantic Schemas for Education Analysis
Phase 3 | Feature 14: Education Analysis
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class GradeData(BaseModel):
    """Structured academic grade information."""
    value: Optional[Union[float, str]] = None
    type: Optional[str] = None  # CGPA, GPA, Percentage, Classification
    scale: Optional[Union[float, int]] = None
    raw_grade: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class EducationEntryData(BaseModel):
    """Structured academic degree/qualification record."""
    id: Optional[str] = None
    resume_id: str
    user_id: Optional[str] = None
    degree: Optional[str] = None
    normalized_degree: Optional[str] = None
    degree_level: Optional[str] = None
    field_of_study: Optional[str] = None
    specialization: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    graduation_status: str = "completed"  # completed, ongoing, expected, discontinued
    grade: Optional[GradeData] = None
    achievements: List[str] = Field(default_factory=list)
    coursework: List[str] = Field(default_factory=list)
    honors: List[str] = Field(default_factory=list)
    source_evidence: List[str] = Field(default_factory=list)
    extraction_confidence: Optional[float] = None
    is_manually_edited: bool = False
    manually_edited_fields: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "degree": "Bachelor of Computer Applications",
                "normalized_degree": "Bachelor of Computer Applications",
                "degree_level": "undergraduate",
                "field_of_study": "Computer Applications",
                "specialization": None,
                "institution": "Example University",
                "location": "India",
                "start_date": "2023",
                "end_date": "2026",
                "graduation_status": "ongoing",
                "grade": {
                    "value": 7.47,
                    "type": "CGPA",
                    "scale": 10,
                    "raw_grade": "7.47/10"
                },
                "achievements": [],
                "coursework": ["Data Structures", "Web Development"],
                "honors": [],
                "source_evidence": ["BCA in Computer Applications, Example University"],
                "extraction_confidence": 0.95,
                "is_manually_edited": False
            }
        }
    )


class EducationListResponse(BaseModel):
    """Response envelope for a list of education entries."""
    success: bool = True
    message: str = "Education records retrieved successfully"
    data: List[EducationEntryData] = Field(default_factory=list)
    total: int = 0
    total_count: Optional[int] = None
    extraction_status: str = "completed"

    def model_post_init(self, __context: Any) -> None:
        if self.total_count is None:
            self.total_count = self.total


class EducationSingleResponse(BaseModel):
    """Response envelope for a single education entry."""
    success: bool = True
    message: str = "Education record retrieved successfully"
    data: EducationEntryData


class EducationCreateRequest(BaseModel):
    """Request payload to add a new education entry manually."""
    degree: Optional[str] = None
    normalized_degree: Optional[str] = None
    degree_level: Optional[str] = None
    field_of_study: Optional[str] = None
    specialization: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    graduation_status: Optional[str] = "completed"
    grade: Optional[GradeData] = None
    achievements: Optional[List[str]] = None
    coursework: Optional[List[str]] = None
    honors: Optional[List[str]] = None

    model_config = ConfigDict(extra="ignore")


class EducationUpdateRequest(BaseModel):
    """Request payload to update an existing education entry."""
    degree: Optional[str] = None
    normalized_degree: Optional[str] = None
    degree_level: Optional[str] = None
    field_of_study: Optional[str] = None
    specialization: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    graduation_status: Optional[str] = None
    grade: Optional[GradeData] = None
    achievements: Optional[List[str]] = None
    coursework: Optional[List[str]] = None
    honors: Optional[List[str]] = None

    model_config = ConfigDict(extra="ignore")
