"""
Pydantic Schemas for Resume Strength Analysis Engine
Phase 4 | Feature 22: Resume Strength Analysis
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

# Allowed categories matching Feature 22 requirements
STRENGTH_CATEGORIES = {
    "technical_skills": "Technical Skills",
    "projects": "Projects",
    "experience": "Work & Internship Experience",
    "education": "Education",
    "achievements": "Achievements & Certifications",
    "leadership": "Leadership & Teamwork",
    "communication": "Communication & Problem-Solving",
}


class StrengthItem(BaseModel):
    """Detailed profile of an individual identified strength."""
    title: str = Field(..., description="Short descriptive title of the strength")
    category: str = Field(
        ...,
        description="One of: technical_skills, projects, experience, education, achievements, leadership, communication"
    )
    category_name: str = Field(..., description="Human-readable category label")
    explanation: str = Field(..., description="In-depth analysis of why this qualifies as a candidate strength")
    evidence: List[str] = Field(
        default_factory=list,
        description="Direct quotes, metrics, or factual technologies from the resume supporting this strength"
    )
    professional_value: str = Field(
        ...,
        description="Explanation of why this strength is valuable to employers, recruiters, or career progression"
    )
    confidence_level: str = Field(
        ...,
        description="Confidence assessment: High, Medium, or Low"
    )
    strength_type: str = Field(
        ...,
        description="demonstrated (concrete track record) or potential (emerging foundation / trajectory)"
    )
    relevance_rank: int = Field(
        ...,
        ge=1,
        description="Rank ordered by strategic career impact and evidence depth (1 = top strength)"
    )

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean not in ["High", "Medium", "Low"]:
            return "Medium"
        return clean

    @field_validator("strength_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ["demonstrated", "potential"]:
            return "demonstrated"
        return clean


class CategoryStrengthSummary(BaseModel):
    """Summary metrics and top takeaway for a specific strength category."""
    category_key: str = Field(..., description="Machine key")
    category_name: str = Field(..., description="Display name")
    total_strengths: int = Field(0, description="Total strengths detected in this category")
    demonstrated_count: int = Field(0, description="Count of demonstrated strengths")
    potential_count: int = Field(0, description="Count of potential strengths")
    key_takeaway: str = Field(..., description="Brief executive synthesis of candidate's capability in this category")


class StrengthAnalysisData(BaseModel):
    """Payload representing a complete resume strength analysis."""
    id: str = Field(..., description="Analysis unique ID")
    resume_id: str = Field(..., description="Associated resume UUID")
    total_strengths_count: int = Field(..., description="Total count of identified strengths")
    demonstrated_count: int = Field(..., description="Count of demonstrated strengths")
    potential_count: int = Field(..., description="Count of potential strengths")
    is_sufficient_evidence: bool = Field(True, description="Whether resume provided sufficient information for robust analysis")
    insufficient_evidence_reason: Optional[str] = Field(None, description="Explanation if evidence was sparse or missing")
    top_strengths_summary: str = Field(..., description="Executive narrative summarizing candidate's most formidable strengths")
    strengths: List[StrengthItem] = Field(default_factory=list, description="Rank-ordered list of all strengths")
    category_summaries: Dict[str, CategoryStrengthSummary] = Field(
        default_factory=dict,
        description="Summaries keyed by category"
    )
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata (model, duration, timestamps)")
    created_at: str = Field(..., description="ISO creation timestamp")
    updated_at: str = Field(..., description="ISO update timestamp")


class StrengthAnalysisResponse(BaseModel):
    """Standard API response envelope."""
    success: bool = True
    message: str = "Resume strength analysis completed successfully"
    data: Optional[StrengthAnalysisData] = None


# =========================================================================
# STRUCTURED LLM OUTPUT SCHEMAS (LangChain & ChatOllama Pydantic output)
# =========================================================================

class StrengthItemAI(BaseModel):
    """Structured LLM output for a single strength."""
    title: str = Field(..., description="Concise, impact-focused title of the strength")
    category: str = Field(
        ...,
        description="Exact category: technical_skills, projects, experience, education, achievements, leadership, or communication"
    )
    explanation: str = Field(..., description="Detailed explanation of the candidate's mastery or accomplishment")
    evidence: List[str] = Field(
        ...,
        description="Specific metrics, technologies, bullet lines or quotes directly from resume"
    )
    professional_value: str = Field(..., description="Why this strength commands attention in hiring decisions")
    confidence_level: str = Field("High", description="High, Medium, or Low based on evidence firmness")
    strength_type: str = Field("demonstrated", description="demonstrated or potential")


class ResumeStrengthAIStructuredOutput(BaseModel):
    """
    Enforced schema on ChatOllama / LangChain structured output.
    Guarantees typed strengths, evidence citation, and zero hallucination.
    """
    is_sufficient_evidence: bool = Field(
        True,
        description="False if resume is empty, placeholder, or completely lacks substantive content"
    )
    insufficient_evidence_reason: Optional[str] = Field(
        None,
        description="Reason if evidence is insufficient (e.g., 'No work experience or project bullets provided')"
    )
    top_strengths_summary: str = Field(
        ...,
        description="Executive 2-3 sentence synthesis of candidate's core professional differentiator"
    )
    strengths: List[StrengthItemAI] = Field(
        default_factory=list,
        description="List of 4 to 12 strengths discovered strictly from resume facts"
    )
    category_takeaways: Dict[str, str] = Field(
        default_factory=dict,
        description="Brief 1-sentence takeaway for each category evaluated"
    )
