"""
Pydantic Schemas for Resume Improvement Recommendations
Phase 4 | Feature 27: Resume Improvement Recommendations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


RecommendationPriority = Literal["Critical", "High", "Medium", "Low"]
RecommendationEffort = Literal["Easy", "Medium", "Hard"]
RecommendationCategory = Literal[
    "technical_skills",
    "professional_summary",
    "project_descriptions",
    "work_experience",
    "achievements_impact",
    "ats_compatibility",
    "grammar_clarity",
    "resume_completeness",
]

CATEGORY_DISPLAY_NAMES: Dict[str, str] = {
    "technical_skills": "Technical Skills Presentation",
    "professional_summary": "Professional Summary",
    "project_descriptions": "Project Descriptions",
    "work_experience": "Work & Internship Experience",
    "achievements_impact": "Achievements & Measurable Impact",
    "ats_compatibility": "ATS Compatibility",
    "grammar_clarity": "Grammar & Clarity",
    "resume_completeness": "Resume Completeness",
}


class RecommendationItemAI(BaseModel):
    """Raw recommendation item emitted by AI LLM or rule engine."""
    title: str = Field(..., description="Short, clear title for the recommendation")
    category: str = Field(..., description="Category key or name for recommendation")
    explanation: str = Field(..., description="Detailed explanation of the problem or gap")
    reason: str = Field(..., description="Why this recommendation matters for hiring managers and ATS")
    evidence: str = Field(default="", description="Supporting quote or resume evidence")
    suggested_action: str = Field(..., description="Specific actionable steps to improve the resume")
    priority: str = Field(default="Medium", description="Critical, High, Medium, or Low")
    estimated_effort: str = Field(default="Medium", description="Easy, Medium, or Hard")
    related_feature: str = Field(default="Feature #21-#26", description="Related analysis feature source")

    @field_validator("evidence", mode="before")
    @classmethod
    def normalize_evidence(cls, v: Any) -> str:
        if isinstance(v, list):
            return "; ".join(str(x) for x in v)
        return str(v) if v is not None else ""


class ResumeRecommendationsAIOutput(BaseModel):
    """Structured LLM output for resume recommendations."""
    overall_summary: str = Field(..., description="Executive summary of the candidate's improvement roadmap")
    recommendations: List[RecommendationItemAI] = Field(default_factory=list, description="List of generated recommendations")


class RecommendationItem(BaseModel):
    """Validated, finalized recommendation item with progress tracking."""
    id: str = Field(..., description="Unique recommendation identifier (e.g. REC-TECH-01)")
    title: str = Field(..., description="Short, clear title for the recommendation")
    category: str = Field(..., description="Category key")
    category_name: str = Field(..., description="Human-readable category title")
    explanation: str = Field(..., description="Detailed explanation of the issue")
    reason: str = Field(..., description="Why this recommendation matters")
    evidence: str = Field(default="", description="Supporting resume evidence")
    suggested_action: str = Field(..., description="Actionable improvement steps")
    priority: RecommendationPriority = Field(default="Medium", description="Critical, High, Medium, or Low")
    estimated_effort: RecommendationEffort = Field(default="Medium", description="Easy, Medium, or Hard")
    related_feature: str = Field(..., description="Related analysis feature (e.g., Feature #24: ATS Compatibility)")
    is_completed: bool = Field(default=False, description="Completion status flag")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp of completion if completed")

    @field_validator("evidence", mode="before")
    @classmethod
    def normalize_evidence(cls, v: Any) -> str:
        if isinstance(v, list):
            return "; ".join(str(x) for x in v)
        return str(v) if v is not None else ""


class CoverageSummary(BaseModel):
    """Coverage indicator showing which of Features #21 to #26 were available."""
    total_features: int = Field(default=6, description="Total expected analysis features")
    available_features: List[str] = Field(default_factory=list, description="Names of available features")
    missing_features: List[str] = Field(default_factory=list, description="Names of missing/incomplete features")
    coverage_percentage: float = Field(default=0.0, description="Percentage of analysis coverage (0-100)")
    is_full_coverage: bool = Field(default=False, description="True if all 6 analyses were present")
    coverage_notes: str = Field(default="", description="Human explanation of coverage status")


class RecommendationAnalysisData(BaseModel):
    """Full payload for resume improvement recommendations."""
    id: str
    resume_id: str
    user_id: Optional[str] = None
    overall_summary: str
    total_recommendations_count: int
    completed_count: int
    pending_count: int
    completion_percentage: float
    priority_breakdown: Dict[str, int]
    category_breakdown: Dict[str, Any]
    coverage_summary: Dict[str, Any]
    recommendations: List[RecommendationItem]
    analysis_metadata: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RecommendationResponse(BaseModel):
    """Standard API response envelope for recommendations."""
    success: bool = True
    message: str = "Success"
    data: Optional[RecommendationAnalysisData] = None


class UpdateRecommendationStatusRequest(BaseModel):
    """Payload to mark recommendation completed or reopen it."""
    is_completed: bool = Field(..., description="True to mark completed, False to reopen")


class SingleRecommendationResponse(BaseModel):
    """Response when a single recommendation item is updated."""
    success: bool = True
    message: str = "Status updated successfully"
    data: Optional[Dict[str, Any]] = None
