"""
JobMatch SQLAlchemy Model
Phase 7 | Feature 39: Resume-to-Job Matching Engine
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class JobMatch(Base):
    """
    Persisted candidate-to-job matching result for a (resume_id, job_description_id) pair.
    Unique on (resume_id, job_description_id) to prevent accidental duplicates while
    supporting regeneration when underlying resume or job analyses change.
    """

    __tablename__ = "job_matches"
    __table_args__ = (
        UniqueConstraint("resume_id", "job_description_id", name="uq_job_matches_resume_job"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    overall_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    matched_requirements: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    partially_matched_requirements: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    missing_requirements: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    not_verifiable_requirements: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    evidence_from_resume: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )
    match_details: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", backref="job_matches")
    resume = relationship("Resume", backref="job_matches")
    job_description = relationship("JobDescription", backref="job_matches")
