"""
Certifications and Achievements SQLAlchemy Models
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Defines structured certification, license, award, hackathon, competition,
and publication records linked to resumes, canonical skills, and projects.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Boolean,
    Float,
    Integer,
    Uuid,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Certification(Base):
    """
    Extracted and structured candidate certification or license record.
    Multiple certification records belong to a resume.
    """
    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    certification_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    issuing_organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    certification_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="other", index=True
    )  # technical, professional, cloud, ai_ml, programming, data_science, security, project_management, course, training, other

    issue_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expiry_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    credential_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    completion_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="completed", index=True
    )  # completed, in_progress, expired, unknown

    related_skills: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    source_section: Mapped[str] = mapped_column(String(100), nullable=False, default="certifications")
    source_evidence: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    extraction_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="hybrid"
    )  # deterministic, ai_assisted, hybrid, manual
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )  # pending, confirmed, needs_review

    is_manually_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manually_edited_fields: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="certifications")
    user = relationship("User", backref="certifications")


class Achievement(Base):
    """
    Extracted and structured candidate accomplishment record (awards, hackathons,
    competitions, publications, scholarships, leadership recognition).
    Multiple achievement records belong to a resume.
    """
    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    achievement_title: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    achievement_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="other", index=True
    )  # hackathon, competition, academic, scholarship, research, publication, professional, leadership, technical, community, volunteer, other

    event_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    achievement_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="award"
    )  # award, ranking, participation, publication, recognition, scholarship, other
    rank_or_position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    achievement_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    team_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    team_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    candidate_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    related_project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    related_skills: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    achievement_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_section: Mapped[str] = mapped_column(String(100), nullable=False, default="achievements")
    source_evidence: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    extraction_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="hybrid"
    )  # deterministic, ai_assisted, hybrid, manual
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )  # pending, confirmed, needs_review

    is_manually_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manually_edited_fields: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="achievements")
    user = relationship("User", backref="achievements")
    related_project = relationship("Project", backref="linked_achievements")
