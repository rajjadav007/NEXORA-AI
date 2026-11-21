"""
API Integration Tests for Resume Quality Score Endpoints
Phase 4 | Feature 21: Resume Quality Score Engine
"""

import io
import uuid
import pytest
import fitz
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.schemas.quality_score import (
    ResumeQualityAIStructuredOutput,
    CategoryEvaluationAI,
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


def mock_ai_quality_output(ratio: float = 0.82) -> ResumeQualityAIStructuredOutput:
    def _cat(name: str):
        return CategoryEvaluationAI(
            score_ratio=ratio,
            explanation=f"Demonstrated solid competency in {name} with clear technical context.",
            strengths=[f"Strong presentation of {name}"],
            improvements=[f"Add deeper quantitative evidence to {name}"],
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
        top_strengths=["Clear technical stack", "Quantified performance improvements"],
        missing_critical_information=[],
        priority_improvements=["Include live links to project demonstrations"],
    )


def _upload_and_save_resume(filename: str = "devon_vance_resume.pdf") -> str:
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


def test_quality_score_api_lifecycle():
    """Tests the complete quality score API lifecycle: upload, 404 before analyze, analyze, and retrieval."""
    # 1. Upload and save a resume
    resume_id = _upload_and_save_resume("devon_vance_resume.pdf")

    # 2. GET before analysis should return 404
    get_res_before = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/quality-score")
    assert get_res_before.status_code == 404

    # 3. POST /analyze with mocked AI evaluator
    with patch(
        "app.services.quality_score.service.quality_score_service.ai_evaluator.evaluate_resume",
        new=AsyncMock(return_value=mock_ai_quality_output(0.85))
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/quality-score/analyze?force_recalculate=true")
        assert analyze_res.status_code == 200, analyze_res.text
        data = analyze_res.json()["data"]
        assert data["resume_id"] == resume_id
        assert 0.0 <= data["overall_score"] <= 100.0
        assert data["rating_level"] in ["Exceptional", "Strong", "Good", "Needs Improvement", "Critical Gaps"]
        assert len(data["category_scores"]) == 8
        assert "completeness" in data["category_scores"]
        assert "work_experience" in data["category_scores"]
        assert "technical_skills" in data["category_scores"]
        assert len(data["strengths"]) >= 1
        assert len(data["improvement_suggestions"]) >= 1

    # 4. GET /quality-score should now return 200 with saved record
    get_res_after = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/quality-score")
    assert get_res_after.status_code == 200
    retrieved = get_res_after.json()["data"]
    assert retrieved["resume_id"] == resume_id
    assert retrieved["overall_score"] == data["overall_score"]
    assert len(retrieved["category_scores"]) == 8


def test_quality_score_api_non_existent_resume():
    """Verify 404 for non-existent resume ID."""
    fake_id = str(uuid.uuid4())
    res_get = client.get(f"{RESUMES_ENDPOINT}/{fake_id}/quality-score")
    assert res_get.status_code == 404

    res_post = client.post(f"{RESUMES_ENDPOINT}/{fake_id}/quality-score/analyze")
    assert res_post.status_code == 404


def test_quality_score_api_ollama_unavailable():
    """Verify 503 error returned when Ollama is unavailable without fabricating fake data."""
    resume_id = _upload_and_save_resume("test_unavail.pdf")

    with patch(
        "app.services.quality_score.service.quality_score_service.ai_evaluator.evaluate_resume",
        new=AsyncMock(side_effect=OllamaUnavailableError("Ollama service unavailable"))
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/quality-score/analyze?force_recalculate=true")
        assert analyze_res.status_code == 503
        assert "unavailable" in analyze_res.json()["detail"].lower()


def test_quality_score_api_invalid_ai_output():
    """Verify 502 error returned when model output is malformed or invalid."""
    resume_id = _upload_and_save_resume("test_bad_output.pdf")

    with patch(
        "app.services.quality_score.service.quality_score_service.ai_evaluator.evaluate_resume",
        new=AsyncMock(side_effect=AIOutputValidationError("Schema mismatch"))
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/quality-score/analyze?force_recalculate=true")
        assert analyze_res.status_code == 502
        assert "schema mismatch" in analyze_res.json()["detail"].lower()
