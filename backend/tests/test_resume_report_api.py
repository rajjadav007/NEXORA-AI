"""
Integration Tests for AI Resume Report Endpoints
Phase 5 | Feature 31: AI Resume Report
"""

import io
import uuid
import pytest
import fitz
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.resume import Resume
from app.models.user import User
from app.models.report import ResumeReport
from app.services.quality_score.ai_evaluator import OllamaUnavailableError

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_pdf_bytes(title: str = "Elena Rostova", extra_text: str = "") -> bytes:
    """Generates a sample PDF resume for testing report generation."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), title)
    page.insert_text((50, 70), "elena.rostova@example.com | (555) 789-0123 | Seattle, WA")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "Senior Full Stack Engineer with 7 years experience in Python, TypeScript, and AWS.")
    page.insert_text((50, 145), "EXPERIENCE")
    page.insert_text((50, 160), "Principal Engineer - CloudScale Inc (2020 - Present)")
    page.insert_text((50, 175), "- Led architectural migration of core monolith to event-driven microservices.")
    page.insert_text((50, 190), "- Increased API throughput by 140% while reducing latency from 220ms to 45ms.")
    if extra_text:
        page.insert_text((50, 210), extra_text)
    page.insert_text((50, 240), "SKILLS")
    page.insert_text((50, 255), "Python, FastAPI, TypeScript, React, PostgreSQL, Docker, Kubernetes, AWS")
    page.insert_text((50, 280), "EDUCATION")
    page.insert_text((50, 295), "M.S. in Computer Science - University of Washington (2019)")

    stream = doc.write()
    doc.close()
    return stream


def _upload_resume(filename: str = "elena_report_test.pdf", extra_text: str = "") -> str:
    """Uploads and saves a resume, returning its permanent resume_id."""
    pdf_bytes = create_sample_pdf_bytes(extra_text=extra_text)
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201, save_res.text
    return save_res.json()["data"]["id"]


def test_generate_report_fallback_deterministic():
    """
    Tests report generation using fallback_to_deterministic=True.
    Validates complete 11-section structured output schema, model info, and status.
    """
    resume_id = _upload_resume(filename="elena_deterministic_report.pdf")

    # Generate report
    res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/reports/generate?fallback_to_deterministic=true&force_recalculate=true"
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert data["resume_id"] == resume_id
    assert data["status"] == "COMPLETED"
    assert data["model"] == settings.OLLAMA_MODEL

    sections = data["sections"]
    # 1. Section A: Executive Summary
    assert "executive_summary" in sections
    assert len(sections["executive_summary"]["overall_assessment"]) > 0

    # 2. Section B: Quality Assessment
    assert "quality_assessment" in sections
    assert "assessment_summary" in sections["quality_assessment"]

    # 3. Section C: Skills Assessment
    assert "skills_assessment" in sections
    assert "distribution_observations" in sections["skills_assessment"]

    # 4. Section D: Experience Assessment
    assert "experience_assessment" in sections
    assert "responsibilities_review" in sections["experience_assessment"]

    # 5. Section E: Education Assessment
    assert "education_assessment" in sections

    # 6. Section F: Projects Assessment
    assert "project_assessment" in sections

    # 7. Section G: Strengths
    assert isinstance(sections["strengths"], list)

    # 8. Section H: Weaknesses
    assert isinstance(sections["weaknesses"], list)

    # 9. Section I: ATS Assessment
    assert "ats_assessment" in sections

    # 10. Section J: Recommendations
    assert isinstance(sections["recommendations"], list)

    # 11. Section K: Final Assessment
    assert "final_assessment" in sections
    assert len(sections["final_assessment"]["top_five_actions"]) == 5


def test_generate_report_ollama_unavailable():
    """
    Validates that when Ollama is unreachable and fallback is False,
    the endpoint raises 503 Service Unavailable with descriptive error.
    """
    resume_id = _upload_resume(filename="elena_unavailable_test.pdf")

    with patch(
        "app.services.report.ai_generator.report_ai_generator.generate_report_sections",
        new_callable=AsyncMock,
        side_effect=OllamaUnavailableError("Ollama LLM service is unavailable at http://localhost:11434."),
    ):
        res = client.post(
            f"{RESUMES_ENDPOINT}/{resume_id}/reports/generate?fallback_to_deterministic=false&force_recalculate=true"
        )
        assert res.status_code == 503, res.text
        assert "unavailable" in res.json()["detail"].lower()


def test_get_report_history_and_latest():
    """
    Validates retrieval of report history and latest report endpoint.
    """
    resume_id = _upload_resume(filename="elena_history_test.pdf")

    # Before generating: /reports/latest returns 404
    res_latest_empty = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/reports/latest")
    assert res_latest_empty.status_code == 404

    # Generate first report
    res1 = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/reports/generate?fallback_to_deterministic=true&force_recalculate=true"
    )
    assert res1.status_code == 200
    report_id1 = res1.json()["data"]["report_id"]

    # Generate second report
    res2 = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/reports/generate?fallback_to_deterministic=true&force_recalculate=true"
    )
    assert res2.status_code == 200
    report_id2 = res2.json()["data"]["report_id"]

    # Check history
    res_hist = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/reports")
    assert res_hist.status_code == 200
    history = res_hist.json()["data"]
    assert len(history) == 2
    assert history[0]["report_id"] == report_id2  # ordered desc

    # Check latest
    res_latest = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/reports/latest")
    assert res_latest.status_code == 200
    assert res_latest.json()["data"]["report_id"] == report_id2

    # Check get by id
    res_by_id = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/reports/{report_id1}")
    assert res_by_id.status_code == 200
    assert res_by_id.json()["data"]["report_id"] == report_id1


def test_unauthorized_report_access_prevention():
    """
    Verifies that foreign users cannot generate or view reports for a private resume (403 Forbidden).
    """
    db = SessionLocal()
    owner_id = str(uuid.uuid4())
    attacker_id = str(uuid.uuid4())
    try:
        owner_user = User(
            id=uuid.UUID(owner_id),
            email=f"report_owner_{uuid.uuid4().hex[:6]}@example.com",
        )
        resume_record = Resume(
            id=uuid.uuid4(),
            user_id=uuid.UUID(owner_id),
            original_filename="private_report_resume.pdf",
            storage_key="storage/resumes/private_report.pdf",
            file_type="pdf",
            file_size=2048,
            processing_status="COMPLETED",
        )
        db.add_all([owner_user, resume_record])
        db.commit()
        res_id = str(resume_record.id)
    finally:
        db.close()

    # Attacker tries to generate report
    res_forbidden = client.post(
        f"{RESUMES_ENDPOINT}/{res_id}/reports/generate?fallback_to_deterministic=true",
        headers={"X-User-Id": attacker_id},
    )
    assert res_forbidden.status_code == 403

    # Owner generates successfully
    res_owner = client.post(
        f"{RESUMES_ENDPOINT}/{res_id}/reports/generate?fallback_to_deterministic=true",
        headers={"X-User-Id": owner_id},
    )
    assert res_owner.status_code == 200


def test_long_resume_handling():
    """
    Validates that a long resume with extensive text excerpts is handled cleanly
    without memory exhaustion or payload blowup.
    """
    long_filler = "Expanded bullet points: Led cross-functional agile sprints, optimized cache layers, improved database queries. " * 50
    resume_id = _upload_resume(filename="long_resume_test.pdf", extra_text=long_filler)

    res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/reports/generate?fallback_to_deterministic=true"
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "COMPLETED"
