"""
Integration Tests for Personal Information Extraction API
Phase 3 | Feature 13: Personal Information Extraction
"""

import io
import uuid
import pytest
import fitz
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.config import settings
from app.services.storage import staging_service
from app.models.personal_information import ResumePersonalInformation

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_resume_pdf_bytes(
    name: str = "Raj Jadav",
    location: str = "Bengaluru, Karnataka, India",
    email: str = "raj.jadav@example.com",
    phone: str = "+91 9876543210",
    linkedin: str = "https://linkedin.com/in/rajjadav",
    github: str = "https://github.com/rajjadav",
) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), name)
    page.insert_text((50, 70), location)
    page.insert_text((50, 90), f"Email: {email} | Phone: {phone}")
    page.insert_text((50, 110), f"LinkedIn: {linkedin} | GitHub: {github}")
    page.insert_text((50, 140), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 160), "Software engineer with 5 years experience in building AI platforms.")
    stream = doc.write()
    doc.close()
    return stream


def test_personal_info_extraction_and_lifecycle():
    pdf_bytes = create_resume_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("CandidateResume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    staging_id = upload_res.json()["data"]["upload_id"]

    try:
        # Save to permanent storage and DB
        save_res = client.post(
            f"{RESUMES_ENDPOINT}/{staging_id}/save",
            json={"user_email": "candidate@nexora.ai"},
        )
        assert save_res.status_code == 201
        resume_id = save_res.json()["data"]["id"]

        # 1. Extract personal information
        extract_res = client.post(
            f"{RESUMES_ENDPOINT}/{resume_id}/personal-info/extract"
        )
        assert extract_res.status_code == 200
        body = extract_res.json()
        assert body["success"] is True
        data = body["data"]

        assert data["full_name"] == "Raj Jadav"
        assert data["first_name"] == "Raj"
        assert data["last_name"] == "Jadav"
        assert data["email"] == "raj.jadav@example.com"
        assert data["phone"] == "+91 9876543210"
        assert data["country_code"] == "+91"
        assert data["location"] is not None
        assert data["location"]["city"] == "Bengaluru"
        assert data["linkedin_url"] == "https://linkedin.com/in/rajjadav"
        assert data["github_url"] == "https://github.com/rajjadav"
        assert data["extraction_status"] == "completed"
        assert data["confidence"]["email"] == 1.0
        assert data["confidence"]["phone"] == 0.95

        # 2. Retrieve extracted information (GET)
        get_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/personal-info")
        assert get_res.status_code == 200
        get_data = get_res.json()["data"]
        assert get_data["email"] == "raj.jadav@example.com"
        assert get_data["full_name"] == "Raj Jadav"

        # 3. Manual update (PATCH)
        patch_res = client.patch(
            f"{RESUMES_ENDPOINT}/{resume_id}/personal-info",
            json={
                "full_name": "Rajesh Jadav",
                "phone": "+91 9999988888",
            },
        )
        assert patch_res.status_code == 200
        patched_data = patch_res.json()["data"]
        assert patched_data["full_name"] == "Rajesh Jadav"
        assert patched_data["phone"] == "+91 9999988888"
        assert patched_data["is_manually_edited"] is True
        assert "full_name" in patched_data["manually_edited_fields"]
        assert "phone" in patched_data["manually_edited_fields"]

        # 4. Reprocess extraction - verify manual corrections are PROTECTED
        reprocess_res = client.post(
            f"{RESUMES_ENDPOINT}/{resume_id}/personal-info/reprocess"
        )
        assert reprocess_res.status_code == 200
        reprocessed_data = reprocess_res.json()["data"]
        # Manually edited name and phone must NOT be overwritten!
        assert reprocessed_data["full_name"] == "Rajesh Jadav"
        assert reprocessed_data["phone"] == "+91 9999988888"
        # Other non-edited fields remain intact
        assert reprocessed_data["email"] == "raj.jadav@example.com"

        # 5. Reprocess with force_overwrite=true - verify manual edits can be reset
        force_res = client.post(
            f"{RESUMES_ENDPOINT}/{resume_id}/personal-info/reprocess?force_overwrite=true"
        )
        assert force_res.status_code == 200
        force_data = force_res.json()["data"]
        assert force_data["full_name"] == "Raj Jadav"
        assert force_data["is_manually_edited"] is False

    finally:
        staging_service.cleanup_file(staging_id)
        if "resume_id" in locals():
            client.delete(f"{RESUMES_ENDPOINT}/{resume_id}")


def test_personal_info_staged_preview_extraction():
    """Verify extraction works on staged resumes before permanent DB save."""
    pdf_bytes = create_resume_pdf_bytes("Staged Candidate", "Mumbai, Maharashtra, India", "staged@example.com")
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("StagedResume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    staging_id = upload_res.json()["data"]["upload_id"]

    try:
        extract_res = client.post(
            f"{RESUMES_ENDPOINT}/{staging_id}/personal-info/extract"
        )
        assert extract_res.status_code == 200
        data = extract_res.json()["data"]
        assert data["full_name"] == "Staged Candidate"
        assert data["email"] == "staged@example.com"
    finally:
        staging_service.cleanup_file(staging_id)


def test_personal_info_security_and_error_handling():
    # 1. Invalid resume_id security check
    res_bad = client.get(f"{RESUMES_ENDPOINT}/..%2F..%2Fetc/personal-info")
    assert res_bad.status_code in (400, 404)

    # 2. Non-existent UUID
    fake_id = str(uuid.uuid4())
    res_404 = client.get(f"{RESUMES_ENDPOINT}/{fake_id}/personal-info")
    assert res_404.status_code == 404
