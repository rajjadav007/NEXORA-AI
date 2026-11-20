"""
Pydantic Schemas for Experience Analysis
Phase 3 | Feature 15: Experience Analysis
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ExperienceEntryData(BaseModel):
    """Structured professional work experience record."""
    id: Optional[str] = None
    resume_id: str
    user_id: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: str = "full_time"  # full_time, part_time, internship, freelance, contract, apprenticeship, research, volunteer, other, unknown
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    duration_months: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list)
    technical_contributions: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    measurable_impact: List[str] = Field(default_factory=list)
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
                "company": "Example Technologies",
                "job_title": "AI Engineer Intern",
                "employment_type": "internship",
                "location": "Bengaluru, India",
                "start_date": "2025-06",
                "end_date": "2025-09",
                "is_current": False,
                "duration_months": 3,
                "responsibilities": ["Developed Python-based AI applications"],
                "technical_contributions": ["Implemented model inference pipelines"],
                "technologies": ["Python", "FastAPI", "LangChain"],
                "achievements": ["Improved inference latency by 35%"],
                "measurable_impact": ["35% latency improvement"],
                "source_evidence": ["AI Engineer Intern at Example Technologies"],
                "extraction_confidence": 0.95,
                "is_manually_edited": False,
            }
        },
    )


class ExperienceSummaryData(BaseModel):
    """Aggregate experience metrics and career summary."""
    total_experience_months: int = 0
    total_experience_years: float = 0.0
    employment_count: int = 0
    full_time_count: int = 0
    part_time_count: int = 0
    internship_count: int = 0
    freelance_count: int = 0
    contract_count: int = 0
    apprenticeship_count: int = 0
    research_count: int = 0
    volunteer_count: int = 0
    other_count: int = 0
    most_recent_role: Optional[Dict[str, Any]] = None
    identified_technologies: List[str] = Field(default_factory=list)
    career_progression_observations: List[str] = Field(default_factory=list)
    extraction_status: str = "completed"

    model_config = ConfigDict(extra="ignore")


class ExperienceListResponse(BaseModel):
    """Response envelope for a list of experience entries."""
    success: bool = True
    message: str = "Experience records retrieved successfully"
    data: List[ExperienceEntryData] = Field(default_factory=list)
    summary: Optional[ExperienceSummaryData] = None
    total: int = 0
    total_count: Optional[int] = None
    extraction_status: str = "completed"

    def model_post_init(self, __context: Any) -> None:
        if self.total_count is None:
            self.total_count = self.total


class ExperienceSingleResponse(BaseModel):
    """Response envelope for a single experience entry."""
    success: bool = True
    message: str = "Experience record retrieved successfully"
    data: ExperienceEntryData


class ExperienceCreateRequest(BaseModel):
    """Request payload to manually add an experience record."""
    company: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: Optional[str] = "full_time"
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = False
    duration_months: Optional[int] = None
    responsibilities: Optional[List[str]] = None
    technical_contributions: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    measurable_impact: Optional[List[str]] = None

    model_config = ConfigDict(extra="ignore")


class ExperienceUpdateRequest(BaseModel):
    """Request payload to update an existing experience record."""
    company: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = None
    duration_months: Optional[int] = None
    responsibilities: Optional[List[str]] = None
    technical_contributions: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    measurable_impact: Optional[List[str]] = None

    model_config = ConfigDict(extra="ignore")


class CareerProgressionItem(BaseModel):
    """Chronological progression entry."""
    company: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: str = "full_time"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    is_promotion: bool = False
    transition_type: Optional[str] = None  # promotion, lateral, new_company, initial


class CareerProgressionResponse(BaseModel):
    """Response envelope for career progression and gap analysis."""
    success: bool = True
    message: str = "Career progression retrieved successfully"
    timeline: List[CareerProgressionItem] = Field(default_factory=list)
    gaps: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    total_experience_months: int = 0
