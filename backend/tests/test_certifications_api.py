"""
Integration Tests for Certifications & Achievements API Endpoints
Phase 3 | Feature 19: Certifications & Achievements Intelligence
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


def create_certifications_resume_pdf_bytes() -> bytes:
    """Generates a test PDF resume containing certifications, hackathons, and achievements."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Alex Rivera")
    page.insert_text((50, 70), "New York, NY | alex.rivera@example.com | linkedin.com/in/alexrivera")

    page.insert_text((50, 100), "PROJECTS")
    page.insert_text((50, 115), "AgriConnect | Python, React (Jan 2023 - Present)")
    page.insert_text((50, 130), "- Developed smart agriculture IoT platform.")

    page.insert_text((50, 155), "CERTIFICATIONS")
    page.insert_text((50, 175), "AWS Certified Solutions Architect - Associate | Amazon Web Services")
    page.insert_text((50, 190), "Credential ID: AWS-84920491 | Issued: Oct 2023 | Expires: Oct 2026")
    page.insert_text((50, 205), "https://www.credly.com/badges/aws-architect-assoc")

    page.insert_text((50, 225), "Google Cloud Professional Data Engineer (Currently Pursuing)")
    page.insert_text((50, 240), "Expected: Dec 2024")

    page.insert_text((50, 265), "HONORS & AWARDS")
    page.insert_text((50, 285), "1st Place Winner - HackMIT 2023 for AgriConnect project, team of 4")
    page.insert_text((50, 300), "- Won grand prize of $5,000 for building IoT pest detector.")

    page.insert_text((50, 320), "Top 10 Finalist - Google Hash Code 2022")
    page.insert_text((50, 335), "Participant - Major League Hacking HackFest 2021")

    page.insert_text((50, 360), "PUBLICATIONS")
    page.insert_text((50, 380), "Neural Network Compression for Edge Devices - Published in IEEE Access, 2023")
    page.insert_text((50, 395), "DOI: 10.1109/ACCESS.2023.1234567")

    stream = doc.write()
    doc.close()
    return stream


