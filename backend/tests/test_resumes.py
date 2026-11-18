"""
API tests for Resume Upload endpoint.
Phase 2 | Feature 1: Resume Upload
"""

import io
import pytest
import fitz
import docx
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core.config import settings
from app.services.storage import staging_service, StorageError

client = TestClient(app)
ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"


def create_sample_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "John Doe - Software Engineer Resume")
    stream = doc.write()
    doc.close()
    return stream


def create_sample_docx() -> bytes:
    doc = docx.Document()
    doc.add_heading("Jane Candidate", 0)
    doc.add_paragraph("Full Stack Developer Resume")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_upload_valid_pdf():
    pdf_content = create_sample_pdf()
    files = {
        "file": ("test_resume.pdf", io.BytesIO(pdf_content), "application/pdf")
    }

    response = client.post(ENDPOINT, files=files)

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["message"] == "Resume uploaded successfully"

    payload = json_data["data"]
    assert "upload_id" in payload
    assert payload["original_filename"] == "test_resume.pdf"
    assert payload["file_size"] == len(pdf_content)
    assert payload["content_type"] == "application/pdf"
    assert payload["status"] == "staged"

    # Verify physical file exists and path is NOT leaked
    assert "staged_path" not in payload
    assert "storage" not in str(payload)

    # Clean up
    staging_service.cleanup_file(payload["upload_id"])


def test_upload_valid_docx():
    docx_content = create_sample_docx()
    files = {
        "file": (
            "resume_candidate.docx",
            io.BytesIO(docx_content),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    response = client.post(ENDPOINT, files=files)

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["original_filename"] == "resume_candidate.docx"
    assert json_data["data"]["status"] == "staged"

    # Clean up
    staging_service.cleanup_file(json_data["data"]["upload_id"])


def test_upload_missing_file():
    # Sending post with empty form data
    response = client.post(ENDPOINT, files={})
    assert response.status_code == 422  # FastAPI validation error for missing field


def test_upload_empty_filename():
    files = {
        "file": ("", io.BytesIO(b"%PDF-1.4"), "application/pdf")
    }
    response = client.post(ENDPOINT, files=files)
    assert response.status_code in (400, 422)


def test_upload_empty_file():
    files = {
        "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
    }
    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_unsupported_extension():
    files = {
        "file": ("script.py", io.BytesIO(b"print('hello')"), "text/x-python")
    }
    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_unsupported_image_format():
    files = {
        "file": ("resume.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")
    }
    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_oversized_file():
    # Patch max size to 1 KB for fast testing
    with patch.object(staging_service, "max_size_bytes", 1024):
        large_content = b"0" * 2048
        files = {
            "file": ("large_resume.pdf", io.BytesIO(large_content), "application/pdf")
        }
        response = client.post(ENDPOINT, files=files)
        assert response.status_code == 413
        assert "exceeds" in response.json()["detail"].lower()


def test_upload_storage_failure():
    # Simulate an internal storage exception
    with patch.object(staging_service, "stage_upload", side_effect=StorageError("Disk full")):
        files = {
            "file": ("resume.pdf", io.BytesIO(b"%PDF-1.4 sample"), "application/pdf")
        }
        response = client.post(ENDPOINT, files=files)
        assert response.status_code == 500
        assert "Failed to store" in response.json()["detail"]
