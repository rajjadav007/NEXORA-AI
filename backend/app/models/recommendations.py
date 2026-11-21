"""
Resume Improvement Recommendations SQLAlchemy Model
Phase 4 | Feature 27: Resume Improvement Recommendations
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


class ResumeRecommendationAnalysis(Base):
    """
    Persisted personalized improvement recommendations for a candidate resume.
    Synthesizes findings across Features #21 to #26 (Quality Score, Strengths,
    Weaknesses, ATS Compatibility, Grammar & Clarity, and Achievement Analysis)
    into prioritized, actionable recommendations with progress tracking.
    """
    __tablename__ = "resume_recommendation_analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Executive Overview
    overall_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Progress Tracking Aggregates
    total_recommendations_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Breakdowns
    priority_breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )
    category_breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )
    coverage_summary: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    # Detailed list of actionable recommendations:
    # [{
    #     id: str,
    #     title: str,
    #     category: str,
    #     category_name: str,
    #     explanation: str,
    #     reason: str,
    #     evidence: str,
    #     suggested_action: str,
    #     priority: str,
    #     estimated_effort: str,
    #     related_feature: str,
    #     is_completed: bool,
    #     completed_at: Optional[str]
    # }]
    recommendations: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
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
    resume = relationship("Resume", back_populates="recommendation_analysis")
    user = relationship("User", backref="resume_recommendation_analyses")
