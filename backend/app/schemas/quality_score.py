"""
Pydantic Schemas for Resume Quality Score Engine
Phase 4 | Feature 21: Resume Quality Score
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class CategoryScoreDetail(BaseModel):
    """Granular score breakdown for an individual evaluation category."""
    category_name: str = Field(..., description="Human-readable category name")
    category_key: str = Field(..., description="Machine-readable key")
    score: float = Field(..., ge=0.0, description="Raw score awarded to category")
    max_score: float = Field(..., gt=0.0, description="Maximum possible score for category")
    weight_percentage: float = Field(..., gt=0.0, description="Category percentage weight in overall score")
    score_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of max score achieved (0-100)")
    rating: str = Field(..., description="Performance level: Excellent, Good, Average, Needs Improvement")
    explanation: str = Field(..., description="Detailed diagnostic rationale for this category's score")
    strengths: List[str] = Field(default_factory=list, description="Specific strengths observed in this category")
    improvements: List[str] = Field(default_factory=list, description="Targeted recommendations for this category")


class QualityScoreData(BaseModel):
    """Full quality score evaluation data payload."""
    id: str = Field(..., description="Evaluation unique identifier")
    resume_id: str = Field(..., description="Associated resume ID")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall resume quality score (0-100)")
    rating_level: str = Field(..., description="Overall rating: Exceptional, Strong, Good, Needs Improvement, Critical Gaps")
    category_scores: Dict[str, CategoryScoreDetail] = Field(..., description="Granular scores for all 8 categories")
    category_explanations: Dict[str, str] = Field(..., description="Explanations keyed by category")
    strengths: List[str] = Field(default_factory=list, description="Key overall strengths identified in the resume")
    missing_information: List[str] = Field(default_factory=list, description="Critical information missing or under-documented")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Actionable suggestions to improve resume impact")
    rubric_version: str = Field(default="1.0.0", description="Scoring rubric version used")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as model, timing, timestamp")
    created_at: str = Field(..., description="Creation ISO timestamp")
    updated_at: str = Field(..., description="Last updated ISO timestamp")


class QualityScoreResponse(BaseModel):
    """Standard API response for quality score operations."""
    success: bool = True
    message: str = "Resume quality score calculated successfully"
    data: Optional[QualityScoreData] = None


class QualityScoreAnalyzeRequest(BaseModel):
    """Optional request payload for manual triggering of quality score analysis."""
    force_recalculate: bool = Field(False, description="Whether to bypass cached scores and re-evaluate with LLM")


# =========================================================================
# STRUCTURED LLM OUTPUT SCHEMAS (LangChain & ChatOllama Pydantic output)
# =========================================================================

class CategoryEvaluationAI(BaseModel):
    """LLM evaluation for one category."""
    score_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score ratio between 0.0 (completely missing/poor) and 1.0 (outstanding/exceptional)"
    )
    explanation: str = Field(
        ...,
        description="Clear, evidence-based diagnostic explanation (2-4 sentences) evaluating relevance and quality"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="1-3 concise observations of what candidate did well in this category"
    )
    improvements: List[str] = Field(
        default_factory=list,
        description="1-3 concise, actionable improvements candidate should make"
    )

    @field_validator("score_ratio")
    @classmethod
    def clamp_ratio(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))


class ResumeQualityAIStructuredOutput(BaseModel):
    """
    Predictable structured output schema enforced on ChatOllama / LangChain.
    Covers all 8 evaluation categories plus global synthesis.
    """
    completeness: CategoryEvaluationAI = Field(
        ...,
        description="Completeness evaluation: presence and depth of all essential resume sections"
    )
    professional_summary: CategoryEvaluationAI = Field(
        ...,
        description="Professional summary evaluation: clarity of career identity, value proposition, conciseness"
    )
    technical_skills: CategoryEvaluationAI = Field(
        ...,
        description="Technical skills evaluation: categorization, relevance, modern tech stack, breadth vs depth"
    )
    work_experience: CategoryEvaluationAI = Field(
        ...,
        description="Work experience evaluation: action verbs, quantified metrics, career progression, scope"
    )
    project_descriptions: CategoryEvaluationAI = Field(
        ...,
        description="Project descriptions evaluation: problem statement, technologies used, outcomes, technical rigor"
    )
    education: CategoryEvaluationAI = Field(
        ...,
        description="Education evaluation: degree, major, institution, graduation dates, academic distinction"
    )
    achievements: CategoryEvaluationAI = Field(
        ...,
        description="Achievements & certifications evaluation: awards, competitions, industry certs, publications"
    )
    content_clarity: CategoryEvaluationAI = Field(
        ...,
        description="Content clarity evaluation: formatting, readability, conciseness, avoiding length padding"
    )
    top_strengths: List[str] = Field(
        default_factory=list,
        description="3-5 standout strengths of this resume"
    )
    missing_critical_information: List[str] = Field(
        default_factory=list,
        description="Key pieces of missing or incomplete information that recruiters need"
    )
    priority_improvements: List[str] = Field(
        default_factory=list,
        description="3-6 concrete, prioritized, high-impact improvements to boost quality score"
    )
