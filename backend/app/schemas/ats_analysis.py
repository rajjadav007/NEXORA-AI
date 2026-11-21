"""
Pydantic Schemas for ATS Compatibility Analysis Engine
Phase 4 | Feature 24: ATS Compatibility Analysis
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

# 8 Category definitions for transparent deterministic scoring summing to 100
ATS_CATEGORIES = {
    "contact_info": {
        "name": "Contact Information Completeness",
        "max_score": 15.0,
        "description": "Email, phone number, location, and professional portfolio / profile links."
    },
    "standard_sections": {
        "name": "Standard Section Detection & Headings",
        "max_score": 15.0,
        "description": "Standard headings recognized by ATS parsers without unusual or missing sections."
    },
    "experience_formatting": {
        "name": "Work Experience Structure & Formatting",
        "max_score": 20.0,
        "description": "Clear role titles, employer names, chronological dates, and bulleted duties."
    },
    "education_structure": {
        "name": "Education Section Structure",
        "max_score": 10.0,
        "description": "Degree title, institution name, and graduation / attendance timeline."
    },
    "skills_presentation": {
        "name": "Technical Skills Presentation",
        "max_score": 15.0,
        "description": "Grouped or clearly organized skills utilizing recognized industry terminology."
    },
    "professional_summary": {
        "name": "Professional Summary Presence",
        "max_score": 10.0,
        "description": "Concise summary block (30-120 words) with targeted professional focus."
    },
    "credentials_projects": {
        "name": "Projects & Certifications",
        "max_score": 5.0,
        "description": "Structured project titles, tech stacks, links, and certifications."
    },
    "formatting_parsing_safety": {
        "name": "File Layout & Parsing Safety",
        "max_score": 10.0,
        "description": "Absence of multi-column layouts, complex tables, text boxes, or unreadable glyphs."
    },
}

STANDARD_ATS_DISCLAIMER = (
    "This score is an algorithmic heuristic estimate based on common industry ATS parsing conventions "
    "and does not replicate or guarantee the proprietary scoring engine of any specific commercial ATS vendor."
)


class ATSCategoryScore(BaseModel):
    """Score breakdown for a specific ATS category."""
    key: str = Field(..., description="Machine category key")
    name: str = Field(..., description="Human-readable category label")
    score: float = Field(..., ge=0.0, description="Earned points in this category")
    max_score: float = Field(..., gt=0.0, description="Maximum possible points in this category")
    status: str = Field("Pass", description="Status: Pass, Warning, or Fail")
    feedback: str = Field(..., description="Actionable summary of performance in this category")


class ATSIssue(BaseModel):
    """An identified ATS issue or formatting risk."""
    id: str = Field(..., description="Unique issue identifier")
    category: str = Field(..., description="Machine category key")
    category_name: str = Field(..., description="Human-readable category name")
    title: str = Field(..., description="Brief title of the issue")
    issue_type: str = Field(
        ...,
        description="'verified_issue' (confirmed data/structural gap) or 'formatting_risk' (layout/parsing hazard)"
    )
    severity: str = Field(
        ...,
        description="'Critical' (high parsing failure risk), 'Warning' (moderate risk), or 'Info' (polish)"
    )
    explanation: str = Field(..., description="Explanation of why this hinders ATS parsers")
    evidence: List[str] = Field(default_factory=list, description="Supporting excerpt, missing field, or file artifact")
    suggested_fix: str = Field(..., description="Specific recommendation to resolve the issue")

    @field_validator("issue_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ["verified_issue", "formatting_risk"]:
            return "formatting_risk"
        return clean

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean not in ["Critical", "Warning", "Info"]:
            return "Warning"
        return clean


class SectionDetectionItem(BaseModel):
    """Status of an individual standard resume section."""
    section_key: str = Field(..., description="Machine section key")
    section_name: str = Field(..., description="Standard section name")
    detected: bool = Field(..., description="Whether section was detected")
    heading_text: Optional[str] = Field(None, description="Actual heading text found in resume")
    is_standard_heading: bool = Field(True, description="Whether the heading matches standard ATS naming")
    status: str = Field(..., description="'Standard', 'Unusual', or 'Missing'")


class KeywordFindings(BaseModel):
    """Analysis of extracted industry keywords and action verbs."""
    total_detected_keywords: int = Field(0, description="Total technical keywords identified")
    top_technical_keywords: List[str] = Field(default_factory=list, description="Primary technical skills detected")
    top_action_verbs: List[str] = Field(default_factory=list, description="Strong action verbs detected in bullets")
    recommended_keywords: List[str] = Field(default_factory=list, description="High-frequency industry keywords to consider")
    keyword_density_note: str = Field(..., description="Observation regarding keyword distribution and formatting")


class RecommendationItem(BaseModel):
    """Targeted before/after recommendation for ATS improvement."""
    title: str = Field(..., description="Short title of recommendation")
    category: str = Field(..., description="Category label")
    priority: str = Field("Medium", description="Critical, High, Medium, or Low")
    current_state: str = Field(..., description="Current detected pattern or excerpt")
    recommended_rewrite: str = Field(..., description="Concrete suggested rewrite or fix")


class AIFeedback(BaseModel):
    """Contextual explanations and tailored improvement recommendations from LangChain / ChatOllama."""
    executive_summary: str = Field(..., description="Executive narrative on ATS readiness")
    tailored_recommendations: List[RecommendationItem] = Field(
        default_factory=list,
        description="Top high-impact recommendations with concrete examples"
    )
    keyword_optimization_advice: str = Field(..., description="Strategic guidance for ATS keyword matching")


class ATSAnalysisData(BaseModel):
    """Complete payload for resume ATS compatibility analysis."""
    id: str = Field(..., description="Analysis unique ID")
    resume_id: str = Field(..., description="Associated resume UUID")
    ats_score: int = Field(..., ge=0, le=100, description="Overall deterministic ATS score (0-100)")
    score_grade: str = Field(..., description="'Excellent', 'Good', 'Needs Work', or 'Poor'")
    score_interpretation: str = Field(..., description="Summary explanation of the score grade")
    category_scores: Dict[str, ATSCategoryScore] = Field(..., description="Score breakdown across 8 categories")
    verified_issues: List[ATSIssue] = Field(default_factory=list, description="Verified content gaps")
    formatting_risks: List[ATSIssue] = Field(default_factory=list, description="Formatting & layout risks")
    detected_sections: List[SectionDetectionItem] = Field(default_factory=list, description="Standard sections audit")
    missing_sections: List[str] = Field(default_factory=list, description="Standard sections that are absent")
    keyword_findings: KeywordFindings = Field(..., description="Keyword & action verb analysis")
    ai_feedback: AIFeedback = Field(..., description="Contextual narrative & improvement advice")
    disclaimer: str = Field(default=STANDARD_ATS_DISCLAIMER, description="Non-affiliation disclaimer")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
    created_at: str = Field(..., description="ISO creation timestamp")
    updated_at: str = Field(..., description="ISO update timestamp")


class ATSAnalysisResponse(BaseModel):
    """Standard API response envelope."""
    success: bool = True
    message: str = "Resume ATS compatibility analysis completed successfully"
    data: Optional[ATSAnalysisData] = None


# =========================================================================
# STRUCTURED LLM OUTPUT SCHEMA (LangChain ChatOllama contextual feedback)
# =========================================================================

class RecommendationItemAI(BaseModel):
    title: str = Field(..., description="Recommendation title")
    category: str = Field(..., description="Category label")
    priority: str = Field("Medium", description="Critical, High, Medium, or Low")
    current_state: str = Field(..., description="Current problematic phrasing or structure from resume")
    recommended_rewrite: str = Field(..., description="Improved ATS-friendly replacement")


class ATSAIStructuredFeedback(BaseModel):
    """
    Enforced schema on ChatOllama / LangChain structured output.
    Used ONLY for qualitative explanations and before/after recommendations.
    Never invents numeric scores.
    """
    executive_summary: str = Field(
        ...,
        description="2-3 sentence executive assessment of candidate's ATS readiness and core bottlenecks"
    )
    tailored_recommendations: List[RecommendationItemAI] = Field(
        default_factory=list,
        description="3 to 6 high-impact before/after recommendations"
    )
    keyword_optimization_advice: str = Field(
        ...,
        description="Practical guidance on incorporating industry keywords and metrics naturally"
    )
