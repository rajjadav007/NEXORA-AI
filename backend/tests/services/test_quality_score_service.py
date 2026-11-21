"""
Unit and Integration Tests for Resume Quality Score Engine Service
Phase 4 | Feature 21: Resume Quality Score Engine
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.schemas.quality_score import (
    ResumeQualityAIStructuredOutput,
    CategoryEvaluationAI,
)
from app.services.quality_score.rubric import (
    RUBRIC_CATEGORIES,
    TOTAL_RUBRIC_WEIGHT,
    get_rating_level,
)
from app.services.quality_score.deterministic_scorer import evaluate_deterministic_baseline
from app.services.quality_score.service import QualityScoreService
from app.services.quality_score.ai_evaluator import (
    QualityScoreAIEvaluator,
    OllamaUnavailableError,
    AIOutputValidationError,
)
from app.models.resume import Resume
from app.models.quality_score import ResumeQualityScore
from app.models.personal_information import ResumePersonalInformation
from app.models.skills import ResumeSkill
from app.models.experience import Experience
from app.models.education import Education
from app.models.project import Project
from app.models.certifications import Certification, Achievement
from app.database.session import SessionLocal


@pytest.fixture
def db_session():
    """Provides a transactional test database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def create_mock_ai_output(ratio: float = 0.85) -> ResumeQualityAIStructuredOutput:
    """Helper to generate a valid mock structured LLM output."""
    def _cat(name: str):
        return CategoryEvaluationAI(
            score_ratio=ratio,
            explanation=f"Strong performance demonstrated in {name}.",
            strengths=[f"Demonstrated good {name} foundation"],
            improvements=[f"Add further metrics to {name}"],
        )

    return ResumeQualityAIStructuredOutput(
        completeness=_cat("completeness"),
        professional_summary=_cat("professional summary"),
        technical_skills=_cat("technical skills"),
        work_experience=_cat("work experience"),
        project_descriptions=_cat("project descriptions"),
        education=_cat("education"),
        achievements=_cat("achievements"),
        content_clarity=_cat("content clarity"),
        top_strengths=["Strong technical skills", "Quantified work achievements"],
        missing_critical_information=[],
        priority_improvements=["Include GitHub links for projects"],
    )


def test_rubric_weights_sum_to_100():
    """Verify that the rubric categories strictly sum to 100.0."""
    total_weight = sum(cat.weight for cat in RUBRIC_CATEGORIES.values())
    total_max_score = sum(cat.max_score for cat in RUBRIC_CATEGORIES.values())
    assert abs(total_weight - 100.0) < 1e-6
    assert abs(total_max_score - 100.0) < 1e-6
    assert len(RUBRIC_CATEGORIES) == 8


def test_rating_level_bands():
    """Verify rating level thresholds."""
    assert get_rating_level(95.0) == "Exceptional"
    assert get_rating_level(85.0) == "Strong"
    assert get_rating_level(75.0) == "Good"
    assert get_rating_level(60.0) == "Needs Improvement"
    assert get_rating_level(40.0) == "Critical Gaps"


def test_deterministic_scoring_full_resume():
    """Verify deterministic scoring on a comprehensive resume."""
    personal_info = MagicMock(
        full_name="Alex Mercer",
        email="alex@example.com",
        phone="+1234567890",
        summary="Senior Software Engineer with 8+ years experience scaling cloud services.",
    )
    skills = [
        MagicMock(canonical_name="Python", category="Programming Languages"),
        MagicMock(canonical_name="FastAPI", category="Frameworks"),
        MagicMock(canonical_name="PostgreSQL", category="Databases"),
        MagicMock(canonical_name="Docker", category="DevOps"),
        MagicMock(canonical_name="Kubernetes", category="DevOps"),
        MagicMock(canonical_name="AWS", category="Cloud"),
    ]
    experience = [
        MagicMock(
            job_title="Lead Backend Engineer",
            company_name="CloudTech",
            description="Architected distributed microservices. Reduced p99 latency by 35% and saved $120,000 annually.",
            key_responsibilities=["Scaled system to 500k daily active users."],
        )
    ]
    education = [
        MagicMock(
            degree_name="B.S. Computer Science",
            institution_name="MIT",
            start_date="2014",
            end_date="2018",
            grade="3.9 GPA",
        )
    ]
    projects = [
        MagicMock(
            project_title="Realtime Stream Processing",
            description="Built distributed pipeline with Kafka and Redis. Achieved 25,000 rps throughput.",
            skills_used=["Kafka", "Redis"],
        )
    ]
    certifications = [MagicMock(certification_name="AWS Certified Solutions Architect")]
    achievements = [MagicMock(achievement_name="Hackathon Grand Prize Winner")]
    cleaned_text = "Alex Mercer Senior Software Engineer. Architected distributed microservices..." * 20

    baseline = evaluate_deterministic_baseline(
        personal_info=personal_info,
        education_records=education,
        experience_records=experience,
        resume_skills=skills,
        projects=projects,
        certifications=certifications,
        achievements=achievements,
        cleaned_text=cleaned_text,
    )

    assert baseline["completeness"]["ratio"] >= 0.8
    assert baseline["completeness"]["sections_present"] >= 6
    assert baseline["work_experience"]["quantified_metrics_count"] >= 1
    assert baseline["technical_skills"]["count"] == 6
    assert baseline["education"]["has_degree"] is True
    assert baseline["achievements"]["ratio"] == 1.0


