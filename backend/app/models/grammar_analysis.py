"""
Resume Grammar & Clarity Analysis SQLAlchemy Model
Phase 4 | Feature 25: Grammar & Clarity Analysis
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
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


class ResumeGrammarAnalysis(Base):
    """
    Persisted grammar, spelling, clarity, and professional tone evaluation.
    Stores detected writing issues, before-and-after sentence comparisons,
    readability metrics, and category counts without overwriting the original resume.
    """
    __tablename__ = "resume_grammar_analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Writing quality assessment score (0-100) and grade
    writing_score: Mapped[int] = mapped_column(Integer, nullable=False, default=85)
    writing_grade: Mapped[str] = mapped_column(String(30), nullable=False, default="Professional")
    overall_assessment: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Automated readability metrics (grade level, avg words/sentence, complexity)
    readability_metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    # Issue breakdown by category: {grammar: 1, spelling: 0, clarity: 2, tone: 1, ...}
    category_counts: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    # List of individual issues: [{id, category, category_name, original_text, suggested_text, explanation, severity, section}]
    issues: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    # Before-and-after sentence improvements: [{original_sentence, improved_sentence, reason, section}]
    sentence_comparisons: Mapped[List[Dict[str, Any]]] = mapped_column(
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
    resume = relationship("Resume", back_populates="grammar_analysis")
    user = relationship("User", backref="resume_grammar_analyses")
