"""
Job Description Report Pydantic Schemas
Phase 6 | Feature 38: Job Description Report
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.job_requirement_analysis import (
    EducationRequirementSchema,
    ExperienceRequirementSchema,
    ExtractedRequirementItem,
)
from app.schemas.job_skill_classification import (
    ClassifiedSkillItem,
    SkillClassificationSummary,
)

COMPLEXITY_LEVELS = ("Beginner", "Intermediate", "Advanced", "Expert")
_COMPLEXITY_LOOKUP = {level.lower(): level for level in COMPLEXITY_LEVELS}


class JobReportOverview(BaseModel):
    job_title: str
    company_name: str
    location: Optional[str] = None
    employment_type: Optional[str] = None
    work_arrangement: str = "Unknown"
    seniority_level: str = "Unknown"
    experience_requirements: Optional[str] = None
    industry: Optional[str] = None
    job_description_summary: Optional[str] = None
    source_type: str = "manual"
    source_url: Optional[str] = None


class JobReportRoleAnalysis(BaseModel):
    standardized_role: str = "Other"
    department: Optional[str] = None
    category: Optional[str] = None
    seniority_level: str = "Unknown"
    role_summary: Optional[str] = None
    main_responsibilities: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    confidence_score: float = 0.0


class JobReportTechnicalRequirements(BaseModel):
    programming_languages: List[ExtractedRequirementItem] = Field(default_factory=list)
    ai_and_machine_learning: List[ExtractedRequirementItem] = Field(default_factory=list)
    frameworks_and_libraries: List[ExtractedRequirementItem] = Field(default_factory=list)
    tools_and_platforms: List[ExtractedRequirementItem] = Field(default_factory=list)
    databases: List[ExtractedRequirementItem] = Field(default_factory=list)
    cloud_technologies: List[ExtractedRequirementItem] = Field(default_factory=list)
    other_technical_skills: List[ExtractedRequirementItem] = Field(default_factory=list)


class JobReportSkillClassification(BaseModel):
    summary: SkillClassificationSummary = Field(default_factory=SkillClassificationSummary)
    mandatory: List[ClassifiedSkillItem] = Field(default_factory=list)
    preferred: List[ClassifiedSkillItem] = Field(default_factory=list)
    optional: List[ClassifiedSkillItem] = Field(default_factory=list)
    unspecified: List[ClassifiedSkillItem] = Field(default_factory=list)


class JobReportComplexityAnalysis(BaseModel):
    level: str = Field(default="Intermediate", max_length=30)
    explanation: str = Field(default="", max_length=600)
    is_ai_estimate: bool = True
    disclaimer: str = (
        "AI-generated estimate based on extracted job requirements; not an official employer rating."
    )

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, value: Any) -> str:
        if not value:
            return "Intermediate"
        return _COMPLEXITY_LOOKUP.get(str(value).strip().lower(), "Intermediate")

    @field_validator("explanation", mode="before")
    @classmethod
    def clean_explanation(cls, value: Any) -> str:
        return str(value or "").strip()[:600]


class JobReportEligibilityCriteria(BaseModel):
    fresher_eligible: Optional[bool] = None
    required_experience: Optional[str] = None
    required_education: Optional[str] = None
    mandatory_qualifications: List[str] = Field(default_factory=list)
    important_technical_requirements: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "General role eligibility summary based on the job description; does not evaluate any specific candidate."
    )


class JobReportInsightItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    detail: str = Field(..., min_length=1, max_length=500)
    source_type: str = Field(default="inferred", max_length=20)


class JobReportAIStructuredOutput(BaseModel):
    """Structured output returned by ChatOllama for complexity analysis & job insights."""

    complexity_analysis: JobReportComplexityAnalysis
    ai_insights: List[JobReportInsightItem] = Field(default_factory=list, max_length=8)


class JobDescriptionReportData(BaseModel):
    """Complete validated Job Description Report payload."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    job_description_id: str
    report_version: str = "1.0"
    version_number: int = 1
    overview: JobReportOverview
    role_analysis: JobReportRoleAnalysis
    technical_requirements: JobReportTechnicalRequirements
    skill_classification: JobReportSkillClassification
    education: EducationRequirementSchema
    experience: ExperienceRequirementSchema
    soft_skills: List[ExtractedRequirementItem] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    complexity_analysis: JobReportComplexityAnalysis
    eligibility_criteria: JobReportEligibilityCriteria
    ai_insights: List[JobReportInsightItem] = Field(default_factory=list)
    analysis_status: str = "COMPLETED"
    model_used: str = ""
    cached: bool = False
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


class JobDescriptionReportResponse(BaseModel):
    success: bool
    message: str
    data: JobDescriptionReportData
