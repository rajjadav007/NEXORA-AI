"""
Resume ATS Compatibility Analysis SQLAlchemy Model
Phase 4 | Feature 24: ATS Compatibility Analysis
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


class ResumeATSAnalysis(Base):
    """
    Persisted ATS compatibility evaluation for a candidate resume.
    Stores deterministic scoring rubric results, verified issues,
    formatting & parsing risks, section detection, and keyword findings.
    """
    __tablename__ = "resume_ats_analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Deterministic ATS Compatibility Score out of 100
    ats_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_grade: Mapped[str] = mapped_column(String(30), nullable=False, default="Fair")

    # Category breakdown scores: {category_key: {key, name, score, max_score, status, feedback}}
    category_scores: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    # Definite content & structural gaps: [{id, category, title, issue_type, severity, explanation, evidence, suggested_fix}]
    verified_issues: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    # Layout, columns, tables, textboxes risks: [{id, category, title, issue_type, severity, explanation, evidence, suggested_fix}]
    formatting_risks: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    # Detected section headings and structure: [{section_key, section_name, detected, heading_text, is_standard_heading, status}]
    detected_sections: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    # List of missing standard section names: ["Professional Summary", "Certifications"]
    missing_sections: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    # Keywords, action verbs, and density: {total_detected_keywords, top_technical_keywords, top_action_verbs, recommended_keywords, keyword_density_note}
    keyword_findings: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    # Contextual LLM explanations & before/after recommendations
    ai_feedback: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    # Transparent rubric execution metadata
    analysis_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    # Standard non-affiliation disclaimer
    disclaimer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="This score is an algorithmic heuristic estimate based on common industry ATS parsing conventions and does not replicate any proprietary vendor's scoring engine."
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="ats_analysis")
    user = relationship("User", backref="resume_ats_analyses")
