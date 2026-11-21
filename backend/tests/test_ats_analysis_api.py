"""
API Integration Tests for Resume ATS Compatibility Analysis Endpoints
Phase 4 | Feature 24: ATS Compatibility Analysis
"""

import io
import uuid
import pytest
import fitz
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.schemas.ats_analysis import (
    AIFeedback,
    RecommendationItem,
)

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_resume_pdf_bytes(multi_column: bool = False) -> bytes:
    """Generates a sample PDF resume for testing ATS compatibility."""
    doc = fitz.open()
    page = doc.new_page()

    if multi_column:
        # Create distinct left and right columns with overlapping vertical range
        page.insert_text((50, 100), "Left Column: Senior Software Engineer at TechCorp\nEngineered backend services.")
        page.insert_text((300, 100), "Right Column: Skills\nPython, Docker, AWS, React, Kubernetes.")
    else:
        # Standard clean single-column layout
        page.insert_text((50, 50), "Devon Vance")
        page.insert_text((50, 70), "devon.vance@example.com | (555) 234-5678 | San Francisco, CA | https://linkedin.com/in/devon")
        page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
        page.insert_text((50, 115), "Results-driven Senior Full Stack Software Engineer with 6+ years of experience designing scalable distributed web platforms, reducing cloud infrastructure latency, and leading cross-functional developer teams.")
        page.insert_text((50, 145), "WORK EXPERIENCE")
        page.insert_text((50, 160), "Senior Software Engineer - FinScale Inc (Jan 2021 - Present)")
        page.insert_text((50, 175), "- Engineered microservices architecture handling 3M daily transactions using FastAPI and PostgreSQL.")
        page.insert_text((50, 190), "- Optimized database query indexes reducing p99 response latency by 45%.")
        page.insert_text((50, 205), "- Spearheaded automated CI/CD pipeline deployments reducing release cycles by 60%.")
        page.insert_text((50, 235), "EDUCATION")
        page.insert_text((50, 250), "Bachelor of Science in Computer Science - University of California, Berkeley (2017 - 2021)")
        page.insert_text((50, 280), "TECHNICAL SKILLS")
        page.insert_text((50, 295), "Languages & Frameworks: Python, JavaScript, TypeScript, React, FastAPI, Node.js, SQL")
        page.insert_text((50, 310), "Cloud & DevOps: Docker, Kubernetes, AWS, PostgreSQL, Redis, Git, Linux")
        page.insert_text((50, 335), "PROJECTS")
        page.insert_text((50, 350), "Nexora AI Platform: Full-stack AI-driven analytics dashboard built with React and FastAPI.")

    stream = doc.write()
    doc.close()
    return stream


def _upload_and_save_resume(filename: str = "devon_vance_ats.pdf", multi_column: bool = False) -> str:
    """Helper to upload and persist a resume, returning its permanent resume_id."""
    pdf_bytes = create_sample_resume_pdf_bytes(multi_column=multi_column)
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201, save_res.text
    return save_res.json()["data"]["id"]


def test_ats_analysis_api_lifecycle():
    """Tests complete ATS analysis API lifecycle: upload, 404 before analyze, analyze, and retrieval."""
    # 1. Upload & save resume
    resume_id = _upload_and_save_resume("test_ats_lifecycle.pdf")

    # 2. GET before analysis should return 404
    get_res_before = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/ats")
    assert get_res_before.status_code == 404

    # 3. POST /ats/analyze
    analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/ats/analyze?force_recalculate=true")
    assert analyze_res.status_code == 200, analyze_res.text
    data = analyze_res.json()["data"]

    assert data["resume_id"] == resume_id
    assert 0 <= data["ats_score"] <= 100
    assert data["score_grade"] in ["Excellent", "Good", "Needs Work", "Poor"]

    # Check 8 categories present
    assert "contact_info" in data["category_scores"]
    assert "standard_sections" in data["category_scores"]
    assert "experience_formatting" in data["category_scores"]
    assert "education_structure" in data["category_scores"]
    assert "skills_presentation" in data["category_scores"]
    assert "professional_summary" in data["category_scores"]
    assert "credentials_projects" in data["category_scores"]
    assert "formatting_parsing_safety" in data["category_scores"]

    # Verify disclaimer is present (non-affiliation)
    assert "disclaimer" in data
    assert "not replicate" in data["disclaimer"].lower() or "heuristic" in data["disclaimer"].lower()

    # Check keyword findings
    assert data["keyword_findings"]["total_detected_keywords"] >= 1

    # 4. GET /ats should return 200 with saved analysis
    get_res_after = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/ats")
    assert get_res_after.status_code == 200
    retrieved = get_res_after.json()["data"]
    assert retrieved["resume_id"] == resume_id
    assert retrieved["ats_score"] == data["ats_score"]
    assert retrieved["score_grade"] == data["score_grade"]


def test_ats_analysis_distinguishes_issues_and_risks():
    """Tests that verified issues and formatting risks are separated with correct issue_type."""
    resume_id = _upload_and_save_resume("test_ats_types.pdf")

    analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/ats/analyze?force_recalculate=true")
    assert analyze_res.status_code == 200
    data = analyze_res.json()["data"]

    for issue in data["verified_issues"]:
        assert issue["issue_type"] == "verified_issue"
        assert issue["severity"] in ["Critical", "Warning", "Info"]
        assert len(issue["suggested_fix"]) > 0

    for risk in data["formatting_risks"]:
        assert risk["issue_type"] == "formatting_risk"
        assert risk["severity"] in ["Critical", "Warning", "Info"]
        assert len(risk["suggested_fix"]) > 0


def test_ats_analysis_non_existent_resume():
    """Verify 404 for non-existent resume ID."""
    fake_id = str(uuid.uuid4())
    res_get = client.get(f"{RESUMES_ENDPOINT}/{fake_id}/ats")
    assert res_get.status_code == 404

    res_post = client.post(f"{RESUMES_ENDPOINT}/{fake_id}/ats/analyze")
    assert res_post.status_code == 404


def test_ats_analysis_ai_offline_fallback():
    """Tests that deterministic ATS scoring still succeeds if Ollama AI is offline."""
    resume_id = _upload_and_save_resume("test_ats_offline.pdf")

    with patch(
        "app.services.ats_analysis.service.ats_analysis_service.ai_evaluator.generate_feedback",
        new=AsyncMock(return_value=AIFeedback(
            executive_summary="Deterministic fallback summary.",
            tailored_recommendations=[
                RecommendationItem(
                    title="Formatting optimization",
                    category="Layout",
                    priority="Medium",
                    current_state="Current format",
                    recommended_rewrite="Clean format",
                )
            ],
            keyword_optimization_advice="Incorporate relevant technical keywords.",
        ))
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/ats/analyze?force_recalculate=true")
        assert analyze_res.status_code == 200
        data = analyze_res.json()["data"]
        assert data["ats_score"] > 0
        assert "fallback" in data["ai_feedback"]["executive_summary"].lower()
