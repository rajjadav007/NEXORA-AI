"""
Resume Strength Analysis SQLAlchemy Model
Phase 4 | Feature 22: Resume Strength Analysis
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


class ResumeStrengthAnalysis(Base):
    """
    Persisted strength evaluation for a candidate resume.
    Identifies top skills, quantified achievements, demonstrated and potential strengths,
    supporting evidence, and career value across 7 categories.
    """
    __tablename__ = "resume_strength_analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Detailed strengths list: [{title, category, explanation, evidence, professional_value, confidence_level, strength_type, relevance_rank}]
    strengths: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    # Summaries grouped by category: {category_key: {category_name, total_strengths, demonstrated_count, potential_count, key_takeaway}}
    category_summaries: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    is_sufficient_evidence: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    insufficient_evidence_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    top_strengths_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

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
    resume = relationship("Resume", back_populates="strength_analysis")
    user = relationship("User", backref="resume_strength_analyses")
