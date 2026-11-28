"""
Job Match Pydantic Schemas
Phase 7 | Feature 39: Resume-to-Job Matching Engine
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


MatchCategory = Literal["Matched", "Partially Matched", "Missing", "Not Verifiable"]


class JobMatchRequest(BaseModel):
    """Request payload to compute or retrieve a resume-to-job match."""

    resume_id: str = Field(..., min_length=1, description="UUID of the analyzed resume")
    job_description_id: str = Field(..., min_length=1, description="UUID of the analyzed job description")
    regenerate: bool = Field(
        default=False,
        description="Force recomputation even if an up-to-date cached match exists",
    )


class RequirementMatchItem(BaseModel):
    """Single evaluated requirement with classification, category, and resume evidence."""

    requirement: str
    category: str  # technical_skill, experience, education, certification, project, soft_skill, domain_knowledge, other
    importance: str = "Unspecified"  # Mandatory, Preferred, Optional, Unspecified
    status: MatchCategory
    score_ratio: float = Field(..., ge=0.0, le=1.0)
    matched_with: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    reason: Optional[str] = None


class CategoryScoreBreakdown(BaseModel):
    """Transparent score breakdown for one evaluation category."""

    category: str
    label: str
    configured_weight: float = Field(..., ge=0.0, le=1.0)
    applied_weight: float = Field(..., ge=0.0, le=1.0)
    raw_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    weighted_contribution: float = Field(default=0.0, ge=0.0, le=100.0)
    available: bool = True
    matched_count: int = 0
    partial_count: int = 0
    missing_count: int = 0
    not_verifiable_count: int = 0
    notes: Optional[str] = None


class ScoreBreakdownSchema(BaseModel):
    """Complete weighted scoring breakdown normalized to 0-100."""

    overall_score: float = Field(..., ge=0.0, le=100.0)
    total_configured_weight: float = 1.0
    total_applied_weight: float = Field(..., ge=0.0, le=1.0)
    normalization_factor: float = Field(..., ge=0.0)
    categories: Dict[str, CategoryScoreBreakdown] = Field(default_factory=dict)


class ExperienceMatchSummary(BaseModel):
    """Comparison of candidate experience against job experience requirements."""

    status: MatchCategory
    candidate_total_months: Optional[int] = None
    candidate_total_years: Optional[float] = None
    required_min_years: Optional[int] = None
    required_max_years: Optional[int] = None
    fresher_eligible: Optional[bool] = None
    relevant_roles: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str


class EducationMatchSummary(BaseModel):
    """Comparison of candidate education against job education requirements."""

    status: MatchCategory
    required_degree: Optional[str] = None
    required_fields: List[str] = Field(default_factory=list)
    candidate_degrees: List[Dict[str, Any]] = Field(default_factory=list)
    certifications_matched: List[str] = Field(default_factory=list)
    certifications_missing: List[str] = Field(default_factory=list)
    summary: str


class RelevantProjectItem(BaseModel):
    """Candidate project evaluated for relevance to the target job."""

    project_id: str
    project_title: str
    project_category: str
    relevance_score: float = Field(..., ge=0.0, le=100.0)
    matched_skills: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)


class JobMatchSummaryCounts(BaseModel):
    matched_count: int = 0
    partially_matched_count: int = 0
    missing_count: int = 0
    not_verifiable_count: int = 0
    total_requirements: int = 0


class JobMatchData(BaseModel):
    """Full structured candidate-to-job match result."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    resume_id: str
    job_description_id: str
    resume_filename: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None

    overall_match_score: float = Field(..., ge=0.0, le=100.0)
    score_breakdown: ScoreBreakdownSchema
    summary_counts: JobMatchSummaryCounts

    matching_skills: List[RequirementMatchItem] = Field(default_factory=list)
    partially_matching_skills: List[RequirementMatchItem] = Field(default_factory=list)
    missing_skills: List[RequirementMatchItem] = Field(default_factory=list)

    matched_requirements: List[RequirementMatchItem] = Field(default_factory=list)
    partially_matched_requirements: List[RequirementMatchItem] = Field(default_factory=list)
    missing_requirements: List[RequirementMatchItem] = Field(default_factory=list)
    not_verifiable_requirements: List[RequirementMatchItem] = Field(default_factory=list)

    experience_match: ExperienceMatchSummary
    education_match: EducationMatchSummary
    relevant_projects: List[RelevantProjectItem] = Field(default_factory=list)

    strengths: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    evidence_from_resume: Dict[str, Any] = Field(default_factory=dict)

    calculation_version: str
    version_number: int = 1
    cached: bool = False
    created_at: datetime
    updated_at: datetime


class JobMatchResponse(BaseModel):
    success: bool = True
    message: str
    data: JobMatchData


class JobMatchListItem(BaseModel):
    id: str
    resume_id: str
    job_description_id: str
    resume_filename: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    overall_match_score: float
    calculation_version: str
    version_number: int
    created_at: datetime
    updated_at: datetime


class JobMatchListResponse(BaseModel):
    success: bool = True
    message: str
    data: List[JobMatchListItem]
    total: int
