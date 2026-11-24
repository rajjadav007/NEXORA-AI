"""
Pydantic Schemas for AI Resume Report
Phase 5 | Feature 31: AI Resume Report
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExecutiveSummarySection(BaseModel):
    """Section A: Executive Summary."""
    overall_assessment: str = Field(..., description="High-level narrative assessment of candidate profile.")
    main_strengths: List[str] = Field(default_factory=list, description="Top identified strengths.")
    key_weaknesses: List[str] = Field(default_factory=list, description="Primary weaknesses and gaps.")
    general_direction: str = Field(..., description="Strategic recommendations for resume enhancement.")


class QualityAssessmentSection(BaseModel):
    """Section B: Resume Quality Assessment."""
    overall_score: Optional[float] = None
    ats_compatibility_score: Optional[float] = None
    readability_score: Optional[float] = None
    content_completeness_score: Optional[float] = None
    score_explanations: Dict[str, str] = Field(default_factory=dict)
    assessment_summary: str = Field(..., description="Narrative evaluation explaining scores.")


class SkillsAssessmentSection(BaseModel):
    """Section C: Skills Assessment."""
    technical_skills: List[str] = Field(default_factory=list)
    ai_ml_skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_and_tools: List[str] = Field(default_factory=list)
    distribution_observations: str = Field(..., description="Observations regarding skill balance and depth.")
    underrepresented_skills_observation: Optional[str] = None


class ExperienceAssessmentSection(BaseModel):
    """Section D: Experience Assessment."""
    roles_reviewed_count: int = 0
    responsibilities_review: str = Field(..., description="Review of clarity and ownership in roles.")
    achievements_review: str = Field(..., description="Review of career accomplishments.")
    measurable_results_usage: str = Field(..., description="Evaluation of quantifiable outcomes and metrics.")
    professional_presentation: str = Field(..., description="Action verbs and role positioning.")


class EducationAssessmentSection(BaseModel):
    """Section E: Education Assessment."""
    degrees_reviewed: List[str] = Field(default_factory=list)
    academic_presentation: str = Field(..., description="Evaluation of academic credentials.")
    relevant_certifications: List[str] = Field(default_factory=list)


class ProjectsAssessmentSection(BaseModel):
    """Section F: Projects Assessment."""
    projects_reviewed_count: int = 0
    technical_stack: List[str] = Field(default_factory=list)
    problem_statements_clarity: str = Field(..., description="Clarity of project goals.")
    implementation_details: str = Field(..., description="Engineering rigor and architecture.")
    outcomes_and_measurable_results: str = Field(..., description="Impact, users, or metrics.")


class StrengthItem(BaseModel):
    """Section G: Prioritized Strength."""
    title: str
    section: str
    evidence: str
    impact: str


class WeaknessItem(BaseModel):
    """Section H: Weakness Item."""
    issue: str
    section: str
    severity: str = "Medium"
    recommendation: str


class ATSAssessmentSection(BaseModel):
    """Section I: ATS Assessment."""
    ats_score: Optional[float] = None
    keyword_coverage_summary: str
    formatting_issues_detected: List[str] = Field(default_factory=list)
    section_completeness: str
    actionable_improvements: List[str] = Field(default_factory=list)


class ImprovementRecommendationItem(BaseModel):
    """Section J: Improvement Recommendation."""
    title: str
    description: str
    priority: str = "Medium"  # High, Medium, Low
    section: str = "General"
    suggested_action: str


class FinalAssessmentSection(BaseModel):
    """Section K: Final Strategic Assessment."""
    overall_conclusion: str
    top_five_actions: List[str] = Field(default_factory=list)
    strategic_priorities: List[str] = Field(default_factory=list)


class ReportSections(BaseModel):
    """Composite container holding all 11 report sections."""
    executive_summary: ExecutiveSummarySection
    quality_assessment: QualityAssessmentSection
    skills_assessment: SkillsAssessmentSection
    experience_assessment: ExperienceAssessmentSection
    education_assessment: EducationAssessmentSection
    project_assessment: ProjectsAssessmentSection
    strengths: List[StrengthItem] = Field(default_factory=list)
    weaknesses: List[WeaknessItem] = Field(default_factory=list)
    ats_assessment: ATSAssessmentSection
    recommendations: List[ImprovementRecommendationItem] = Field(default_factory=list)
    final_assessment: FinalAssessmentSection


class ResumeReportData(BaseModel):
    """Full structured report output."""
    report_id: str
    resume_id: str
    generated_at: str
    model: str
    status: str = "COMPLETED"
    sections: ReportSections
    generation_duration_seconds: Optional[float] = None


class ReportHistoryItem(BaseModel):
    """Summary item for report history list."""
    report_id: str
    resume_id: str
    generated_at: str
    model: str
    status: str
    executive_summary: str
    overall_score: Optional[float] = None


# --- Response Envelopes ---

class GenerateReportResponse(BaseModel):
    success: bool = True
    message: str = "AI Resume Report generated successfully"
    data: ResumeReportData


class GetReportResponse(BaseModel):
    success: bool = True
    message: str = "AI Resume Report retrieved successfully"
    data: ResumeReportData


class ReportHistoryResponse(BaseModel):
    success: bool = True
    message: str = "Resume report history retrieved successfully"
    data: List[ReportHistoryItem] = Field(default_factory=list)
