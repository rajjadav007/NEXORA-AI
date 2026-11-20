"""
Skill Normalization SQLAlchemy Models
Phase 3 | Feature 17: Skill Normalization
Defines Canonical Skills, Skill Aliases, and Resume-specific Normalized Skills.
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


class Skill(Base):
    """
    Centralized canonical skill catalog.
    Maintains standardized skill names, categories, skill types, and dictionary version.
    """
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    skill_type: Mapped[str] = mapped_column(String(50), nullable=False, default="technical")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    aliases: Mapped[List["SkillAlias"]] = relationship(
        "SkillAlias",
        back_populates="skill",
        cascade="all, delete-orphan",
        order_by="SkillAlias.alias",
    )
    resume_skills: Mapped[List["ResumeSkill"]] = relationship(
        "ResumeSkill",
        back_populates="canonical_skill",
    )


class SkillAlias(Base):
    """
    Alternative skill names, abbreviations, and spellings mapped to canonical skills.
    """
    __tablename__ = "skill_aliases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(150), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="aliases")


class ResumeSkill(Base):
    """
    Normalized candidate skill extracted or mapped for a specific resume.
    Preserves all original names, section provenances, source evidence, and user edit history.
    """
    __tablename__ = "resume_skills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True
    )

    original_name: Mapped[str] = mapped_column(String(150), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Other")
    skill_type: Mapped[str] = mapped_column(String(50), nullable=False, default="technical")

    normalization_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="exact_match"
    )  # exact_match, alias_match, format_normalization, contextual_match, semantic_suggestion, user_manual, unknown

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    normalization_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="normalized"
    )  # normalized, pending_review, confirmed, rejected

    source_sections: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    source_evidence: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    aliases_detected: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    is_manually_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manually_edited_fields: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    dictionary_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="resume_skills")
    canonical_skill = relationship("Skill", back_populates="resume_skills")
