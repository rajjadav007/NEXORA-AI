"""
Pydantic Schemas for Resume Improvement Tracker
Phase 5 | Feature 30: Resume Improvement Tracker
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ScoreMetricComparison(BaseModel):
    """Comparison for a single numerical score between two points in time."""
    previous_score: Optional[float] = None
    latest_score: Optional[float] = None
    delta: Optional[float] = None
    status: str = Field(
        ...,
        description="'improved', 'declined', 'unchanged', or 'no_previous_data'"
    )


class ScoreComparisonSummary(BaseModel):
    """Comparison summary across primary evaluation scores."""
    overall_score: ScoreMetricComparison
    ats_compatibility: ScoreMetricComparison
    readability: ScoreMetricComparison
    category_comparisons: Dict[str, ScoreMetricComparison] = Field(default_factory=dict)


class ImprovementTaskData(BaseModel):
    """Actionable improvement task model."""
    id: str
    resume_id: str
    title: str
    description: str = ""
    section: str = "General"
    priority: str = Field(..., description="'High', 'Medium', or 'Low'")
    status: str = Field(..., description="'Pending', 'In Progress', or 'Completed'")
    created_at: str
    completed_at: Optional[str] = None
    updated_at: str


class UpdateTaskStatusRequest(BaseModel):
    """Payload for updating task status or priority."""
    status: str = Field(..., description="Target status: 'Pending', 'In Progress', or 'Completed'")
    priority: Optional[str] = Field(None, description="Optional priority: 'High', 'Medium', 'Low'")


class ProgressOverview(BaseModel):
    """Task completion metrics vs score improvement."""
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completion_percentage: float = 0.0
    score_improvement_delta: Optional[float] = None


class TimelineEventData(BaseModel):
    """Milestone event in resume improvement timeline."""
    id: str
    resume_id: str
    event_type: str
    title: str
    description: str = ""
    event_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class AnalysisSnapshotData(BaseModel):
    """Point-in-time snapshot of resume analysis scores."""
    id: str
    resume_id: str
    version_number: int
    version_name: str
    overall_score: Optional[float] = None
    ats_score: Optional[float] = None
    readability_score: Optional[float] = None
    category_scores: Dict[str, Any] = Field(default_factory=dict)
    strengths_count: int = 0
    weaknesses_count: int = 0
    created_at: str


class VersionComparisonData(BaseModel):
    """Detailed comparison between two resume versions."""
    resume_id: str
    version_1: Dict[str, Any]
    version_2: Dict[str, Any]
    score_comparison: Dict[str, ScoreMetricComparison] = Field(default_factory=dict)
    skills_comparison: Dict[str, Any] = Field(default_factory=dict)
    content_changes: Dict[str, Any] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class ImprovementOverviewData(BaseModel):
    """Complete aggregated overview for Resume Improvement Tracker."""
    resume_id: str
    filename: str
    score_comparison: ScoreComparisonSummary
    progress_overview: ProgressOverview
    tasks: List[ImprovementTaskData] = Field(default_factory=list)
    timeline: List[TimelineEventData] = Field(default_factory=list)
    history: List[AnalysisSnapshotData] = Field(default_factory=list)
    available_versions: List[Dict[str, Any]] = Field(default_factory=list)


# --- Response Wrappers ---

class ImprovementOverviewResponse(BaseModel):
    success: bool = True
    message: str = "Improvement tracking data retrieved successfully"
    data: ImprovementOverviewData


class ImprovementHistoryResponse(BaseModel):
    success: bool = True
    message: str = "Improvement history retrieved successfully"
    data: List[AnalysisSnapshotData] = Field(default_factory=list)


class ImprovementTasksResponse(BaseModel):
    success: bool = True
    message: str = "Improvement tasks retrieved successfully"
    data: Dict[str, Any]


class SingleTaskResponse(BaseModel):
    success: bool = True
    message: str = "Task updated successfully"
    data: ImprovementTaskData


class VersionComparisonResponse(BaseModel):
    success: bool = True
    message: str = "Resume versions compared successfully"
    data: VersionComparisonData
