"""
Pydantic Schemas for Resume Weakness Analysis Engine
Phase 4 | Feature 23: Resume Weakness Analysis
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

# 7 core categories required by Feature #23
WEAKNESS_CATEGORIES = {
    "technical_skills": "Technical Skills Presentation",
    "projects": "Project Descriptions",
    "experience": "Work & Internship Experience",
    "education": "Education Details",
    "achievements": "Achievements & Certifications",
    "summary": "Professional Summary",
    "clarity_relevance": "Content Clarity & Relevance",
}

VALID_PRIORITIES = ["Critical", "High", "Medium", "Low"]


class WeaknessItem(BaseModel):
    """Detailed profile of an individual identified weakness."""
    title: str = Field(..., description="Short descriptive title of the weakness")
    category: str = Field(
        ...,
        description="One of: technical_skills, projects, experience, education, achievements, summary, clarity_relevance"
    )
    category_name: str = Field(..., description="Human-readable category label")
    explanation: str = Field(..., description="In-depth analysis of the weakness and why it hinders the resume")
    evidence: List[str] = Field(
        default_factory=list,
        description="Supporting resume quotes, vague phrases, or missing bullet points from the resume"
    )
    why_it_matters: str = Field(
        ...,
        description="Explanation of why this weakness matters to recruiters, hiring managers, or ATS systems"
    )
    suggested_improvement: str = Field(
        ...,
        description="Actionable guidance and concrete examples for how the candidate can fix this weakness"
    )
    priority: str = Field(
        ...,
        description="Priority severity: Critical, High, Medium, or Low"
    )
    relevance_rank: int = Field(
        ...,
        ge=1,
        description="Rank ordered by severity and career urgency (1 = top priority weakness)"
    )
    weakness_type: str = Field(
        "vague_description",
        description="vague_description, lacks_measurable_impact, content_gap, formatting_structure, or clarity_issue"
    )

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean not in VALID_PRIORITIES:
            return "Medium"
        return clean


class MissingInformationItem(BaseModel):
    """Missing section or key detail identified separately from actual content weaknesses."""
    section: str = Field(..., description="Resume section or topic where information is missing")
    item: str = Field(..., description="Specific item or detail that is absent")
    relevance: str = Field(..., description="Why having this detail would strengthen the resume")
    impact_level: str = Field("Medium", description="High, Medium, or Low impact")
    is_optional: bool = Field(False, description="Whether this information is strictly optional for candidate level")

    @field_validator("impact_level")
    @classmethod
    def validate_impact(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean not in VALID_PRIORITIES:
            return "Medium"
        return clean


class CategoryWeaknessSummary(BaseModel):
    """Summary metrics and top recommendation for a specific weakness category."""
    category_key: str = Field(..., description="Machine category key")
    category_name: str = Field(..., description="Display category name")
    total_weaknesses: int = Field(0, description="Total weaknesses detected in this category")
    critical_count: int = Field(0, description="Count of critical priority weaknesses")
    high_count: int = Field(0, description="Count of high priority weaknesses")
    medium_count: int = Field(0, description="Count of medium priority weaknesses")
    low_count: int = Field(0, description="Count of low priority weaknesses")
    key_recommendation: str = Field(..., description="Top targeted recommendation for improving this category")


class PriorityBreakdown(BaseModel):
    """Counts of weaknesses grouped by severity priority."""
    critical: int = Field(0, description="Number of critical weaknesses")
    high: int = Field(0, description="Number of high priority weaknesses")
    medium: int = Field(0, description="Number of medium priority weaknesses")
    low: int = Field(0, description="Number of low priority weaknesses")


class WeaknessAnalysisData(BaseModel):
    """Complete payload for resume weakness analysis."""
    id: str = Field(..., description="Analysis unique ID")
    resume_id: str = Field(..., description="Associated resume UUID")
    total_weaknesses_count: int = Field(..., description="Total count of identified weaknesses")
    priority_breakdown: PriorityBreakdown = Field(..., description="Breakdown by Critical, High, Medium, Low")
    overall_summary: str = Field(..., description="Executive overview of areas needing improvement")
    weaknesses: List[WeaknessItem] = Field(default_factory=list, description="Rank-ordered list of all weaknesses")
    missing_information: List[MissingInformationItem] = Field(
        default_factory=list,
        description="Missing information items identified separately from content weaknesses"
    )
    category_summaries: Dict[str, CategoryWeaknessSummary] = Field(
        default_factory=dict,
        description="Summaries keyed by category"
    )
    analysis_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata (model, duration, timestamps)"
    )
    created_at: str = Field(..., description="ISO creation timestamp")
    updated_at: str = Field(..., description="ISO update timestamp")


class WeaknessAnalysisResponse(BaseModel):
    """Standard API response envelope."""
    success: bool = True
    message: str = "Resume weakness analysis completed successfully"
    data: Optional[WeaknessAnalysisData] = None


# =========================================================================
# STRUCTURED LLM OUTPUT SCHEMAS (LangChain & ChatOllama Pydantic output)
# =========================================================================

class WeaknessItemAI(BaseModel):
    """Structured LLM output for a single weakness."""
    title: str = Field(..., description="Concise, clear title of the weakness")
    category: str = Field(
        ...,
        description="Exact category: technical_skills, projects, experience, education, achievements, summary, or clarity_relevance"
    )
    explanation: str = Field(..., description="Detailed explanation of what makes this content weak or unclear")
    evidence: List[str] = Field(
        ...,
        description="Specific vague phrases, bullet points, or missing metrics cited directly from resume"
    )
    why_it_matters: str = Field(..., description="Why this weakness matters to recruiters, hiring managers, or ATS")
    suggested_improvement: str = Field(..., description="Concrete, actionable improvement suggestion with example phrasing")
    priority: str = Field("Medium", description="Critical, High, Medium, or Low")
    weakness_type: str = Field(
        "vague_description",
        description="One of: vague_description, lacks_measurable_impact, content_gap, formatting_structure, clarity_issue"
    )


class MissingItemAI(BaseModel):
    """Structured LLM output for missing information."""
    section: str = Field(..., description="Section or area where information is missing")
    item: str = Field(..., description="Specific piece of information that is missing")
    relevance: str = Field(..., description="Why this detail is relevant and how it helps the candidate")
    impact_level: str = Field("Medium", description="High, Medium, or Low")
    is_optional: bool = Field(False, description="Whether this is optional for the candidate's career level")


class ResumeWeaknessAIStructuredOutput(BaseModel):
    """
    Enforced schema on ChatOllama / LangChain structured output.
    Guarantees typed weaknesses, evidence citations, separate missing information, and suggested improvements.
    """
    overall_summary: str = Field(
        ...,
        description="Executive 2-3 sentence overview of the most critical resume weaknesses and areas to improve"
    )
    weaknesses: List[WeaknessItemAI] = Field(
        default_factory=list,
        description="List of 3 to 10 substantive weaknesses discovered from the resume"
    )
    missing_information: List[MissingItemAI] = Field(
        default_factory=list,
        description="List of missing details or sections, kept strictly separate from content weaknesses"
    )
    category_recommendations: Dict[str, str] = Field(
        default_factory=dict,
        description="Top recommendation for each category evaluated"
    )
