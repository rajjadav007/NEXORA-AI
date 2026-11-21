"""
API Integration Tests for Resume Strength Analysis Endpoints
Phase 4 | Feature 22: Resume Strength Analysis
"""

import io
import uuid
import pytest
import fitz
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.schemas.strength_analysis import (
    ResumeStrengthAIStructuredOutput,
    StrengthItemAI,
)
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_resume_pdf_bytes() -> bytes:
    """Generates a sample PDF resume for testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Devon Vance")
    page.insert_text((50, 70), "devon.vance@example.com | (555) 234-5678 | San Francisco, CA")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "Full Stack Software Engineer with 5 years experience designing scalable web services.")
    page.insert_text((50, 140), "TECHNICAL SKILLS")
    page.insert_text((50, 155), "Python, JavaScript, React, FastAPI, PostgreSQL, Docker, AWS")
    page.insert_text((50, 180), "EXPERIENCE")
    page.insert_text((50, 195), "Senior Software Engineer - FinScale Inc (2021 - Present)")
    page.insert_text((50, 210), "- Spearheaded high-volume transaction pipeline handling 2M requests daily.")
    page.insert_text((50, 225), "- Optimized database queries reducing p99 latency by 45%.")
    page.insert_text((50, 250), "EDUCATION")
    page.insert_text((50, 265), "B.S. in Computer Science - University of California, Berkeley (2017 - 2021)")
    page.insert_text((50, 290), "PROJECTS")
    page.insert_text((50, 305), "Nexora Analytics Engine: Open-source metrics aggregation platform.")
    stream = doc.write()
    doc.close()
    return stream


def _upload_and_save_resume(filename: str = "devon_vance_strength.pdf") -> str:
    """Helper to upload and persist a resume, returning its permanent resume_id."""
    pdf_bytes = create_sample_resume_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201, save_res.text
    return save_res.json()["data"]["id"]


def mock_strength_ai_output() -> ResumeStrengthAIStructuredOutput:
    return ResumeStrengthAIStructuredOutput(
        is_sufficient_evidence=True,
        insufficient_evidence_reason=None,
        top_strengths_summary="High-impact full stack engineer with demonstrable backend scalability results.",
        strengths=[
            StrengthItemAI(
                title="Distributed Systems Engineering",
                category="technical_skills",
                explanation="Demonstrated capability engineering high-volume APIs handling millions of daily requests.",
                evidence=["2M requests daily", "FastAPI, PostgreSQL, AWS"],
                professional_value="Enables high-reliability cloud product operations.",
                confidence_level="High",
                strength_type="demonstrated",
            ),
            StrengthItemAI(
                title="Database Latency Optimization",
                category="experience",
                explanation="Direct experience diagnosing and resolving database performance bottlenecks.",
                evidence=["Reduced p99 latency by 45%"],
                professional_value="Reduces cloud infrastructure spend and improves user responsiveness.",
                confidence_level="High",
                strength_type="demonstrated",
            ),
        ],
        category_takeaways={
            "technical_skills": "Core proficiency in modern cloud-native web backends.",
            "experience": "Strong operational metrics and quantifiable latency wins.",
        },
    )


def test_strength_analysis_api_lifecycle():
    """Tests complete strength analysis API lifecycle: upload, 404 before analyze, analyze, and retrieval."""
    # 1. Upload & save resume
    resume_id = _upload_and_save_resume("test_strength_lifecycle.pdf")

    # 2. GET before analysis should return 404
    get_res_before = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/strengths")
    assert get_res_before.status_code == 404

    # 3. POST /analyze with mocked AI evaluator
    with patch(
        "app.services.strength_analysis.service.strength_analysis_service.ai_evaluator.evaluate_strengths",
        new=AsyncMock(return_value=mock_strength_ai_output())
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/strengths/analyze?force_recalculate=true")
        assert analyze_res.status_code == 200, analyze_res.text
        data = analyze_res.json()["data"]
        assert data["resume_id"] == resume_id
        assert data["total_strengths_count"] == 2
        assert data["demonstrated_count"] == 2
        assert len(data["strengths"]) == 2
        assert data["strengths"][0]["title"] == "Distributed Systems Engineering"
        assert len(data["strengths"][0]["evidence"]) >= 1

    # 4. GET /strengths should return 200 with saved analysis
    get_res_after = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/strengths")
    assert get_res_after.status_code == 200
    retrieved = get_res_after.json()["data"]
    assert retrieved["resume_id"] == resume_id
    assert retrieved["total_strengths_count"] == 2
    assert len(retrieved["strengths"]) == 2


def test_strength_analysis_api_non_existent_resume():
    """Verify 404 for non-existent resume ID."""
    fake_id = str(uuid.uuid4())
    res_get = client.get(f"{RESUMES_ENDPOINT}/{fake_id}/strengths")
    assert res_get.status_code == 404

    res_post = client.post(f"{RESUMES_ENDPOINT}/{fake_id}/strengths/analyze")
    assert res_post.status_code == 404


def test_strength_analysis_api_ollama_unavailable():
    """Verify 503 error returned when Ollama is unavailable."""
    resume_id = _upload_and_save_resume("test_strength_unavail.pdf")

    with patch(
        "app.services.strength_analysis.service.strength_analysis_service.ai_evaluator.evaluate_strengths",
        new=AsyncMock(side_effect=OllamaUnavailableError("Ollama service unavailable"))
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/strengths/analyze?force_recalculate=true")
        assert analyze_res.status_code == 503
        assert "unavailable" in analyze_res.json()["detail"].lower()


def test_strength_analysis_api_invalid_ai_output():
    """Verify 502 error returned when model output is malformed or invalid."""
    resume_id = _upload_and_save_resume("test_strength_bad_output.pdf")

    with patch(
        "app.services.strength_analysis.service.strength_analysis_service.ai_evaluator.evaluate_strengths",
        new=AsyncMock(side_effect=AIOutputValidationError("Schema validation failed"))
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/strengths/analyze?force_recalculate=true")
        assert analyze_res.status_code == 502
        assert "validation failed" in analyze_res.json()["detail"].lower()
