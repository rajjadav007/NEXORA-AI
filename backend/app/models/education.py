"""
Education SQLAlchemy Model
Phase 3 | Feature 14: Education Analysis
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Boolean,
    Float,
    Uuid,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Education(Base):
    """
    Extracted and validated candidate academic qualification record.
    Multiple education entries belong to a resume.
    """
    __tablename__ = "education"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    degree: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    normalized_degree: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    degree_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # undergraduate, postgraduate, etc.
    field_of_study: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    institution: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    start_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    graduation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")

    # Grade structured JSON: {"value": float|str, "type": "CGPA"|"GPA"|"Percentage", "scale": float|int, "raw_grade": str}
    grade: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )

    achievements: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    coursework: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    honors: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    source_evidence: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    is_manually_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manually_edited_fields: Mapped[List[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    resume = relationship("Resume", back_populates="education_records")
    user = relationship("User", backref="education_records")
