"""
Skill Normalization Pydantic Schemas
Phase 3 | Feature 17: Skill Normalization
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SkillEntryData(BaseModel):
    """Normalized skill entry representing a standardized capability."""
    id: Optional[str] = Field(None, description="Unique record identifier")
    resume_id: Optional[str] = Field(None, description="Associated resume ID")
    skill_id: Optional[str] = Field(None, description="Canonical catalog ID")
    original_name: str = Field(..., description="Original raw extracted name")
    canonical_name: str = Field(..., description="Standardized canonical name")
    category: str = Field("Other", description="Skill category taxonomy")
    skill_type: str = Field("technical", description="technical, soft, or tool")
    normalization_method: str = Field(
        "exact_match",
        description="exact_match, alias_match, format_normalization, contextual_match, semantic_suggestion, user_manual, unknown"
    )
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Evidence-backed confidence")
    normalization_status: str = Field("normalized", description="normalized, pending_review, confirmed, rejected")
    source_sections: List[str] = Field(default_factory=list, description="Sections where skill appeared")
    source_evidence: List[str] = Field(default_factory=list, description="Verifying text snippets")
    aliases_detected: List[str] = Field(default_factory=list, description="All alias forms found")
    occurrence_count: int = Field(1, ge=1, description="Total mentions consolidated")
    is_manually_edited: bool = Field(False, description="Manual modification protection flag")
    manually_edited_fields: List[str] = Field(default_factory=list, description="Fields edited manually")
    dictionary_version: str = Field("1.0.0", description="Dictionary version used")

    model_config = ConfigDict(from_attributes=True)


class SkillSummaryData(BaseModel):
    """Aggregate statistics for skill normalization."""
    total_original_skills: int = Field(0, description="Total raw skill mentions found")
    total_normalized_skills: int = Field(0, description="Total unique canonical skills")
    aliases_matched: int = Field(0, description="Number of alias matches mapped")
    duplicates_consolidated: int = Field(0, description="Number of redundant mentions merged")
    pending_reviews: int = Field(0, description="Ambiguous skills needing confirmation")
    unknown_skills: int = Field(0, description="Unrecognized skills preserved as original")
    category_distribution: Dict[str, int] = Field(default_factory=dict, description="Count per category")
    skill_type_distribution: Dict[str, int] = Field(default_factory=dict, description="Count per skill type")

    model_config = ConfigDict(from_attributes=True)


class SkillNormalizeRequest(BaseModel):
    """Payload to normalize an arbitrary list of raw skill strings."""
    skills: List[str] = Field(..., description="List of raw skill strings to normalize")
    context_text: Optional[str] = Field(None, description="Optional surrounding text for contextual resolution")


class SkillManualUpdateRequest(BaseModel):
    """Payload for manual edit or correction of a normalized skill."""
    canonical_name: Optional[str] = Field(None, min_length=1, max_length=150)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    skill_type: Optional[str] = Field(None, min_length=1, max_length=50)
    normalization_status: Optional[str] = Field(None, description="confirmed, rejected, normalized, pending_review")


class SkillConfirmRequest(BaseModel):
    """Payload to confirm a pending review mapping."""
    canonical_name: Optional[str] = Field(None, description="Optional override to confirm with a different canonical name")


class SkillRejectRequest(BaseModel):
    """Payload to reject a proposed normalization mapping."""
    reason: Optional[str] = Field(None, description="Reason for rejecting the mapping")


class SkillAliasCreateRequest(BaseModel):
    """Payload to add a new alias to the canonical skill dictionary."""
    canonical_name: str = Field(..., min_length=1, max_length=150)
    alias: str = Field(..., min_length=1, max_length=150)
    category: Optional[str] = Field(None, max_length=100)
    skill_type: Optional[str] = Field("technical", max_length=50)


class CanonicalSkillData(BaseModel):
    """Entry in the canonical skill dictionary."""
    id: Optional[str] = None
    name: str
    category: str
    skill_type: str = "technical"
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    version: str = "1.0.0"
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class SkillListResponse(BaseModel):
    """Response containing list of normalized skills."""
    success: bool = True
    message: str = "Skills normalized successfully"
    data: List[SkillEntryData] = Field(default_factory=list)
    summary: Optional[SkillSummaryData] = None
    total: int = 0
    extraction_status: str = "completed"


class SkillSingleResponse(BaseModel):
    """Response containing a single normalized skill."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[SkillEntryData] = None


class DictionaryResponse(BaseModel):
    """Response containing canonical dictionary entries."""
    success: bool = True
    message: str = "Dictionary retrieved successfully"
    version: str = "1.0.0"
    total: int = 0
    data: List[CanonicalSkillData] = Field(default_factory=list)
