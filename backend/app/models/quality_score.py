"""
Resume Quality Score SQLAlchemy Model
Phase 4 | Feature 21: Resume Quality Score Engine
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Float,
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


class ResumeQualityScore(Base):
    """
    Quality evaluation record for an uploaded resume.
    Persists overall score, category breakdown, explanations, strengths,
    missing sections, and actionable improvement recommendations.
    """
    __tablename__ = "resume_quality_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rating_level: Mapped[str] = mapped_column(String(50), nullable=False, default="Needs Improvement")
    
    # Category score dictionary: {category_key: {score, max_score, weight, percentage, rating, explanation}}
    category_scores: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )
    
    # Direct lookup of explanations per category
    category_explanations: Mapped[Dict[str, str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    strengths: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    missing_information: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    improvement_suggestions: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    rubric_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    
    # Metadata: model used, prompt version, execution duration, timestamp
    analysis_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="quality_score")
    user = relationship("User", backref="resume_quality_scores")
