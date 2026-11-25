"""
Integration Tests for PDF Report Export
Phase 5 | Feature 32: PDF Report Export
"""

import io
import uuid
import pytest
import fitz  # PyMuPDF to inspect exported PDF binary
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.resume import Resume
from app.models.user import User
from app.models.report import ResumeReport

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_pdf_bytes(title: str = "Marcus Vance", extra_text: str = "") -> bytes:
    """Generates a sample PDF resume for testing PDF export."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), title)
    page.insert_text((50, 70), "marcus.vance@example.com | (555) 321-7654 | Austin, TX")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "Staff Software Engineer with 8 years building distributed systems and high-throughput APIs.")
    page.insert_text((50, 145), "EXPERIENCE")
    page.insert_text((50, 160), "Lead Backend Architect - FinTech Corp (2021 - Present)")
    page.insert_text((50, 175), "- Architected distributed transaction engine handling 25,000 req/sec.")
    page.insert_text((50, 190), "- Reduced database p99 query latency by 45% using Redis cluster caching.")
    if extra_text:
        page.insert_text((50, 210), extra_text)
    page.insert_text((50, 240), "SKILLS")
    page.insert_text((50, 255), "Python, Go, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, Terraform, AWS")
    page.insert_text((50, 280), "EDUCATION")
    page.insert_text((50, 295), "B.S. in Computer Science - University of Texas at Austin (2018)")

    stream = doc.write()
    doc.close()
    return stream


def _upload_resume(filename: str = "marcus_export_test.pdf", extra_text: str = "") -> str:
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


def test_export_pdf_success():
    """
    Validates end-to-end PDF export for a saved AI Resume Report:
    - Status 200 OK
    - Content-Type: application/pdf
    - Content-Disposition contains attachment and sanitized filename
    - Valid multi-page PDF structure with all 6 required pages
    - Correct textual content on each page
    """
    resume_id = _upload_resume(filename="marcus_vance_resume.pdf")

    # 1. Generate an AI report first
    gen_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/reports/generate?fallback_to_deterministic=true&force_recalculate=true"
    )
    assert gen_res.status_code == 200, gen_res.text
    report_data = gen_res.json()["data"]
    report_id = report_data["report_id"]

    # 2. Export PDF
    pdf_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/reports/{report_id}/pdf")
    assert pdf_res.status_code == 200, pdf_res.text
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "attachment" in pdf_res.headers["content-disposition"]
    assert "marcus_vance_resume" in pdf_res.headers["content-disposition"]
    assert str(report_id)[:8] in pdf_res.headers["content-disposition"]

    pdf_bytes = pdf_res.content
    assert len(pdf_bytes) > 5000, "PDF size unexpectedly small"

    # 3. Parse and verify with PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert doc.page_count == 6, f"Expected 6 pages, got {doc.page_count}"

    # Verify key text presence on each page
    p1_text = doc.load_page(0).get_text()
    assert "NEXORA AI" in p1_text
    assert "AI Resume Assessment Report" in p1_text
    assert "Executive Summary" in p1_text

    p2_text = doc.load_page(1).get_text()
    assert "Resume Quality Assessment" in p2_text
    assert "OVERALL QUALITY" in p2_text.upper()

    p3_text = doc.load_page(2).get_text()
    assert "Skills Assessment" in p3_text

    p4_text = doc.load_page(3).get_text()
    assert "Strengths & Weaknesses Analysis" in p4_text

    p5_text = doc.load_page(4).get_text()
    assert "Experience, Projects" in p5_text

    p6_text = doc.load_page(5).get_text()
    assert "ATS Assessment" in p6_text
    assert "Top Recommended Actions" in p6_text

    # Verify running footer on all pages
    for i in range(doc.page_count):
        page_text = doc.load_page(i).get_text()
        assert f"Page {i+1} of 6" in page_text
        assert "Confidential - Powered by Nexora AI" in page_text

    doc.close()


def test_export_pdf_missing_report():
    """Validates 404 error when exporting a non-existent report ID."""
    resume_id = _upload_resume(filename="missing_report_test.pdf")
    non_existent_report_id = str(uuid.uuid4())

    res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/reports/{non_existent_report_id}/pdf")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_export_pdf_invalid_uuid():
    """Validates 400 error when report_id is not a valid UUID."""
    resume_id = _upload_resume(filename="invalid_uuid_test.pdf")

    res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/reports/invalid-uuid-string/pdf")
    assert res.status_code == 400
    assert "invalid report id format" in res.json()["detail"].lower()


def test_export_pdf_unauthorized_access():
    """Validates that a user cannot export a report for a resume owned by another user (403)."""
    db = SessionLocal()
    owner_id = str(uuid.uuid4())
    attacker_id = str(uuid.uuid4())
    try:
        owner_user = User(
            id=uuid.UUID(owner_id),
            email=f"pdf_owner_{uuid.uuid4().hex[:6]}@example.com",
        )
        resume_record = Resume(
            id=uuid.uuid4(),
            user_id=uuid.UUID(owner_id),
            original_filename="confidential_resume.pdf",
            storage_key="storage/resumes/confidential.pdf",
            file_type="pdf",
            file_size=2048,
            processing_status="COMPLETED",
        )
        report_record = ResumeReport(
            id=uuid.uuid4(),
            resume_id=resume_record.id,
            user_id=uuid.UUID(owner_id),
            model_name="gemma4:12b",
            report_data={
                "sections": {
                    "executive_summary": {"overall_assessment": "Owner private profile."},
                    "quality_assessment": {"overall_score": 90.0},
                }
            },
            executive_summary="Owner private summary.",
        )
        db.add_all([owner_user, resume_record, report_record])
        db.commit()
        res_id = str(resume_record.id)
        rep_id = str(report_record.id)
    finally:
        db.close()

    # Attacker attempts export -> 403 Forbidden
    res_forbidden = client.get(
        f"{RESUMES_ENDPOINT}/{res_id}/reports/{rep_id}/pdf",
        headers={"X-User-Id": attacker_id},
    )
    assert res_forbidden.status_code == 403

    # Owner attempts export -> 200 OK
    res_owner = client.get(
        f"{RESUMES_ENDPOINT}/{res_id}/reports/{rep_id}/pdf",
        headers={"X-User-Id": owner_id},
    )
    assert res_owner.status_code == 200
    assert res_owner.headers["content-type"] == "application/pdf"


def test_export_does_not_regenerate_report():
    """
    Validates rule #7 & #10:
    Exporting a PDF must NEVER trigger AI report regeneration or insert new report records.
    """
    resume_id = _upload_resume(filename="no_regen_test.pdf")

    # Generate initial report
    gen_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/reports/generate?fallback_to_deterministic=true"
    )
    assert gen_res.status_code == 200
    report_id = gen_res.json()["data"]["report_id"]

    # Count reports in DB
    db = SessionLocal()
    try:
        count_before = db.query(ResumeReport).filter(ResumeReport.resume_id == uuid.UUID(resume_id)).count()
    finally:
        db.close()

    # Export PDF twice
    res1 = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/reports/{report_id}/pdf")
    res2 = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/reports/{report_id}/pdf")
    assert res1.status_code == 200
    assert res2.status_code == 200

    # Verify no new report records created
    db = SessionLocal()
    try:
        count_after = db.query(ResumeReport).filter(ResumeReport.resume_id == uuid.UUID(resume_id)).count()
    finally:
        db.close()

    assert count_before == count_after, "PDF export should not create new report records"
