"""
Pydantic Schemas for Resume Analytics Dashboard
Phase 5 | Feature 28: Resume Analytics Dashboard
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AvailableResumeOption(BaseModel):
    """Resume descriptor for multi-resume selection dropdown."""
    id: str = Field(..., description="Resume UUID")
    filename: str = Field(..., description="Original filename")
    created_at: Optional[str] = Field(None, description="Upload timestamp")
    is_active: bool = Field(False, description="Whether this resume is currently active/selected")


class ResumeHeaderInfo(BaseModel):
    """Resume metadata, processing date, status, and multi-resume selection."""
    resume_id: str = Field(..., description="Active resume UUID")
    filename: str = Field(..., description="Original uploaded filename")
    file_type: str = Field(..., description="Document type (PDF, DOCX)")
    file_size: int = Field(..., description="Document size in bytes")
    last_analyzed_date: Optional[str] = Field(None, description="ISO timestamp of most recent analysis")
    analysis_status: str = Field(..., description="COMPLETE, PARTIAL, or NOT_ANALYZED")
    coverage_count: int = Field(0, description="Count of completed Phase 4 analyses (0-6)")
    total_features: int = Field(6, description="Total expected Phase 4 analyses (6)")
    available_features: List[str] = Field(default_factory=list, description="Names of completed analyses")
    missing_features: List[str] = Field(default_factory=list, description="Names of uncompleted analyses")
    available_resumes: List[AvailableResumeOption] = Field(default_factory=list, description="All resumes available for the user")


class MetricCard(BaseModel):
    """Summary metric card with genuine score or clear not-analyzed indication."""
    score: Optional[float] = Field(None, description="Score value (0-100) or null if unanalyzed")
    max_score: float = Field(100.0, description="Scale maximum")
    grade_or_rating: Optional[str] = Field(None, description="Text rating or grade (e.g. Exceptional, Professional, Good)")
    available: bool = Field(False, description="True if based on genuine existing analysis")
    label: str = Field(..., description="Card display title")
    description: str = Field(..., description="Explanation of what this metric reflects")


class AnalyticsSummaryCards(BaseModel):
    """The 4 core summary cards."""
    quality_score: MetricCard = Field(..., description="Overall Resume Quality Score (Feature #21)")
    ats_compatibility: MetricCard = Field(..., description="ATS Compatibility Score (Feature #24)")
    readability: MetricCard = Field(..., description="Readability / Writing Score (Feature #25)")
    content_completeness: MetricCard = Field(..., description="Content Completeness Score (Feature #21)")


class CategoryScoreBar(BaseModel):
    """Category breakdown bar item from quality scoring."""
    category_key: str
    category_name: str
    score: float
    max_score: float
    score_percentage: float
    rating: str
    weight_percentage: float


class ScoreDistributionItem(BaseModel):
    """Standardized score item across different analysis dimensions."""
    metric: str = Field(..., description="Name of the evaluated dimension")
    score: Optional[float] = Field(None, description="Raw score value or null")
    max_score: float = Field(100.0, description="Scale maximum")
    percentage: Optional[float] = Field(None, description="Percentage of scale (0-100)")
    status: str = Field(..., description="Rating, grade, or status text")
    available: bool = Field(False, description="Whether data exists")


class StrengthsVsWeaknessesOverview(BaseModel):
    """Comparison metrics for strengths vs weaknesses."""
    strengths_count: int = Field(0, description="Total identified strengths")
    weaknesses_count: int = Field(0, description="Total identified weaknesses")
    missing_info_count: int = Field(0, description="Total missing information items")
    strengths_by_category: Dict[str, int] = Field(default_factory=dict)
    weaknesses_by_category: Dict[str, int] = Field(default_factory=dict)
    weaknesses_by_priority: Dict[str, int] = Field(default_factory=dict)


class VisualAnalytics(BaseModel):
    """Visual analytics components."""
    quality_category_breakdown: List[CategoryScoreBar] = Field(default_factory=list)
    score_distribution: List[ScoreDistributionItem] = Field(default_factory=list)
    strengths_vs_weaknesses: StrengthsVsWeaknessesOverview = Field(default_factory=StrengthsVsWeaknessesOverview)


class KeyStrengthItem(BaseModel):
    """Highlight of a key resume strength."""
    title: str
    category: str
    explanation: str
    evidence: str
    professional_value: Optional[str] = None


class KeyWeaknessItem(BaseModel):
    """Highlight of an important weakness."""
    title: str
    category: str
    explanation: str
    suggested_improvement: str
    priority: str


class ImprovementAreaItem(BaseModel):
    """Actionable improvement area."""
    title: str
    category: str
    suggested_action: str
    priority: str
    estimated_effort: str


class ResumeInsights(BaseModel):
    """Actionable resume insights synthesizing Phase 4 outputs."""
    key_strengths: List[KeyStrengthItem] = Field(default_factory=list)
    important_weaknesses: List[KeyWeaknessItem] = Field(default_factory=list)
    main_improvement_areas: List[ImprovementAreaItem] = Field(default_factory=list)
    feature_summaries: Dict[str, Any] = Field(default_factory=dict)


class ResumeAnalyticsDashboardData(BaseModel):
    """Complete response payload for the Resume Analytics Dashboard."""
    resume_id: str
    resume_header: ResumeHeaderInfo
    summary_cards: AnalyticsSummaryCards
    visual_analytics: VisualAnalytics
    resume_insights: ResumeInsights
    generated_at: str
    has_any_analysis: bool


class ResumeAnalyticsDashboardResponse(BaseModel):
    """Standard API response envelope."""
    success: bool = True
    message: str = "Resume analytics dashboard retrieved successfully"
    data: Optional[ResumeAnalyticsDashboardData] = None
