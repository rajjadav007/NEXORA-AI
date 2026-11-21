"""
Certifications and Achievements Pydantic Schemas
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Validation, serialization, and API response structures.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class CertificationSkillLinkData(BaseModel):
    """Canonical skill mapping linked to a certification."""
    model_config = ConfigDict(from_attributes=True)

    original_name: str = Field(..., description="Original technology / skill name from evidence")
    canonical_id: Optional[str] = Field(None, description="Feature #17 canonical skill ID")
    canonical_name: str = Field(..., description="Feature #17 standardized canonical name")
    category: str = Field(default="Other", description="Skill category")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_explicit: bool = Field(default=True)


class CertificationEntryData(BaseModel):
    """Full structured candidate certification intelligence entry."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None

    certification_name: str
    normalized_name: str
    issuing_organization: Optional[str] = None
    certification_category: str = "other"  # technical, professional, cloud, ai_ml, programming, data_science, security, project_management, course, training, other

    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None

    completion_status: str = "completed"  # completed, in_progress, expired, unknown
    related_skills: List[CertificationSkillLinkData] = Field(default_factory=list)

    source_section: str = "certifications"
    source_evidence: List[str] = Field(default_factory=list)

    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_method: str = "hybrid"
    review_status: str = "pending"  # pending, confirmed, needs_review

    is_manually_edited: bool = False
    manually_edited_fields: List[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CertificationCreateRequest(BaseModel):
    """User payload to manually create a certification record."""
    certification_name: str = Field(..., min_length=2, max_length=255)
    normalized_name: Optional[str] = Field(None, max_length=255)
    issuing_organization: Optional[str] = Field(None, max_length=255)
    certification_category: str = Field(default="other", max_length=50)

    issue_date: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[str] = Field(None, max_length=50)
    credential_id: Optional[str] = Field(None, max_length=150)
    credential_url: Optional[str] = None

    completion_status: str = Field(default="completed", max_length=30)
    related_skills: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    source_section: Optional[str] = "manual_entry"
    source_evidence: Optional[List[str]] = Field(default_factory=list)


class CertificationUpdateRequest(BaseModel):
    """User payload to manually update an existing certification."""
    certification_name: Optional[str] = Field(None, min_length=2, max_length=255)
    normalized_name: Optional[str] = Field(None, max_length=255)
    issuing_organization: Optional[str] = Field(None, max_length=255)
    certification_category: Optional[str] = Field(None, max_length=50)

    issue_date: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[str] = Field(None, max_length=50)
    credential_id: Optional[str] = Field(None, max_length=150)
    credential_url: Optional[str] = None

    completion_status: Optional[str] = Field(None, max_length=30)
    related_skills: Optional[List[Dict[str, Any]]] = None
    review_status: Optional[str] = Field(None, max_length=30)


class CertificationConfirmRequest(BaseModel):
    """Payload to confirm or adjust verification review status."""
    notes: Optional[str] = None


class CertificationSummaryData(BaseModel):
    """Aggregate analytics for candidate certifications."""
    total_certifications: int = 0
    completed_certifications: int = 0
    in_progress_certifications: int = 0
    expired_certifications: int = 0
    category_counts: Dict[str, int] = Field(default_factory=dict)
    pending_reviews: int = 0
    unique_issuers: List[str] = Field(default_factory=list)


class CertificationListResponse(BaseModel):
    """API list response envelope for certifications."""
    success: bool = True
    message: str = "Certifications retrieved successfully"
    data: List[CertificationEntryData] = Field(default_factory=list)
    summary: Optional[CertificationSummaryData] = None
    total: int = 0
    extraction_status: str = "completed"


class CertificationSingleResponse(BaseModel):
    """API single response envelope for a certification record."""
    success: bool = True
    message: str = "Certification operation successful"
    data: Optional[CertificationEntryData] = None


# =========================================================================
# ACHIEVEMENTS SCHEMAS
# =========================================================================

class AchievementEntryData(BaseModel):
    """Full structured candidate accomplishment intelligence entry."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None

    achievement_title: str
    normalized_title: str
    achievement_category: str = "other"  # hackathon, competition, academic, scholarship, research, publication, professional, leadership, technical, community, volunteer, other

    event_name: Optional[str] = None
    organization: Optional[str] = None
    achievement_type: str = "award"  # award, ranking, participation, publication, recognition, scholarship, other
    rank_or_position: Optional[str] = None

    achievement_date: Optional[str] = None
    description: Optional[str] = None

    team_name: Optional[str] = None
    team_size: Optional[int] = None
    candidate_role: Optional[str] = None

    related_project_id: Optional[uuid.UUID] = None
    related_project_title: Optional[str] = None
    related_skills: List[CertificationSkillLinkData] = Field(default_factory=list)
    achievement_url: Optional[str] = None

    source_section: str = "achievements"
    source_evidence: List[str] = Field(default_factory=list)

    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_method: str = "hybrid"
    review_status: str = "pending"  # pending, confirmed, needs_review

    is_manually_edited: bool = False
    manually_edited_fields: List[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AchievementCreateRequest(BaseModel):
    """User payload to manually create an achievement record."""
    achievement_title: str = Field(..., min_length=2, max_length=255)
    normalized_title: Optional[str] = Field(None, max_length=255)
    achievement_category: str = Field(default="other", max_length=50)

    event_name: Optional[str] = Field(None, max_length=255)
    organization: Optional[str] = Field(None, max_length=255)
    achievement_type: str = Field(default="award", max_length=50)
    rank_or_position: Optional[str] = Field(None, max_length=100)

    achievement_date: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

    team_name: Optional[str] = Field(None, max_length=100)
    team_size: Optional[int] = Field(None, ge=1)
    candidate_role: Optional[str] = Field(None, max_length=100)

    related_project_id: Optional[uuid.UUID] = None
    related_skills: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    achievement_url: Optional[str] = None

    source_section: Optional[str] = "manual_entry"
    source_evidence: Optional[List[str]] = Field(default_factory=list)


class AchievementUpdateRequest(BaseModel):
    """User payload to manually update an existing achievement."""
    achievement_title: Optional[str] = Field(None, min_length=2, max_length=255)
    normalized_title: Optional[str] = Field(None, max_length=255)
    achievement_category: Optional[str] = Field(None, max_length=50)

    event_name: Optional[str] = Field(None, max_length=255)
    organization: Optional[str] = Field(None, max_length=255)
    achievement_type: Optional[str] = Field(None, max_length=50)
    rank_or_position: Optional[str] = Field(None, max_length=100)

    achievement_date: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

    team_name: Optional[str] = Field(None, max_length=100)
    team_size: Optional[int] = Field(None, ge=1)
    candidate_role: Optional[str] = Field(None, max_length=100)

    related_project_id: Optional[uuid.UUID] = None
    related_skills: Optional[List[Dict[str, Any]]] = None
    achievement_url: Optional[str] = None
    review_status: Optional[str] = Field(None, max_length=30)


class AchievementConfirmRequest(BaseModel):
    """Payload to confirm or adjust achievement review status."""
    notes: Optional[str] = None


class AchievementSummaryData(BaseModel):
    """Aggregate analytics for candidate achievements."""
    total_achievements: int = 0
    total_awards: int = 0
    hackathon_awards: int = 0
    competition_achievements: int = 0
    publications: int = 0
    scholarship_awards: int = 0
    category_counts: Dict[str, int] = Field(default_factory=dict)
    pending_reviews: int = 0
    linked_projects_count: int = 0


class AchievementListResponse(BaseModel):
    """API list response envelope for achievements."""
    success: bool = True
    message: str = "Achievements retrieved successfully"
    data: List[AchievementEntryData] = Field(default_factory=list)
    summary: Optional[AchievementSummaryData] = None
    total: int = 0
    extraction_status: str = "completed"


class AchievementSingleResponse(BaseModel):
    """API single response envelope for an achievement record."""
    success: bool = True
    message: str = "Achievement operation successful"
    data: Optional[AchievementEntryData] = None


class CertificationsAchievementsCombinedSummary(BaseModel):
    """Combined summary analytics for both certifications and achievements."""
    certifications: CertificationSummaryData
    achievements: AchievementSummaryData
    total_combined_records: int = 0
    total_pending_reviews: int = 0
