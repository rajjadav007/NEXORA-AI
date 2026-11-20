"""
Project Intelligence Pydantic Schemas
Phase 3 | Feature 18: Project Intelligence
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ProjectSkillLinkData(BaseModel):
    """Canonical skill linkage mapped from Feature #17 dictionary."""
    original_name: str = Field(..., description="Original technology mention in project text")
    canonical_id: Optional[str] = Field(None, description="Feature #17 canonical skill ID")
    canonical_name: str = Field(..., description="Feature #17 canonical name")
    category: str = Field("Other", description="Skill category")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    is_explicit: bool = Field(True, description="Whether explicitly stated in text")

    model_config = ConfigDict(from_attributes=True)


class ProjectLinkData(BaseModel):
    """External project hyperlink (GitHub, demo, website, docs)."""
    type: str = Field("github", description="github, demo, website, docs, other")
    url: str = Field(..., description="HTTP/HTTPS project link")

    model_config = ConfigDict(from_attributes=True)


class ProjectEntryData(BaseModel):
    """Structured project intelligence record."""
    id: Optional[str] = Field(None, description="Unique project UUID")
    resume_id: Optional[str] = Field(None, description="Associated resume UUID")
    project_title: str = Field(..., description="Original extracted project title")
    normalized_title: str = Field(..., description="Standardized project title")
    project_category: str = Field(
        "other",
        description="academic, personal, hackathon, research, open_source, internship, professional, freelance, other"
    )
    short_description: Optional[str] = Field(None, description="Brief summary")
    detailed_description: Optional[str] = Field(None, description="Detailed project description")
    problem_statement: Optional[str] = Field(None, description="Problem addressed")
    proposed_solution: Optional[str] = Field(None, description="Solution implemented")
    domain: Optional[str] = Field(None, description="Industry/Technical domain")

    project_role: Optional[str] = Field(None, description="Candidate role")
    team_type: str = Field("unknown", description="individual, team, unknown")
    team_size: Optional[int] = Field(None, description="Number of team members if stated")

    start_date: Optional[str] = Field(None, description="Start date (YYYY or YYYY-MM)")
    end_date: Optional[str] = Field(None, description="End date (YYYY or YYYY-MM)")
    is_ongoing: bool = Field(False, description="Whether currently active")

    technologies: List[str] = Field(default_factory=list, description="Raw technology names")
    skills: List[ProjectSkillLinkData] = Field(default_factory=list, description="Linked Feature #17 skills")
    responsibilities: List[str] = Field(default_factory=list, description="Individual contributions")
    achievements: List[str] = Field(default_factory=list, description="Awards, rankings, completions")
    measurable_outcomes: List[str] = Field(default_factory=list, description="Quantified performance results")
    project_links: List[ProjectLinkData] = Field(default_factory=list, description="Extracted URLs")

    source_section: str = Field("projects", description="Resume section source")
    source_evidence: List[str] = Field(default_factory=list, description="Verifying text snippets")

    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Evidence-backed confidence")
    extraction_method: str = Field("hybrid", description="deterministic, ai_assisted, hybrid, manual")
    review_status: str = Field("pending", description="pending, confirmed, needs_review")

    is_manually_edited: bool = Field(False, description="Manual modification protection flag")
    manually_edited_fields: List[str] = Field(default_factory=list, description="Fields edited by user")

    model_config = ConfigDict(from_attributes=True)


class ProjectCreateRequest(BaseModel):
    """Payload to create a project entry manually."""
    project_title: str = Field(..., min_length=1, max_length=255)
    project_category: Optional[str] = Field("other", max_length=50)
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    problem_statement: Optional[str] = None
    proposed_solution: Optional[str] = None
    domain: Optional[str] = None
    project_role: Optional[str] = None
    team_type: Optional[str] = "unknown"
    team_size: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_ongoing: Optional[bool] = False
    technologies: Optional[List[str]] = Field(default_factory=list)
    responsibilities: Optional[List[str]] = Field(default_factory=list)
    achievements: Optional[List[str]] = Field(default_factory=list)
    measurable_outcomes: Optional[List[str]] = Field(default_factory=list)
    project_links: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class ProjectUpdateRequest(BaseModel):
    """Payload to update an existing project entry."""
    project_title: Optional[str] = Field(None, min_length=1, max_length=255)
    project_category: Optional[str] = None
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    problem_statement: Optional[str] = None
    proposed_solution: Optional[str] = None
    domain: Optional[str] = None
    project_role: Optional[str] = None
    team_type: Optional[str] = None
    team_size: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_ongoing: Optional[bool] = None
    technologies: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    measurable_outcomes: Optional[List[str]] = None
    project_links: Optional[List[Dict[str, str]]] = None
    review_status: Optional[str] = None


class ProjectConfirmRequest(BaseModel):
    """Payload to confirm an extracted project mapping."""
    review_status: Optional[str] = Field("confirmed", description="confirmed, needs_review")


class ProjectSummaryData(BaseModel):
    """Aggregated analytical summary of candidate projects."""
    total_projects: int = Field(0, description="Total projects extracted")
    projects_by_category: Dict[str, int] = Field(default_factory=dict)
    projects_by_domain: Dict[str, int] = Field(default_factory=dict)
    unique_technologies: List[str] = Field(default_factory=list)
    unique_technologies_count: int = Field(0)
    projects_with_github: int = Field(0)
    projects_with_demo: int = Field(0)
    projects_with_measurable_outcomes: int = Field(0)
    pending_reviews: int = Field(0)
    team_projects_count: int = Field(0)
    solo_projects_count: int = Field(0)

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """API response model for list of projects."""
    success: bool = True
    message: str = "Projects retrieved successfully"
    data: List[ProjectEntryData] = Field(default_factory=list)
    summary: Optional[ProjectSummaryData] = None
    total: int = 0
    extraction_status: str = "completed"


class ProjectSingleResponse(BaseModel):
    """API response model for a single project."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[ProjectEntryData] = None
