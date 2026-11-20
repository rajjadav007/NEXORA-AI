"""
Project Intelligence SQLAlchemy Model
Phase 3 | Feature 18: Project Intelligence
Defines structured candidate project intelligence records linked to resumes and canonical skills.
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


class Project(Base):
    """
    Extracted and structured project record.
    Multiple project records belong to a resume.
    """
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    project_title: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    project_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="other", index=True
    )  # academic, personal, hackathon, research, open_source, internship, professional, freelance, other

    short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detailed_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    problem_statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposed_solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    project_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    team_type: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")  # individual, team, unknown
    team_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    start_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_ongoing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    technologies: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    skills: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    responsibilities: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    achievements: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    measurable_outcomes: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    project_links: Mapped[List[Dict[str, str]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    source_section: Mapped[str] = mapped_column(String(100), nullable=False, default="projects")
    source_evidence: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    extraction_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="hybrid"
    )  # deterministic, ai_assisted, hybrid, manual
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
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
    resume = relationship("Resume", back_populates="projects")
    user = relationship("User", backref="projects")
