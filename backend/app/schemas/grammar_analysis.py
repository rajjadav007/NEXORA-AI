"""
Pydantic Schemas for Grammar & Clarity Analysis Engine
Phase 4 | Feature 25: Grammar & Clarity Analysis
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

GRAMMAR_CATEGORIES = {
    "grammar": "Grammar Mistakes",
    "spelling": "Spelling Errors",
    "clarity": "Sentence Clarity",
    "tone": "Professional Tone",
    "structure": "Sentence Structure",
    "repetition": "Repeated Words & Phrases",
    "wordiness": "Unnecessary Wording",
    "readability": "Readability & Complexity",
}

VALID_SEVERITIES = ["High", "Medium", "Low"]


class GrammarIssue(BaseModel):
    """An individual writing, grammar, tone, or clarity issue."""
    id: str = Field(..., description="Unique issue identifier")
    category: str = Field(
        ...,
        description="One of: grammar, spelling, clarity, tone, structure, repetition, wordiness, readability"
    )
    category_name: str = Field(..., description="Human-readable category label")
    original_text: str = Field(..., description="Original problematic excerpt or sentence")
    suggested_text: str = Field(..., description="Polished, professional correction preserving meaning")
    explanation: str = Field(..., description="Clear explanation of the writing rule or tone deficiency")
    severity: str = Field(..., description="Severity level: High, Medium, or Low")
    section: Optional[str] = Field("General", description="Resume section (e.g. Summary, Experience, Projects)")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean not in VALID_SEVERITIES:
            return "Medium"
        return clean

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in GRAMMAR_CATEGORIES:
            return "clarity"
        return clean


class SentenceComparison(BaseModel):
    """Side-by-side comparison of an unclear sentence versus an enhanced professional alternative."""
    original_sentence: str = Field(..., description="Original phrasing from resume")
    improved_sentence: str = Field(..., description="Stronger, impact-focused rewrite preserving facts")
    reason: str = Field(..., description="Why the revision enhances professional impression")
    section: Optional[str] = Field("General", description="Resume section location")


class ReadabilityMetrics(BaseModel):
    """Automated linguistic and readability measurements."""
    readability_score: float = Field(..., description="Automated reading ease score (0-100)")
    grade_level: str = Field(..., description="Target reading difficulty level (e.g. 'Grade 10-12')")
    avg_words_per_sentence: float = Field(..., description="Average sentence length in words")
    total_words: int = Field(0, description="Total analyzed resume word count")
    complexity_assessment: str = Field(..., description="Summary assessment of sentence flow and complexity")


class GrammarAnalysisData(BaseModel):
    """Complete payload for resume grammar & clarity analysis."""
    id: str = Field(..., description="Analysis unique ID")
    resume_id: str = Field(..., description="Associated resume UUID")
    writing_score: int = Field(..., ge=0, le=100, description="Overall writing quality score (0-100)")
    writing_grade: str = Field(..., description="'Excellent', 'Professional', 'Needs Polish', or 'Poor'")
    overall_assessment: str = Field(..., description="Executive narrative on communication quality and tone")
    readability_metrics: ReadabilityMetrics = Field(..., description="Linguistic readability measurements")
    category_counts: Dict[str, int] = Field(default_factory=dict, description="Issues count per category")
    issues: List[GrammarIssue] = Field(default_factory=list, description="All identified writing issues")
    sentence_comparisons: List[SentenceComparison] = Field(
        default_factory=list,
        description="Side-by-side before/after sentence upgrades"
    )
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
    created_at: str = Field(..., description="ISO creation timestamp")
    updated_at: str = Field(..., description="ISO update timestamp")


class GrammarAnalysisResponse(BaseModel):
    """Standard API response envelope."""
    success: bool = True
    message: str = "Resume grammar and clarity analysis completed successfully"
    data: Optional[GrammarAnalysisData] = None


# =========================================================================
# STRUCTURED LLM OUTPUT SCHEMA (LangChain ChatOllama)
# =========================================================================

class GrammarIssueAI(BaseModel):
    original_text: str = Field(..., description="Problematic phrase or sentence from the resume")
    suggested_text: str = Field(..., description="Polished correction maintaining original facts and achievements")
    category: str = Field(
        ...,
        description="Exact key: grammar, spelling, clarity, tone, structure, repetition, wordiness, or readability"
    )
    explanation: str = Field(..., description="Why this needs improvement and what rule applies")
    severity: str = Field("Medium", description="High, Medium, or Low")
    section: Optional[str] = Field("General", description="Section (e.g. Summary, Experience, Projects)")


class SentenceComparisonAI(BaseModel):
    original_sentence: str = Field(..., description="Original weak or unclear statement from resume")
    improved_sentence: str = Field(..., description="Professional, executive rewrite preserving meaning")
    reason: str = Field(..., description="Core improvement rationale")
    section: Optional[str] = Field("General", description="Section name")


class ResumeGrammarAIStructuredOutput(BaseModel):
    """
    Enforced schema on ChatOllama / LangChain structured output.
    Ensures typed writing issues, sentence comparisons, and executive assessment.
    """
    overall_assessment: str = Field(
        ...,
        description="2-3 sentence executive assessment of candidate's writing style, tone, and clarity"
    )
    issues: List[GrammarIssueAI] = Field(
        default_factory=list,
        description="List of detected writing issues across the 8 categories"
    )
    sentence_comparisons: List[SentenceComparisonAI] = Field(
        default_factory=list,
        description="3 to 6 high-value before-and-after sentence comparisons"
    )
    readability_summary: str = Field(
        ...,
        description="Observation regarding sentence complexity, word choice, and flow"
    )
