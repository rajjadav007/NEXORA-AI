"""
AI Resume Report SQLAlchemy Model
Phase 5 | Feature 31: AI Resume Report
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
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


class ResumeReport(Base):
    """
    Persisted comprehensive AI Resume Report generated using local Ollama.
    Contains detailed multi-section evaluations, score interpretations,
    skills, experience, education, projects, ATS compliance, strengths,
    weaknesses, actionable recommendations, and final strategic assessment.
    """
    __tablename__ = "resume_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="COMPLETED")

    # Structured report data containing all report sections:
    # executive_summary, quality_assessment, skills_assessment,
    # experience_assessment, education_assessment, project_assessment,
    # strengths, weaknesses, ats_assessment, recommendations, final_assessment
    report_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False
    )

    executive_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    generation_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="reports")
    user = relationship("User", backref="resume_reports")
