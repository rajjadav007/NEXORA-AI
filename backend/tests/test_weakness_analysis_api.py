"""
API Integration Tests for Resume Weakness Analysis Endpoints
Phase 4 | Feature 23: Resume Weakness Analysis
"""

import io
import uuid
import pytest
import fitz
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.schemas.weakness_analysis import (
    ResumeWeaknessAIStructuredOutput,
    WeaknessItemAI,
    MissingItemAI,
)
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_resume_pdf_bytes() -> bytes:
    """Generates a sample PDF resume for testing weaknesses."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Devon Vance")
    page.insert_text((50, 70), "devon.vance@example.com | (555) 234-5678")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "Hardworking team player looking for any software opportunity.")
    page.insert_text((50, 140), "TECHNICAL SKILLS")
    page.insert_text((50, 155), "Python, JavaScript, React, FastAPI, SQL, Git")
    page.insert_text((50, 180), "EXPERIENCE")
    page.insert_text((50, 195), "Software Developer - FinScale Inc")
    page.insert_text((50, 210), "- Responsible for backend development and bug fixing.")
    page.insert_text((50, 225), "- Helped team with testing and writing code.")
    page.insert_text((50, 250), "EDUCATION")
    page.insert_text((50, 265), "B.S. in Computer Science - University of California, Berkeley")
    page.insert_text((50, 290), "PROJECTS")
    page.insert_text((50, 305), "Nexora: A web application.")
    stream = doc.write()
    doc.close()
    return stream


def _upload_and_save_resume(filename: str = "devon_vance_weakness.pdf") -> str:
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


def mock_weakness_ai_output() -> ResumeWeaknessAIStructuredOutput:
    return ResumeWeaknessAIStructuredOutput(
        overall_summary="The resume lacks quantifiable impact metrics and suffers from vague, passive job duty descriptions.",
        weaknesses=[
            WeaknessItemAI(
                title="Passive Duty Descriptions Without Quantified Impact",
                category="experience",
                explanation="Work experience bullets rely on passive responsibilities ('Responsible for backend development') rather than measurable results.",
                evidence=["Responsible for backend development and bug fixing", "Helped team with testing"],
                why_it_matters="Recruiters and hiring managers look for measurable business outcomes rather than job duty checklists.",
                suggested_improvement="Rewrite using Google's X-Y-Z formula: 'Built high-throughput payment API handling 10k RPS, reducing processing errors by 30%'.",
                priority="Critical",
                weakness_type="lacks_measurable_impact",
            ),
            WeaknessItemAI(
                title="Vague Project Description Without Technical Stack or Outcomes",
                category="projects",
                explanation="The Nexora project does not state what technologies were used, candidate's specific contribution, or architecture.",
                evidence=["Nexora: A web application"],
                why_it_matters="Unclear project descriptions make it impossible to evaluate hands-on technical depth.",
                suggested_improvement="Detail architecture, key libraries used, and deployment details (e.g. Docker, PostgreSQL, React).",
                priority="High",
                weakness_type="vague_description",
            ),
            WeaknessItemAI(
                title="Generic Summary Statement",
                category="summary",
                explanation="The professional summary uses cliché buzzwords ('hardworking team player') without highlighting technical specializations.",
                evidence=["Hardworking team player looking for any software opportunity"],
                why_it_matters="Generic summaries fail to differentiate the applicant from hundreds of other candidates.",
                suggested_improvement="Target a specific domain or stack, stating years of focus and key architectural competencies.",
                priority="Medium",
                weakness_type="clarity_issue",
            ),
        ],
        missing_information=[
            MissingItemAI(
                section="Education",
                item="Graduation year / attendance dates",
                relevance="Clarifies timeline and career seniority level.",
                impact_level="High",
                is_optional=False,
            ),
            MissingItemAI(
                section="Projects",
                item="Live URL or GitHub repository links",
                relevance="Allows technical reviewers to inspect code quality and live features.",
                impact_level="Medium",
                is_optional=True,
            ),
        ],
        category_recommendations={
            "experience": "Transform passive bullets into outcome-oriented metrics with specific business impact.",
            "projects": "Expand technical depth and include repository or live demo links.",
            "summary": "Tailor your summary to showcase distinct engineering strengths and target roles.",
        },
    )


def test_weakness_analysis_api_lifecycle():
    """Tests complete weakness analysis API lifecycle: upload, 404 before analyze, analyze, and retrieval."""
    # 1. Upload & save resume
    resume_id = _upload_and_save_resume("test_weakness_lifecycle.pdf")

    # 2. GET before analysis should return 404
    get_res_before = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/weaknesses")
    assert get_res_before.status_code == 404

    # 3. POST /analyze with mocked AI evaluator
    with patch(
        "app.services.weakness_analysis.service.weakness_analysis_service.ai_evaluator.evaluate_weaknesses",
        new=AsyncMock(return_value=mock_weakness_ai_output())
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/weaknesses/analyze?force_recalculate=true")
        assert analyze_res.status_code == 200, analyze_res.text
        data = analyze_res.json()["data"]
        assert data["resume_id"] == resume_id
        assert data["total_weaknesses_count"] == 3
        assert data["priority_breakdown"]["critical"] == 1
        assert data["priority_breakdown"]["high"] == 1
        assert data["priority_breakdown"]["medium"] == 1
        assert len(data["weaknesses"]) == 3

        # Check ranking: Critical first, then High, then Medium
        assert data["weaknesses"][0]["priority"] == "Critical"
        assert data["weaknesses"][0]["relevance_rank"] == 1
        assert data["weaknesses"][1]["priority"] == "High"
        assert data["weaknesses"][1]["relevance_rank"] == 2
        assert data["weaknesses"][2]["priority"] == "Medium"
        assert data["weaknesses"][2]["relevance_rank"] == 3

        # Check missing information separated
        assert len(data["missing_information"]) == 2
        assert data["missing_information"][0]["section"] == "Education"
        assert data["missing_information"][0]["is_optional"] is False
        assert data["missing_information"][1]["is_optional"] is True

        # Check evidence citations
        assert len(data["weaknesses"][0]["evidence"]) >= 1

    # 4. GET /weaknesses should return 200 with saved analysis
    get_res_after = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/weaknesses")
    assert get_res_after.status_code == 200
    retrieved = get_res_after.json()["data"]
    assert retrieved["resume_id"] == resume_id
    assert retrieved["total_weaknesses_count"] == 3
    assert len(retrieved["weaknesses"]) == 3
    assert len(retrieved["missing_information"]) == 2


def test_weakness_analysis_api_non_existent_resume():
    """Verify 404 for non-existent resume ID."""
    fake_id = str(uuid.uuid4())
    res_get = client.get(f"{RESUMES_ENDPOINT}/{fake_id}/weaknesses")
    assert res_get.status_code == 404

    res_post = client.post(f"{RESUMES_ENDPOINT}/{fake_id}/weaknesses/analyze")
    assert res_post.status_code == 404


def test_weakness_analysis_api_ollama_unavailable():
    """Verify 503 error returned when Ollama is unavailable."""
    resume_id = _upload_and_save_resume("test_weakness_unavail.pdf")

    with patch(
        "app.services.weakness_analysis.service.weakness_analysis_service.ai_evaluator.evaluate_weaknesses",
        new=AsyncMock(side_effect=OllamaUnavailableError("Ollama service unavailable"))
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/weaknesses/analyze?force_recalculate=true")
        assert analyze_res.status_code == 503
        assert "unavailable" in analyze_res.json()["detail"].lower()


def test_weakness_analysis_api_invalid_ai_output():
    """Verify 502 error returned when model output is malformed or invalid."""
    resume_id = _upload_and_save_resume("test_weakness_bad_output.pdf")

    with patch(
        "app.services.weakness_analysis.service.weakness_analysis_service.ai_evaluator.evaluate_weaknesses",
        new=AsyncMock(side_effect=AIOutputValidationError("Schema validation failed"))
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/weaknesses/analyze?force_recalculate=true")
        assert analyze_res.status_code == 502
        assert "validation failed" in analyze_res.json()["detail"].lower()