def test_certifications_and_achievements_api_full_lifecycle():
    # 1. Upload resume
    pdf_bytes = create_certifications_resume_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("CertsResume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    staging_id = upload_res.json()["data"]["upload_id"]

    # 2. Save resume permanently to DB
    save_res = client.post(
        f"{RESUMES_ENDPOINT}/{staging_id}/save",
        json={"user_email": "candidate.certs@nexora.ai"},
    )
    assert save_res.status_code == 201
    resume_id = save_res.json()["data"]["id"]

    # Also trigger projects extraction to link AgriConnect project
    client.post(f"{RESUMES_ENDPOINT}/{resume_id}/projects/extract")

    # 3. Extract Certifications
    extract_cert_url = f"{RESUMES_ENDPOINT}/{resume_id}/certifications/extract"
    cert_res = client.post(extract_cert_url)
    assert cert_res.status_code == 200
    cert_json = cert_res.json()
    assert cert_json["success"] is True
    assert cert_json["total"] >= 2
    certs = cert_json["data"]

    aws_cert = next((c for c in certs if "AWS" in c["certification_name"]), None)
    assert aws_cert is not None
    assert aws_cert["issuing_organization"] == "Amazon Web Services (AWS)"
    assert aws_cert["credential_id"] == "AWS-84920491"
    assert aws_cert["completion_status"] == "completed"
    assert aws_cert["certification_category"] == "cloud"

    gcp_cert = next((c for c in certs if "Google Cloud" in c["certification_name"]), None)
    assert gcp_cert is not None
    assert gcp_cert["completion_status"] == "in_progress"

    # 4. Extract Achievements
    extract_achieve_url = f"{RESUMES_ENDPOINT}/{resume_id}/achievements/extract"
    achieve_res = client.post(extract_achieve_url)
    assert achieve_res.status_code == 200
    achieve_json = achieve_res.json()
    assert achieve_json["success"] is True
    assert achieve_json["total"] >= 2
    achieves = achieve_json["data"]

    # HackMIT (1st Place Winner)
    hackmit = next((a for a in achieves if "HackMIT" in a["achievement_title"] or (a.get("event_name") and "HackMIT" in a["event_name"])), None)
    assert hackmit is not None
    assert hackmit["achievement_type"] == "award"
    assert hackmit["rank_or_position"] == "1st Place"
    # Project AgriConnect should be linked
    if hackmit.get("related_project_id"):
        assert hackmit["related_project_title"] == "AgriConnect"

    # Publication
    pub = next((a for a in achieves if "Neural Network Compression" in a["achievement_title"]), None)
    assert pub is not None
    assert pub["achievement_type"] == "publication"
    assert "10.1109/ACCESS" in pub.get("achievement_url", "")

    # Participant (Must NOT be converted to winner)
    part = next((a for a in achieves if "HackFest" in a["achievement_title"] or (a.get("event_name") and "HackFest" in a["event_name"])), None)
    if part:
        assert part["achievement_type"] == "participation"
        assert part["rank_or_position"] == "Participant"

    # 5. Summaries
    cert_summary_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/certifications/summary")
    assert cert_summary_res.status_code == 200
    assert cert_summary_res.json()["total_certifications"] >= 2

    achieve_summary_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/achievements/summary")
    assert achieve_summary_res.status_code == 200
    assert achieve_summary_res.json()["total_achievements"] >= 2

    combined_summary_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/certifications-achievements/summary")
    assert combined_summary_res.status_code == 200
    comb = combined_summary_res.json()
    assert comb["total_combined_records"] >= 4

    # 6. Manual Add & Edit Certification
    add_cert_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/certifications",
        json={
            "certification_name": "Certified Scrum Master (CSM)",
            "issuing_organization": "Scrum Alliance",
            "certification_category": "project_management",
            "completion_status": "completed",
        },
    )
    assert add_cert_res.status_code == 201
    created_cert_id = add_cert_res.json()["data"]["id"]

    patch_cert_res = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/certifications/{created_cert_id}",
        json={"credential_id": "CSM-999888"},
    )
    assert patch_cert_res.status_code == 200
    assert patch_cert_res.json()["data"]["credential_id"] == "CSM-999888"

    # Confirm certification
    confirm_cert_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/certifications/{created_cert_id}/confirm"
    )
    assert confirm_cert_res.status_code == 200
    assert confirm_cert_res.json()["data"]["review_status"] == "confirmed"

    # Delete certification
    del_cert_res = client.delete(f"{RESUMES_ENDPOINT}/{resume_id}/certifications/{created_cert_id}")
    assert del_cert_res.status_code == 200

    # 7. Manual Add & Edit Achievement
    add_achieve_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/achievements",
        json={
            "achievement_title": "Dean's List of Academic Excellence",
            "achievement_category": "academic",
            "achievement_type": "award",
            "rank_or_position": "Top 5%",
        },
    )
    assert add_achieve_res.status_code == 201
    created_achieve_id = add_achieve_res.json()["data"]["id"]

    confirm_achieve_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/achievements/{created_achieve_id}/confirm"
    )
    assert confirm_achieve_res.status_code == 200
    assert confirm_achieve_res.json()["data"]["review_status"] == "confirmed"

    del_achieve_res = client.delete(f"{RESUMES_ENDPOINT}/{resume_id}/achievements/{created_achieve_id}")
    assert del_achieve_res.status_code == 200


def test_invalid_resume_id_security():
    bad_res = client.get(f"{RESUMES_ENDPOINT}/not-a-valid-uuid/certifications")
    assert bad_res.status_code == 400

    path_traversal_res = client.get(f"{RESUMES_ENDPOINT}/invalid..id/certifications")
    assert path_traversal_res.status_code == 400

    random_id = str(uuid.uuid4())
    not_found_res = client.get(f"{RESUMES_ENDPOINT}/{random_id}/certifications")
    assert not_found_res.status_code == 404
