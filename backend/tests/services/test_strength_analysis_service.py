"""
Unit and Integration Tests for Resume Strength Analysis Service
Phase 4 | Feature 22: Resume Strength Analysis
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.schemas.strength_analysis import (
    ResumeStrengthAIStructuredOutput,
    StrengthItemAI,
    STRENGTH_CATEGORIES,
)
from app.services.strength_analysis.service import StrengthAnalysisService
from app.services.strength_analysis.ai_evaluator import (
    StrengthAIEvaluator,
    OllamaUnavailableError,
    AIOutputValidationError,
)
from app.models.resume import Resume
from app.models.strength_analysis import ResumeStrengthAnalysis
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


def create_mock_strength_ai_output(sparse: bool = False) -> ResumeStrengthAIStructuredOutput:
    """Helper to generate a mock structured LLM strength output."""
    if sparse:
        return ResumeStrengthAIStructuredOutput(
            is_sufficient_evidence=False,
            insufficient_evidence_reason="Resume contains insufficient substantive experience, project descriptions, or technical metrics.",
            top_strengths_summary="Insufficient evidence to extract substantiated strengths.",
            strengths=[],
            category_takeaways={},
        )

    return ResumeStrengthAIStructuredOutput(
        is_sufficient_evidence=True,
        insufficient_evidence_reason=None,
        top_strengths_summary="Seasoned backend architect with verified track record optimizing high-throughput distributed microservices and cloud infrastructure.",
        strengths=[
            StrengthItemAI(
                title="Distributed Systems & High-Throughput Engineering",
                category="technical_skills",
                explanation="Demonstrated ability to design scalable microservices handling massive request volume.",
                evidence=["Handled 2M requests daily", "Optimized queries reducing p99 latency by 45%"],
                professional_value="Drives reliability and scale for high-growth enterprise platforms.",
                confidence_level="High",
                strength_type="demonstrated",
            ),
            StrengthItemAI(
                title="Quantified Infrastructure Cost Reduction",
                category="experience",
                explanation="Repeated track record of measuring, optimizing, and reducing cloud overhead.",
                evidence=["Saved $120,000 annually through architectural refactoring"],
                professional_value="Directly impacts corporate bottom line and operational efficiency.",
                confidence_level="High",
                strength_type="demonstrated",
            ),
            StrengthItemAI(
                title="Emerging Machine Learning Model Serving",
                category="projects",
                explanation="Shows active initiative deploying edge machine learning pipelines.",
                evidence=["Built neural network compression pipeline published in IEEE"],
                professional_value="Bridges classical backend software with applied AI deployment.",
                confidence_level="Medium",
                strength_type="potential",
            ),
        ],
        category_takeaways={
            "technical_skills": "Exceptional backend technologies and systems proficiency.",
            "experience": "Demonstrated financial and performance impact.",
            "projects": "Strong technical rigor in published and experimental work.",
        },
    )


def test_strength_categories_catalogue():
    """Verify that all required Feature 22 strength categories exist."""
    assert "technical_skills" in STRENGTH_CATEGORIES
    assert "projects" in STRENGTH_CATEGORIES
    assert "experience" in STRENGTH_CATEGORIES
    assert "education" in STRENGTH_CATEGORIES
    assert "achievements" in STRENGTH_CATEGORIES
    assert "leadership" in STRENGTH_CATEGORIES
    assert "communication" in STRENGTH_CATEGORIES
    assert len(STRENGTH_CATEGORIES) == 7


@pytest.mark.asyncio
async def test_strength_analysis_calculation_flow(db_session):
    """Test full strength analysis calculation, ranking, and database save with mocked LLM."""
    resume = Resume(
        original_filename="alex_backend_resume.pdf",
        storage_key="resumes/test_alex_strength.pdf",
        file_type="application/pdf",
        file_size=24000,
        processing_status="COMPLETED",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    mock_ai = MagicMock(spec=StrengthAIEvaluator)
    mock_ai.model = "qwen2.5:3b"
    mock_ai.base_url = "http://localhost:11434"
    mock_ai.evaluate_strengths = AsyncMock(return_value=create_mock_strength_ai_output(sparse=False))

    service = StrengthAnalysisService(ai_evaluator=mock_ai)
    result = await service.calculate_strength_analysis(str(resume.id), force_recalculate=True, db=db_session)

    assert result.resume_id == str(resume.id)
    assert result.is_sufficient_evidence is True
    assert result.total_strengths_count == 3
    assert result.demonstrated_count == 2
    assert result.potential_count == 1
    assert len(result.strengths) == 3

    # Check rank ordering (demonstrated strengths ranked first)
    assert result.strengths[0].relevance_rank == 1
    assert result.strengths[0].strength_type == "demonstrated"
    assert result.strengths[2].relevance_rank == 3
    assert result.strengths[2].strength_type == "potential"

    # Verify category summaries
    assert "technical_skills" in result.category_summaries
    assert result.category_summaries["technical_skills"].total_strengths >= 1

    # Verify database persistence
    saved_db = db_session.query(ResumeStrengthAnalysis).filter_by(resume_id=resume.id).first()
    assert saved_db is not None
    assert len(saved_db.strengths) == 3
    assert saved_db.is_sufficient_evidence is True


@pytest.mark.asyncio
async def test_strength_analysis_sparse_resume_insufficient_evidence(db_session):
    """Verify that a sparse resume cleanly surfaces insufficient evidence indicators."""
    resume = Resume(
        original_filename="empty_resume.pdf",
        storage_key="resumes/test_empty.pdf",
        file_type="application/pdf",
        file_size=5000,
        processing_status="COMPLETED",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    mock_ai = MagicMock(spec=StrengthAIEvaluator)
    mock_ai.evaluate_strengths = AsyncMock(return_value=create_mock_strength_ai_output(sparse=True))

    service = StrengthAnalysisService(ai_evaluator=mock_ai)
    result = await service.calculate_strength_analysis(str(resume.id), force_recalculate=True, db=db_session)

    assert result.is_sufficient_evidence is False
    assert result.insufficient_evidence_reason is not None
    assert "insufficient" in result.insufficient_evidence_reason.lower()
    assert result.total_strengths_count == 0


@pytest.mark.asyncio
async def test_recalculation_updates_record_without_duplicates(db_session):
    """Ensure recalculating strength analysis updates the existing record instead of creating duplicates."""
    resume = Resume(
        original_filename="dev_recalc.pdf",
        storage_key="resumes/test_recalc.pdf",
        file_type="application/pdf",
        file_size=18000,
        processing_status="COMPLETED",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    mock_ai = MagicMock(spec=StrengthAIEvaluator)
    mock_ai.evaluate_strengths = AsyncMock(return_value=create_mock_strength_ai_output(sparse=False))

    service = StrengthAnalysisService(ai_evaluator=mock_ai)

    # First run
    await service.calculate_strength_analysis(str(resume.id), force_recalculate=True, db=db_session)
    count1 = db_session.query(ResumeStrengthAnalysis).filter_by(resume_id=resume.id).count()
    assert count1 == 1

    # Second run
    await service.calculate_strength_analysis(str(resume.id), force_recalculate=True, db=db_session)
    count2 = db_session.query(ResumeStrengthAnalysis).filter_by(resume_id=resume.id).count()
    assert count2 == 1


@pytest.mark.asyncio
async def test_ollama_unavailable_raises_and_never_fabricates(db_session):
    """Verify that when Ollama is unreachable, service raises OllamaUnavailableError and never fabricates fake strengths."""
    resume = Resume(
        original_filename="fail_ollama.pdf",
        storage_key="resumes/test_fail_ollama.pdf",
        file_type="application/pdf",
        file_size=12000,
        processing_status="COMPLETED",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    mock_ai = MagicMock(spec=StrengthAIEvaluator)
    mock_ai.evaluate_strengths = AsyncMock(
        side_effect=OllamaUnavailableError("Ollama LLM service is unavailable at http://localhost:11434")
    )

    service = StrengthAnalysisService(ai_evaluator=mock_ai)

    with pytest.raises(OllamaUnavailableError) as exc_info:
        await service.calculate_strength_analysis(str(resume.id), force_recalculate=True, db=db_session)

    assert "unavailable" in str(exc_info.value).lower()
    db_record = db_session.query(ResumeStrengthAnalysis).filter_by(resume_id=resume.id).first()
    assert db_record is None
