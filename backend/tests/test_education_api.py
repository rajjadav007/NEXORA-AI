"""
Integration Tests for Education Analysis API
Phase 3 | Feature 14: Education Analysis
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


def create_education_resume_pdf_bytes() -> bytes:
    """Generates a test PDF resume with rich education sections."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Raj Jadav")
    page.insert_text((50, 70), "Bengaluru, Karnataka, India | raj.jadav@example.com")
    page.insert_text((50, 100), "EDUCATION")
    page.insert_text((50, 120), "Bachelor of Computer Applications (BCA)")
    page.insert_text((50, 140), "Bangalore University, Bengaluru")
    page.insert_text((50, 160), "2020 - 2023 | CGPA: 8.42 / 10.0")
    page.insert_text((50, 180), "Coursework: Data Structures, Algorithms, DBMS")
    page.insert_text((50, 210), "Higher Secondary School (12th)")
    page.insert_text((50, 230), "National Public School, Bengaluru")
    page.insert_text((50, 250), "2018 - 2020 | Percentage: 88.5%")
    page.insert_text((50, 280), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 300), "Software engineer with 2+ years experience.")
    stream = doc.write()
    doc.close()
    return stream


def test_education_api_full_lifecycle():
    # 1. Upload resume
    pdf_bytes = create_education_resume_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("EducationResume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    staging_id = upload_res.json()["data"]["upload_id"]

    # 2. Save resume permanently to DB
    save_res = client.post(
        f"{RESUMES_ENDPOINT}/{staging_id}/save",
        json={"user_email": "candidate.edu@nexora.ai"},
    )
    assert save_res.status_code == 201
    resume_id = save_res.json()["data"]["id"]

    # 3. Extract education (POST /resumes/{resume_id}/education/extract)
    extract_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/education/extract")
    assert extract_res.status_code == 200
    extract_body = extract_res.json()
    assert extract_body["success"] is True
    entries = extract_body["data"]
    assert len(entries) >= 2

    # Verify structured fields
    bca_entry = next((e for e in entries if "Computer Applications" in (e.get("normalized_degree") or "")), None)
    assert bca_entry is not None
    assert bca_entry["degree_level"] == "undergraduate"
    assert "Bangalore University" in (bca_entry["institution"] or "")
    assert bca_entry["grade"] is not None
    assert bca_entry["grade"]["type"].lower() == "cgpa"
    assert bca_entry["grade"]["value"] == 8.42
    assert bca_entry["grade"]["scale"] == 10.0
    assert bca_entry["graduation_status"] == "completed"
    assert bca_entry["is_manually_edited"] is False

    # 4. Retrieve education entries (GET /resumes/{resume_id}/education)
    get_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/education")
    assert get_res.status_code == 200
    get_body = get_res.json()
    assert get_body["success"] is True
    assert (get_body.get("total") or get_body.get("total_count")) >= 2
    retrieved_entries = get_body["data"]
    first_entry_id = retrieved_entries[0]["id"]

    # 5. Add a manual education entry (POST /resumes/{resume_id}/education)
    manual_payload = {
        "degree": "Master of Computer Applications",
        "institution": "Indian Institute of Science",
        "location": "Bengaluru, India",
        "start_date": "2023",
        "end_date": "2025",
        "graduation_status": "ongoing",
        "grade": {"type": "cgpa", "value": 9.2, "scale": 10.0},
        "achievements": ["Dean's Merit List"],
        "coursework": ["Distributed Systems", "Cloud Computing"],
        "honors": ["Gold Medalist"],
    }
    create_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/education",
        json=manual_payload,
    )
    assert create_res.status_code == 201
    created_entry = create_res.json()["data"]
    created_id = created_entry["id"]
    assert created_entry["normalized_degree"] == "Master of Computer Applications"
    assert created_entry["degree_level"] == "postgraduate"
    assert created_entry["is_manually_edited"] is True

    # 6. Update manual entry (PATCH /resumes/{resume_id}/education/{education_id})
    patch_res = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/education/{created_id}",
        json={"location": "Bengaluru, Karnataka, India", "specialization": "Artificial Intelligence"},
    )
    assert patch_res.status_code == 200
    updated_entry = patch_res.json()["data"]
    assert updated_entry["location"] == "Bengaluru, Karnataka, India"
    assert updated_entry["specialization"] == "Artificial Intelligence"
    assert updated_entry["is_manually_edited"] is True
    assert "location" in updated_entry["manually_edited_fields"]

    # 7. Reprocess education (POST /resumes/{resume_id}/education/reprocess)
    # Default reprocess must PRESERVE manual entries
    reprocess_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/education/reprocess",
        json={"force_overwrite": False},
    )
    assert reprocess_res.status_code == 200
    reprocessed_entries = reprocess_res.json()["data"]
    reprocessed_ids = [e["id"] for e in reprocessed_entries]
    assert created_id in reprocessed_ids

    # 8. Reprocess with force_overwrite = True
    # Overwrites manual entries
    overwrite_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/education/reprocess",
        json={"force_overwrite": True},
    )
    assert overwrite_res.status_code == 200
    overwritten_entries = overwrite_res.json()["data"]
    overwritten_ids = [e["id"] for e in overwritten_entries]
    assert created_id not in overwritten_ids

    # 9. Delete an entry (DELETE /resumes/{resume_id}/education/{education_id})
    delete_target_id = overwritten_entries[0]["id"]
    delete_res = client.delete(f"{RESUMES_ENDPOINT}/{resume_id}/education/{delete_target_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    # Verify deletion
    verify_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/education")
    remaining_ids = [e["id"] for e in verify_res.json()["data"]]
    assert delete_target_id not in remaining_ids


def test_education_api_errors():
    # 1. Non-existent resume
    non_existent_id = str(uuid.uuid4())
    res = client.get(f"{RESUMES_ENDPOINT}/{non_existent_id}/education")
    assert res.status_code == 404

    # 2. Invalid resume UUID format
    res_bad = client.get(f"{RESUMES_ENDPOINT}/not-a-uuid/education")
    assert res_bad.status_code in (400, 404, 422)

    # 3. Non-existent education_id on update
    valid_resume_uuid = str(uuid.uuid4())
    random_edu_uuid = str(uuid.uuid4())
    res_patch = client.patch(
        f"{RESUMES_ENDPOINT}/{valid_resume_uuid}/education/{random_edu_uuid}",
        json={"degree": "Test Degree"},
    )
    assert res_patch.status_code in (404, 400)
