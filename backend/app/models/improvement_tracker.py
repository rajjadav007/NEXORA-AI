"""
Resume Improvement Tracker SQLAlchemy Models
Phase 5 | Feature 30: Resume Improvement Tracker
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Float,
    Integer,
    DateTime,
    Uuid,
    ForeignKey,
    func,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class ResumeAnalysisSnapshot(Base):
    """
    Historical point-in-time snapshot of resume analysis scores and evaluations.
    Associated with a resume and optionally its version.
    Never overwritten when subsequent analyses are executed.
    """
    __tablename__ = "resume_analysis_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ats_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    readability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    category_scores: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )
    strengths_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weaknesses_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    snapshot_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="improvement_snapshots")
    resume_version = relationship("ResumeVersion")


class ResumeImprovementTask(Base):
    """
    Actionable improvement task generated from recommendations and weaknesses.
    Supports tracking progress (Pending, In Progress, Completed), priorities,
    and completion dates persisted in PostgreSQL.
    """
    __tablename__ = "resume_improvement_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    section: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="Medium")  # High, Medium, Low
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending")    # Pending, In Progress, Completed

    source_recommendation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="improvement_tasks")
    user = relationship("User", backref="improvement_tasks")


class ResumeTimelineEvent(Base):
    """
    Chronological timeline events tracking key milestones:
    RESUME_UPLOADED, RESUME_ANALYZED, TASK_CREATED, TASK_COMPLETED,
    TASK_STATUS_UPDATED, TASK_REOPENED, VERSION_UPLOADED, VERSION_ANALYZED.
    """
    __tablename__ = "resume_timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    event_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="timeline_events")
    user = relationship("User", backref="resume_timeline_events")
