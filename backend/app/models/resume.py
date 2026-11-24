"""
Resume and ResumeVersion SQLAlchemy Models
Phase 2 | Feature 6: Resume Storage
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    BigInteger,
    Integer,
    DateTime,
    Uuid,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Resume(Base):
    """
    Primary resume record associating uploaded documents with users.
    Maps to `resumes` table in DATABASE_SCHEMA.md.
    """
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(30), nullable=False, default="COMPLETED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    versions: Mapped[List["ResumeVersion"]] = relationship(
        "ResumeVersion",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeVersion.version_number.desc()",
    )
    user = relationship("User", backref="resumes")
    personal_information = relationship(
        "ResumePersonalInformation",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    education_records = relationship(
        "Education",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="Education.created_at",
    )
    experience_records = relationship(
        "Experience",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="Experience.created_at",
    )
    resume_skills = relationship(
        "ResumeSkill",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeSkill.canonical_name",
    )
    projects = relationship(
        "Project",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="Project.created_at",
    )
    certifications = relationship(
        "Certification",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="Certification.created_at",
    )
    achievements = relationship(
        "Achievement",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="Achievement.created_at",
    )
    quality_score = relationship(
        "ResumeQualityScore",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    strength_analysis = relationship(
        "ResumeStrengthAnalysis",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    weakness_analysis = relationship(
        "ResumeWeaknessAnalysis",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    ats_analysis = relationship(
        "ResumeATSAnalysis",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    grammar_analysis = relationship(
        "ResumeGrammarAnalysis",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    achievement_analysis = relationship(
        "ResumeAchievementAnalysis",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    recommendation_analysis = relationship(
        "ResumeRecommendationAnalysis",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    improvement_snapshots = relationship(
        "ResumeAnalysisSnapshot",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeAnalysisSnapshot.created_at.asc()",
    )
    improvement_tasks = relationship(
        "ResumeImprovementTask",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeImprovementTask.created_at.asc()",
    )
    timeline_events = relationship(
        "ResumeTimelineEvent",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeTimelineEvent.created_at.asc()",
    )
    reports = relationship(
        "ResumeReport",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeReport.created_at.desc()",
    )


class ResumeVersion(Base):
    """
    Version record for historical changes to a resume.
    Maps to `resume_versions` table in DATABASE_SCHEMA.md.
    """
    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="versions")
