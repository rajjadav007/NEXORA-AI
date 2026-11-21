"""
Pydantic Schemas for Achievement Analysis Engine
Phase 4 | Feature 26: Achievement Analysis
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

ACHIEVEMENT_CATEGORIES = {
    "experience": "Work & Internship Experience",
    "academic_projects": "Academic Projects",
    "projects": "Personal & Professional Projects",
    "competitions": "Hackathons & Competitions",
    "awards": "Awards & Recognitions",
    "certifications": "Certifications",
    "leadership": "Leadership & Volunteering",
}

VALID_IMPACT_LEVELS = ["High", "Medium", "Low"]
VALID_QUALITY_RATINGS = ["Strong", "Moderate", "Weak"]


class MeasurableMetrics(BaseModel):
    """Specific measurable parameters extracted from achievement."""
    percentages: List[str] = Field(default_factory=list, description="Percentages like '45%', '2x'")
    numbers: List[str] = Field(default_factory=list, description="Numbers like '3M requests', '15 engineers'")
    time_saved: List[str] = Field(default_factory=list, description="Time metrics like '10 hours/week', '60% faster'")
    users_impacted: List[str] = Field(default_factory=list, description="User scale like '500k DAU', '100+ clients'")
    performance_gain: List[str] = Field(default_factory=list, description="Latency, throughput, scale gains")


class AchievementItem(BaseModel):
    """Detailed profile of an analyzed achievement."""
    id: str = Field(..., description="Unique achievement identifier")
    title: str = Field(..., description="Concise, action-focused title of the accomplishment")
    category: str = Field(
        ...,
        description="One of: experience, academic_projects, projects, competitions, awards, certifications, leadership"
    )
    category_name: str = Field(..., description="Human-readable category label")
    original_statement: str = Field(..., description="Exact original statement or bullet from resume")
    is_quantified: bool = Field(..., description="Whether achievement includes measurable metrics or outcomes")
    measurable_metrics: MeasurableMetrics = Field(
        default_factory=MeasurableMetrics,
        description="Detailed breakdown of detected numbers, percentages, and scale"
    )
    has_verified_metrics: bool = Field(True, description="Whether metrics are corroborated by resume evidence")
    missing_metrics_note: Optional[str] = Field(
        None,
        description="Explanation if achievement lacks measurable impact and how it could be quantified"
    )
    evidence: List[str] = Field(default_factory=list, description="Exact quotes and phrases from resume supporting this")
    impact_level: str = Field("Medium", description="High, Medium, or Low impact")
    professional_relevance: str = Field("High", description="High, Medium, or Low relevance to career trajectory")
    quality_rating: str = Field("Moderate", description="Strong, Moderate, or Weak")
    suggested_statement: str = Field(
        ...,
        description="Improved statement following Google X-Y-Z formula while strictly preserving original facts"
    )
    explanation: str = Field(..., description="Analysis of why this accomplishment stands out or how it can be upgraded")

    @field_validator("impact_level")
    @classmethod
    def validate_impact(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean not in VALID_IMPACT_LEVELS:
            return "Medium"
        return clean

    @field_validator("quality_rating")
    @classmethod
    def validate_quality(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean not in VALID_QUALITY_RATINGS:
            return "Moderate"
        return clean


class CategoryAchievementSummary(BaseModel):
    """Quantification metrics and highlight for a specific category."""
    category_key: str = Field(..., description="Machine category key")
    category_name: str = Field(..., description="Display category name")
    total_count: int = Field(0, description="Total accomplishments in this category")
    quantified_count: int = Field(0, description="Count of quantified accomplishments")
    unquantified_count: int = Field(0, description="Count of non-quantified accomplishments")
    top_highlight: str = Field(..., description="Top notable takeaway for this category")


class RubricBreakdown(BaseModel):
    """Transparent scoring rubric components summing to 100 points."""
    quantification_rate_score: float = Field(..., description="Points earned from percentage of quantified statements (max 35)")
    impact_magnitude_score: float = Field(..., description="Points earned from high-impact business/system outcomes (max 25)")
    cross_category_diversity_score: float = Field(..., description="Points earned from achievements across multiple areas (max 15)")
    action_clarity_score: float = Field(..., description="Points earned from strong action-verb formulation (max 15)")
    metric_verification_fidelity_score: float = Field(..., description="Points earned from verified factual grounding (max 10)")
    total_score: int = Field(..., ge=0, le=100, description="Overall Achievement Quality Score")


class AchievementAnalysisData(BaseModel):
    """Complete payload for resume achievement analysis."""
    id: str = Field(..., description="Analysis unique ID")
    resume_id: str = Field(..., description="Associated resume UUID")
    achievement_score: int = Field(..., ge=0, le=100, description="Overall Achievement Quality Score (0-100)")
    score_grade: str = Field(..., description="'Exceptional', 'Strong', 'Moderate', or 'Needs Quantification'")
    executive_summary: str = Field(..., description="Executive narrative assessing candidate's accomplishments and impact presentation")
    total_achievements_count: int = Field(..., description="Total achievements evaluated")
    quantified_count: int = Field(..., description="Count of achievements with measurable numbers/metrics")
    unquantified_count: int = Field(..., description="Count of achievements lacking measurable numbers")
    quantification_rate: float = Field(..., description="Percentage of achievements that are quantified (0.0 to 100.0)")
    achievements: List[AchievementItem] = Field(default_factory=list, description="Detailed list of all evaluated achievements")
    category_breakdown: Dict[str, CategoryAchievementSummary] = Field(
        default_factory=dict,
        description="Category summaries"
    )
    rubric_breakdown: RubricBreakdown = Field(..., description="Transparent rubric score components")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
    created_at: str = Field(..., description="ISO creation timestamp")
    updated_at: str = Field(..., description="ISO update timestamp")


class AchievementAnalysisResponse(BaseModel):
    """Standard API response envelope."""
    success: bool = True
    message: str = "Resume achievement analysis completed successfully"
    data: Optional[AchievementAnalysisData] = None


# =========================================================================
# STRUCTURED LLM OUTPUT SCHEMAS (LangChain & ChatOllama Pydantic output)
# =========================================================================

class AchievementItemAI(BaseModel):
    title: str = Field(..., description="Impactful title of the accomplishment")
    category: str = Field(
        ...,
        description="Exact key: experience, academic_projects, projects, competitions, awards, certifications, or leadership"
    )
    original_statement: str = Field(..., description="Exact statement or bullet line from the resume")
    is_quantified: bool = Field(..., description="True if statement includes numbers, percentages, or measurable scale")
    percentages: List[str] = Field(default_factory=list, description="Extracted percentages")
    numbers: List[str] = Field(default_factory=list, description="Extracted counts, throughput, financial figures")
    time_saved: List[str] = Field(default_factory=list, description="Time savings or velocity improvements")
    users_impacted: List[str] = Field(default_factory=list, description="User scale or customer impact numbers")
    performance_gain: List[str] = Field(default_factory=list, description="Latency or architectural efficiency metrics")
    has_verified_metrics: bool = Field(True, description="True if metrics are directly cited from resume facts")
    missing_metrics_note: Optional[str] = Field(None, description="Note on what metric could have been included if unquantified")
    evidence: List[str] = Field(..., description="Quotes or factual keywords from resume directly supporting this")
    impact_level: str = Field("Medium", description="High, Medium, or Low")
    professional_relevance: str = Field("High", description="High, Medium, or Low")
    quality_rating: str = Field("Moderate", description="Strong, Moderate, or Weak")
    suggested_statement: str = Field(
        ...,
        description="Google X-Y-Z formula rewrite ('Accomplished [X] as measured by [Y] by doing [Z]') strictly preserving original facts"
    )
    explanation: str = Field(..., description="Detailed explanation of the achievement's career and recruiter value")


class ResumeAchievementAIStructuredOutput(BaseModel):
    """
    Enforced schema on ChatOllama / LangChain structured output.
    Guarantees typed accomplishments, metric extraction, and fact-preserving rewrites.
    """
    executive_summary: str = Field(
        ...,
        description="2-3 sentence executive assessment of the candidate's quantified track record and accomplishments"
    )
    achievements: List[AchievementItemAI] = Field(
        default_factory=list,
        description="List of 3 to 12 accomplishments extracted from experience, projects, hackathons, awards, and certifications"
    )
    category_highlights: Dict[str, str] = Field(
        default_factory=dict,
        description="Key takeaway highlight for each category"
    )
