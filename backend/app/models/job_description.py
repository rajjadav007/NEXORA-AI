"""
JobDescription SQLAlchemy Model
Phase 6 | Feature 33: Job Description Input
"""

import uuid
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Uuid,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class JobDescription(Base):
    """
    Persisted job description submitted or imported by an authenticated user.
    Structured to support downstream Phase 6 features (#34-#38).
    """

    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Readiness fields for Features #34-#38
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    analysis_status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    experience_required: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    salary_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    education_required: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[List[Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    mandatory_skills: Mapped[List[Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )
    preferred_skills: Mapped[List[Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", backref="job_descriptions")
