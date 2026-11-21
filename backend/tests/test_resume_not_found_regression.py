"""
Regression Tests for Phase 3 Resume Not Found Issue & Ownership Verification
Verifies:
1. Missing/unpersisted UUID (such as c1ef1bd8-b268-4159-97aa-030845e99a8a) returns 404 across all Phase 3 endpoints.
2. Uploaded resume auto-persists to DB and immediately provides canonical UUID accessible by all Phase 3 endpoints.
3. Ownership check returns 403 Forbidden when requested with another user's identifier.
4. Deletion of resume causes immediate 404 across all Phase 3 endpoints.
"""

import io
import uuid
import pytest
import fitz
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.config import settings
from app.database.session import get_db
from app.models.resume import Resume

client = TestClient(app)
MISSING_UUID = "c1ef1bd8-b268-4159-97aa-030845e99a8a"
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_dummy_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Jane Doe")
    page.insert_text((50, 70), "jane.doe@example.com | (555) 123-4567 | San Francisco, CA")
    page.insert_text((50, 100), "EDUCATION")
    page.insert_text((50, 120), "Stanford University - B.S. Computer Science, 2020")
    page.insert_text((50, 150), "EXPERIENCE")
    page.insert_text((50, 170), "Software Engineer at Tech Corp (2020 - Present)")
    page.insert_text((50, 190), "- Built distributed backend microservices in Python and Go.")
    page.insert_text((50, 220), "SKILLS")
    page.insert_text((50, 240), "Python, FastAPI, PostgreSQL, Docker, Kubernetes, React")
    page.insert_text((50, 270), "PROJECTS")
    page.insert_text((50, 290), "Project Alpha: Open source cloud orchestrator.")
    page.insert_text((50, 320), "CERTIFICATIONS")
    page.insert_text((50, 340), "AWS Certified Developer - Associate (2022)")
    stream = doc.write()
    doc.close()
    return stream


def test_missing_uuid_returns_404_across_all_phase3_endpoints():
    """Verify exact user-reported UUID returns 404 detail across Phase 3 modules."""
    endpoints = [
        ("GET", f"{RESUMES_ENDPOINT}/{MISSING_UUID}/education"),
        ("GET", f"{RESUMES_ENDPOINT}/{MISSING_UUID}/experience"),
        ("GET", f"{RESUMES_ENDPOINT}/{MISSING_UUID}/personal-info"),
        ("GET", f"{RESUMES_ENDPOINT}/{MISSING_UUID}/skills"),
        ("GET", f"{RESUMES_ENDPOINT}/{MISSING_UUID}/projects"),
        ("GET", f"{RESUMES_ENDPOINT}/{MISSING_UUID}/certifications"),
        ("GET", f"{RESUMES_ENDPOINT}/{MISSING_UUID}/achievements"),
    ]

    for method, url in endpoints:
        resp = client.request(method, url)
        assert resp.status_code == 404, f"{url} expected 404, got {resp.status_code}"
        assert f"Resume not found: {MISSING_UUID}" in resp.json()["detail"]


def test_upload_auto_persists_canonical_id_for_phase3():
    """Verify uploading a resume returns a canonical UUID that exists in DB and works across Phase 3."""
    pdf_bytes = create_dummy_pdf()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("JaneDoeResume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()["data"]
    resume_id = upload_data["upload_id"]
    assert resume_id is not None

    # Check DB record exists
    db_gen = get_db()
    db = next(db_gen)
    resume_db = db.execute(select(Resume).where(Resume.id == uuid.UUID(resume_id))).scalar_one_or_none()
    assert resume_db is not None, "Resume was not auto-persisted to DB"

    # All Phase 3 endpoints now successfully recognize the resume
    edu_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/education")
    assert edu_res.status_code == 200

    exp_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/experience")
    assert exp_res.status_code == 200

    pi_extract = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/personal-info/extract")
    assert pi_extract.status_code == 200

    pi_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/personal-info")
    assert pi_res.status_code == 200

    skills_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/skills")
    assert skills_res.status_code == 200

    proj_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/projects")
    assert proj_res.status_code == 200

    cert_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/certifications")
    assert cert_res.status_code == 200


def test_unauthorized_access_rejected_with_403():
    """Verify that an unauthorized user attempting to access someone else's resume gets 403."""
    user_a_id = str(uuid.uuid4())
    user_b_id = str(uuid.uuid4())
    user_a_email = f"user_a_{uuid.uuid4().hex[:8]}@example.com"

    pdf_bytes = create_dummy_pdf()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("UserAResume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["data"]["upload_id"]

    # Save / associate with User A
    save_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/save",
        json={"resume_id": resume_id, "user_id": user_a_id, "user_email": user_a_email},
    )
    assert save_res.status_code in (200, 201)

    # User A accesses: OK
    res_a = client.get(
        f"{RESUMES_ENDPOINT}/{resume_id}/education",
        headers={"X-User-Id": user_a_id},
    )
    assert res_a.status_code == 200

    # User B accesses: 403 Forbidden
    res_b = client.get(
        f"{RESUMES_ENDPOINT}/{resume_id}/education",
        headers={"X-User-Id": user_b_id},
    )
    assert res_b.status_code == 403
    assert f"Access denied: You do not own resume {resume_id}" in res_b.json()["detail"]


def test_deleted_resume_returns_404():
    """Verify that deleted resume returns 404 across Phase 3."""
    pdf_bytes = create_dummy_pdf()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("ToDelete.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    resume_id = upload_res.json()["data"]["upload_id"]

    # Delete resume
    del_res = client.delete(f"{RESUMES_ENDPOINT}/{resume_id}")
    assert del_res.status_code == 200

    # Phase 3 requests return 404
    res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/experience")
    assert res.status_code == 404
    assert f"Resume not found: {resume_id}" in res.json()["detail"]
