"""
Resume Weakness Analysis SQLAlchemy Model
Phase 4 | Feature 23: Resume Weakness Analysis
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Boolean,
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


class ResumeWeaknessAnalysis(Base):
    """
    Persisted weakness evaluation for a candidate resume.
    Identifies missing information, weak content, unclear descriptions,
    vague statements lacking measurable impact, and categorized improvement areas.
    """
    __tablename__ = "resume_weakness_analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Detailed weaknesses list: [{title, category, explanation, evidence, why_it_matters, suggested_improvement, priority, relevance_rank, weakness_type}]
    weaknesses: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    # Missing information identified separately: [{section, item, relevance, impact_level, is_optional}]
    missing_information: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    # Summaries grouped by category: {category_key: {category_name, total_weaknesses, key_recommendation}}
    category_summaries: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    overall_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

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
    resume = relationship("Resume", back_populates="weakness_analysis")
    user = relationship("User", backref="resume_weakness_analyses")
