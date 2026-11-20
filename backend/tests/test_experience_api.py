"""
Integration Tests for Experience Analysis API
Phase 3 | Feature 15: Experience Analysis
"""

import io
import uuid
import pytest
import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_experience_resume_pdf_bytes() -> bytes:
    """Generates a test PDF resume with rich work experience sections."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Raj Jadav")
    page.insert_text((50, 70), "Bengaluru, Karnataka, India | raj.jadav@example.com")
    page.insert_text((50, 100), "PROFESSIONAL EXPERIENCE")
    page.insert_text((50, 120), "Acme Systems | Senior AI Engineer")
    page.insert_text((50, 140), "Bengaluru, India")
    page.insert_text((50, 160), "01/2024 - Present")
    page.insert_text((50, 180), "- Architected backend pipelines with FastAPI and Docker")
    page.insert_text((50, 200), "- Improved API response times by 35%")
    page.insert_text((50, 230), "Beta Labs | AI Engineer Intern")
    page.insert_text((50, 250), "Bengaluru, India")
    page.insert_text((50, 270), "06/2023 - 12/2023")
    page.insert_text((50, 290), "- Developed Python machine learning models using PyTorch")
    page.insert_text((50, 320), "EDUCATION")
    page.insert_text((50, 340), "Bachelor of Computer Applications")
    page.insert_text((50, 360), "Bangalore University, 2020 - 2023")
    stream = doc.write()
    doc.close()
    return stream


def test_experience_api_full_lifecycle():
    # 1. Upload resume
    pdf_bytes = create_experience_resume_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("ExperienceResume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    staging_id = upload_res.json()["data"]["upload_id"]

    # 2. Save resume permanently to DB
    save_res = client.post(
        f"{RESUMES_ENDPOINT}/{staging_id}/save",
        json={"user_email": "candidate.exp@nexora.ai"},
    )
    assert save_res.status_code == 201
    resume_id = save_res.json()["data"]["id"]

    # 3. Extract experience (POST /resumes/{resume_id}/experience/extract)
    extract_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/experience/extract")
    assert extract_res.status_code == 200
    extract_body = extract_res.json()
    assert extract_body["success"] is True
    entries = extract_body["data"]
    assert len(entries) >= 2

    # Verify structured fields
    acme_entry = next((e for e in entries if "Acme" in (e.get("company") or "")), None)
    assert acme_entry is not None
    assert "Senior AI Engineer" in acme_entry["job_title"]
    assert acme_entry["employment_type"] == "full_time"
    assert acme_entry["is_current"] is True
    assert acme_entry["end_date"] is None
    assert "FastAPI" in acme_entry["technologies"] or "Docker" in acme_entry["technologies"]
    assert acme_entry["is_manually_edited"] is False

    beta_entry = next((e for e in entries if "Beta" in (e.get("company") or "")), None)
    assert beta_entry is not None
    assert beta_entry["employment_type"] == "internship"
    assert beta_entry["start_date"] == "2023-06"
    assert beta_entry["end_date"] == "2023-12"

    # 4. Retrieve experience entries (GET /resumes/{resume_id}/experience)
    get_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/experience")
    assert get_res.status_code == 200
    get_body = get_res.json()
    assert get_body["success"] is True
    assert len(get_body["data"]) >= 2
    assert get_body.get("summary") is not None
    assert get_body["summary"]["employment_count"] >= 2

    # 5. Add a manual experience entry (POST /resumes/{resume_id}/experience)
    manual_payload = {
        "company": "Gamma Startups",
        "job_title": "Freelance Cloud Engineer",
        "employment_type": "freelance",
        "location": "Remote",
        "start_date": "2022-01",
        "end_date": "2022-12",
        "is_current": False,
        "responsibilities": ["Configured AWS infrastructure"],
        "technologies": ["AWS", "Terraform", "Docker"],
        "achievements": ["Deployed resilient microservices"],
    }
    add_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/experience", json=manual_payload)
    assert add_res.status_code == 201
    added_entry = add_res.json()["data"]
    assert added_entry["company"] == "Gamma Startups"
    assert added_entry["is_manually_edited"] is True
    manual_exp_id = added_entry["id"]

    # 6. Update manual entry (PATCH /resumes/{resume_id}/experience/{experience_id})
    update_res = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/experience/{manual_exp_id}",
        json={"location": "Global Remote"},
    )
    assert update_res.status_code == 200
    updated_entry = update_res.json()["data"]
    assert updated_entry["location"] == "Global Remote"
    assert updated_entry["is_manually_edited"] is True

    # 7. Test Reprocess (Test Case 13 & 14):
    # Reprocess without force_overwrite must preserve manual entry and not duplicate entries
    reprocess_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/experience/reprocess",
        json={"force_overwrite": False},
    )
    assert reprocess_res.status_code == 200
    reprocessed_entries = reprocess_res.json()["data"]

    # Manual entry still exists
    manual_found = any(e["id"] == manual_exp_id for e in reprocessed_entries)
    assert manual_found is True

    # No duplicate records for Acme
    acme_count = sum(1 for e in reprocessed_entries if "Acme" in (e.get("company") or ""))
    assert acme_count == 1

    # 8. Retrieve Experience Summary (GET /resumes/{resume_id}/experience/summary)
    summary_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/experience/summary")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["employment_count"] >= 3
    assert summary_data["total_experience_months"] > 0
    assert summary_data["full_time_count"] >= 1
    assert summary_data["internship_count"] >= 1
    assert summary_data["freelance_count"] >= 1

    # 9. Retrieve Career Progression (GET /resumes/{resume_id}/experience/progression)
    prog_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/experience/progression")
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["success"] is True
    assert len(prog_data["timeline"]) >= 3
    assert len(prog_data["observations"]) >= 1

    # 10. Delete manual entry (DELETE /resumes/{resume_id}/experience/{experience_id})
    del_res = client.delete(f"{RESUMES_ENDPOINT}/{resume_id}/experience/{manual_exp_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Confirm deletion
    verify_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/experience")
    assert not any(e["id"] == manual_exp_id for e in verify_res.json()["data"])


def test_experience_api_security_and_validation():
    """Test Case 15: Security, validation, and authorization handling."""
    # Invalid UUID format returns 400
    res = client.get(f"{RESUMES_ENDPOINT}/not-a-valid-uuid/experience")
    assert res.status_code == 400

    # Non-existent valid UUID returns 404
    non_existent_uuid = str(uuid.uuid4())
    res = client.get(f"{RESUMES_ENDPOINT}/{non_existent_uuid}/experience")
    assert res.status_code == 404

    # Non-existent experience_id on update returns 404
    random_exp_uuid = str(uuid.uuid4())
    res_patch = client.patch(
        f"{RESUMES_ENDPOINT}/{non_existent_uuid}/experience/{random_exp_uuid}",
        json={"company": "Ghost Corp"},
    )
    assert res_patch.status_code in (404, 400)