def test_deterministic_scoring_incomplete_resume():
    """Verify deterministic scoring correctly detects missing sections in a sparse resume."""
    baseline = evaluate_deterministic_baseline(
        personal_info=None,
        education_records=[],
        experience_records=[],
        resume_skills=[],
        projects=[],
        certifications=[],
        achievements=[],
        cleaned_text="Short unformatted text.",
    )

    assert baseline["completeness"]["ratio"] <= 0.1
    assert len(baseline["completeness"]["missing_sections"]) >= 5
    assert baseline["work_experience"]["ratio"] <= 0.2
    assert baseline["technical_skills"]["count"] == 0
    assert baseline["education"]["ratio"] == 0.0


@pytest.mark.asyncio
async def test_quality_score_calculation_flow(db_session):
    """Test full score calculation, Pydantic validation, and DB save with mocked LLM."""
    resume = Resume(
        original_filename="jane_doe_resume.pdf",
        storage_key="resumes/test_jane.pdf",
        file_type="application/pdf",
        file_size=20480,
        processing_status="COMPLETED",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    mock_ai = MagicMock(spec=QualityScoreAIEvaluator)
    mock_ai.model = "qwen2.5:3b"
    mock_ai.base_url = "http://localhost:11434"
    mock_ai.evaluate_resume = AsyncMock(return_value=create_mock_ai_output(0.85))

    service = QualityScoreService(ai_evaluator=mock_ai)
    result = await service.calculate_quality_score(str(resume.id), force_recalculate=True, db=db_session)

    assert result.resume_id == str(resume.id)
    assert 0.0 <= result.overall_score <= 100.0
    assert len(result.category_scores) == 8
    assert result.rating_level in ["Exceptional", "Strong", "Good", "Needs Improvement", "Critical Gaps"]

    # Verify category score details
    for cat_key, cat_data in result.category_scores.items():
        assert cat_data.score <= cat_data.max_score
        assert cat_data.weight_percentage == RUBRIC_CATEGORIES[cat_key].weight

    # Verify database persistence
    saved_db = db_session.query(ResumeQualityScore).filter_by(resume_id=resume.id).first()
    assert saved_db is not None
    assert saved_db.overall_score == result.overall_score
    assert len(saved_db.category_scores) == 8


@pytest.mark.asyncio
async def test_recalculation_updates_record_without_duplicates(db_session):
    """Ensure recalculating a score updates the existing record rather than creating a duplicate."""
    resume = Resume(
        original_filename="alex_resume.pdf",
        storage_key="resumes/test_alex.pdf",
        file_type="application/pdf",
        file_size=15000,
        processing_status="COMPLETED",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    mock_ai = MagicMock(spec=QualityScoreAIEvaluator)
    mock_ai.model = "qwen2.5:3b"
    mock_ai.base_url = "http://localhost:11434"
    mock_ai.evaluate_resume = AsyncMock(return_value=create_mock_ai_output(0.70))

    service = QualityScoreService(ai_evaluator=mock_ai)

    # First run
    res1 = await service.calculate_quality_score(str(resume.id), force_recalculate=True, db=db_session)
    count1 = db_session.query(ResumeQualityScore).filter_by(resume_id=resume.id).count()
    assert count1 == 1

    # Second run with different mock score
    mock_ai.evaluate_resume = AsyncMock(return_value=create_mock_ai_output(0.95))
    res2 = await service.calculate_quality_score(str(resume.id), force_recalculate=True, db=db_session)
    count2 = db_session.query(ResumeQualityScore).filter_by(resume_id=resume.id).count()
    assert count2 == 1
    assert res2.overall_score > res1.overall_score


@pytest.mark.asyncio
async def test_ollama_unavailable_raises_and_never_fabricates(db_session):
    """Verify that when Ollama is unreachable, service raises OllamaUnavailableError and never fabricates fake scores."""
    resume = Resume(
        original_filename="test_ollama_fail.pdf",
        storage_key="resumes/test_ollama.pdf",
        file_type="application/pdf",
        file_size=12000,
        processing_status="COMPLETED",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    mock_ai = MagicMock(spec=QualityScoreAIEvaluator)
    mock_ai.evaluate_resume = AsyncMock(
        side_effect=OllamaUnavailableError("Ollama LLM service is unavailable at http://localhost:11434")
    )

    service = QualityScoreService(ai_evaluator=mock_ai)

    with pytest.raises(OllamaUnavailableError) as exc_info:
        await service.calculate_quality_score(str(resume.id), force_recalculate=True, db=db_session)

    assert "unavailable" in str(exc_info.value).lower()
    # Ensure NO fake score was persisted
    db_record = db_session.query(ResumeQualityScore).filter_by(resume_id=resume.id).first()
    assert db_record is None


@pytest.mark.asyncio
async def test_ai_validation_error_handling(db_session):
    """Verify that invalid AI output format raises AIOutputValidationError."""
    resume = Resume(
        original_filename="test_invalid_ai.pdf",
        storage_key="resumes/test_invalid.pdf",
        file_type="application/pdf",
        file_size=12000,
        processing_status="COMPLETED",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    mock_ai = MagicMock(spec=QualityScoreAIEvaluator)
    mock_ai.evaluate_resume = AsyncMock(
        side_effect=AIOutputValidationError("Model output did not match expected quality score schema")
    )

    service = QualityScoreService(ai_evaluator=mock_ai)

    with pytest.raises(AIOutputValidationError):
        await service.calculate_quality_score(str(resume.id), force_recalculate=True, db=db_session)
