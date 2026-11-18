"""
Tests for Resume Storage
Phase 2 | Feature 6: Resume Storage
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
from app.services.permanent_storage import permanent_storage
from app.models.resume import Resume, ResumeVersion
from app.models.user import User

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_test_pdf_bytes(title: str = "Test Candidate") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), title)
    page.insert_text((50, 80), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 110), "Experienced engineer with full stack background.")
    stream = doc.write()
    doc.close()
    return stream


def test_save_staged_resume_to_database():
    pdf_bytes = create_test_pdf_bytes("Storage Test Candidate")
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("StorageCandidate.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    staging_id = upload_res.json()["data"]["upload_id"]

    try:
        # Save resume to permanent DB
        save_res = client.post(
            f"{RESUMES_ENDPOINT}/{staging_id}/save",
            json={"user_email": "candidate@nexora.ai"},
        )
        assert save_res.status_code == 201
        body = save_res.json()
        assert body["success"] is True
        data = body["data"]

        assert data["original_filename"] == "StorageCandidate.pdf"
        assert data["file_type"] == "pdf"
        assert data["processing_status"] == "COMPLETED"
        assert data["current_version"] == 1
        assert len(data["versions"]) == 1

        version = data["versions"][0]
        assert version["version_number"] == 1
        assert "Storage Test Candidate" in version["cleaned_text"]

        # Verify permanent file exists on disk
        stored_file_path = permanent_storage.get_storage_path(data["storage_key"])
        assert stored_file_path is not None
        assert stored_file_path.exists()

        # Verify secure file download endpoint serves permanent file
        file_res = client.get(f"{RESUMES_ENDPOINT}/{data['id']}/file")
        assert file_res.status_code == 200
        assert file_res.headers["content-type"] == "application/pdf"
        assert "StorageCandidate.pdf" in file_res.headers["content-disposition"]
    finally:
        staging_service.cleanup_file(staging_id)
        if "data" in locals() and "id" in data:
            client.delete(f"{RESUMES_ENDPOINT}/{data['id']}")


def test_list_stored_resumes():
    pdf_bytes = create_test_pdf_bytes("List Candidate")
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("ListCandidate.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    staging_id = upload_res.json()["data"]["upload_id"]

    try:
        save_res = client.post(
            f"{RESUMES_ENDPOINT}/{staging_id}/save",
            json={"user_email": "list_user@nexora.ai"},
        )
        assert save_res.status_code == 201
        resume_id = save_res.json()["data"]["id"]

        list_res = client.get(RESUMES_ENDPOINT)
        assert list_res.status_code == 200
        body = list_res.json()
        assert body["success"] is True
        assert body["total"] >= 1
        assert any(r["id"] == resume_id for r in body["data"])
    finally:
        staging_service.cleanup_file(staging_id)
        if "resume_id" in locals():
            client.delete(f"{RESUMES_ENDPOINT}/{resume_id}")


def test_get_stored_resume_by_id():
    pdf_bytes = create_test_pdf_bytes("Detail Candidate")
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("DetailCandidate.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    staging_id = upload_res.json()["data"]["upload_id"]

    try:
        save_res = client.post(
            f"{RESUMES_ENDPOINT}/{staging_id}/save",
            json={"user_email": "detail_user@nexora.ai"},
        )
        resume_id = save_res.json()["data"]["id"]

        detail_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}")
        assert detail_res.status_code == 200
        data = detail_res.json()["data"]
        assert data["id"] == resume_id
        assert data["original_filename"] == "DetailCandidate.pdf"
        assert len(data["versions"]) == 1
    finally:
        staging_service.cleanup_file(staging_id)
        if "resume_id" in locals():
            client.delete(f"{RESUMES_ENDPOINT}/{resume_id}")


def test_delete_stored_resume_cleans_db_and_disk():
    pdf_bytes = create_test_pdf_bytes("Delete Candidate")
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("DeleteCandidate.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    staging_id = upload_res.json()["data"]["upload_id"]

    try:
        save_res = client.post(
            f"{RESUMES_ENDPOINT}/{staging_id}/save",
            json={"user_email": "delete_user@nexora.ai"},
        )
        data = save_res.json()["data"]
        resume_id = data["id"]
        storage_key = data["storage_key"]

        # Confirm file exists before delete
        stored_path = permanent_storage.get_storage_path(storage_key)
        assert stored_path is not None and stored_path.exists()

        # Execute DELETE
        del_res = client.delete(f"{RESUMES_ENDPOINT}/{resume_id}")
        assert del_res.status_code == 200

        # Confirm 404 from DB
        get_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}")
        assert get_res.status_code == 404

        # Confirm file removed from disk
        assert not stored_path.exists()
    finally:
        staging_service.cleanup_file(staging_id)


def test_save_staged_resume_not_found():
    res = client.post(f"{RESUMES_ENDPOINT}/{uuid.uuid4()}/save")
    assert res.status_code == 404
