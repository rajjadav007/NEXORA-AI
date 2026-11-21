"""
Resume Achievement Analysis SQLAlchemy Model
Phase 4 | Feature 26: Achievement Analysis
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Integer,
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


class ResumeAchievementAnalysis(Base):
    """
    Persisted achievement and accomplishment evaluation for a candidate resume.
    Identifies accomplishments across work, projects, hackathons, awards, certifications,
    and leadership; detects measurable metrics, evaluates quality, and suggests improved statements.
    """
    __tablename__ = "resume_achievement_analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Overall Achievement Quality Score out of 100
    achievement_score: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    score_grade: Mapped[str] = mapped_column(String(35), nullable=False, default="Strong")
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Core Quantification Metrics
    total_achievements_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantified_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unquantified_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantification_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Detailed list of all evaluated achievements
    achievements: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    # Summaries grouped by category: {category_key: {total, quantified, unquantified, top_achievement}}
    category_breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    # Rubric component score breakdown summing to 100
    rubric_breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

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
    resume = relationship("Resume", back_populates="achievement_analysis")
    user = relationship("User", backref="resume_achievement_analyses")
