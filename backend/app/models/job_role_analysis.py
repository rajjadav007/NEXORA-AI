"""
JobRoleAnalysis SQLAlchemy Model
Phase 6 | Feature 35: Job Role Extraction
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Text,
    Float,
    DateTime,
    Uuid,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class JobRoleAnalysis(Base):
    """
    Persisted AI-extracted job role classification and metadata for a JobDescription.
    One-to-one with job_descriptions to prevent duplicate records on repeated extraction.
    """

    __tablename__ = "job_role_analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    standardized_role: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    seniority: Mapped[str] = mapped_column(String(60), nullable=False, default="Unknown")
    experience_level: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )
    employment_type: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    work_arrangement: Mapped[str] = mapped_column(String(40), nullable=False, default="Unknown")
    industry: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    responsibilities: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    role_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    analysis_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    job_description = relationship("JobDescription", backref="role_analysis")
