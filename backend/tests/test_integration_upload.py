"""
End-to-End Integration Tests for Resume Upload.
Phase 2 | Feature 1: Resume Upload

Verifies real multi-part uploads, temporary file creation in the staging directory,
safe internal naming, path traversal safety, and error rejections.
"""

import io
import pytest
from pathlib import Path
import fitz
import docx
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.storage import staging_service

client = TestClient(app)
ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"


def create_valid_test_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "John Doe - Integration Resume PDF")
    stream = doc.write()
    doc.close()
    return stream


def create_valid_test_docx() -> bytes:
    doc = docx.Document()
    doc.add_heading("Jane Smith", 0)
    doc.add_paragraph("Product Manager Resume")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_integration_full_pdf_upload_flow():
    """Validates complete PDF upload, metadata integrity, and temporary staging."""
    pdf_bytes = create_valid_test_pdf()

    files = {
        "file": ("John_Doe_Software_Engineer_Resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    }

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Resume uploaded successfully"

    payload = data["data"]
    upload_id = payload["upload_id"]
    assert payload["original_filename"] == "John_Doe_Software_Engineer_Resume.pdf"
    assert payload["file_size"] == len(pdf_bytes)
    assert payload["content_type"] == "application/pdf"
    assert payload["status"] == "staged"

    # Verify physical file existence in staging directory
    staged_file = staging_service.get_staged_path(upload_id)
    assert staged_file is not None
    assert staged_file.exists()
    assert staged_file.is_file()
    assert staged_file.read_bytes() == pdf_bytes

    # Ensure internal filename incorporates upload_id and sanitized base
    assert upload_id in staged_file.name
    assert "John_Doe_Software_Engineer_Resume.pdf" in staged_file.name

    # Physical path must NOT be leaked anywhere in API response
    assert str(staged_file) not in response.text
    assert "backend" not in response.text

    # Cleanup
    assert staging_service.cleanup_file(upload_id) is True
    assert not staged_file.exists()


def test_integration_full_docx_upload_flow():
    """Validates complete DOCX upload and temporary staging."""
    docx_bytes = create_valid_test_docx()

    files = {
        "file": (
            "Jane_Smith_Product_Manager.docx",
            io.BytesIO(docx_bytes),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    payload = data["data"]
    upload_id = payload["upload_id"]

    assert payload["original_filename"] == "Jane_Smith_Product_Manager.docx"
    assert payload["file_size"] == len(docx_bytes)

    # Check physical file on disk
    staged_file = staging_service.get_staged_path(upload_id)
    assert staged_file is not None
    assert staged_file.exists()
    assert staged_file.read_bytes() == docx_bytes

    # Cleanup
    staging_service.cleanup_file(upload_id)
    assert not staged_file.exists()


def test_integration_path_traversal_attack_blocked():
    """Attempts directory traversal in filename to write outside staging directory."""
    pdf_payload = create_valid_test_pdf()
    docx_payload = create_valid_test_docx()

    test_cases = [
        ("../../../../etc/passwd.pdf", pdf_payload, "application/pdf"),
        ("..\\..\\..\\windows\\system32\\calc.docx", docx_payload, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("/absolute/root/path/resume.pdf", pdf_payload, "application/pdf"),
        ("nested/sub/dir/resume.docx", docx_payload, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ]

    for fname, payload, ct in test_cases:
        files = {
            "file": (fname, io.BytesIO(payload), ct)
        }
        response = client.post(ENDPOINT, files=files)
        assert response.status_code == 200, f"Failed for {fname}: {response.text}"

        upload_id = response.json()["data"]["upload_id"]
        staged_file = staging_service.get_staged_path(upload_id)
        assert staged_file is not None

        # File MUST be safely confined inside the staging directory
        assert staged_file.parent.resolve() == staging_service.staging_dir.resolve()
        assert ".." not in staged_file.name
        assert "/" not in staged_file.name
        assert "\\" not in staged_file.name

        # Clean up
        staging_service.cleanup_file(upload_id)


def test_integration_empty_file_cleanup():
    """Empty files must be rejected with 400 and immediately unlinked."""
    before_count = len(list(staging_service.staging_dir.glob("*")))

    files = {
        "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
    }
    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400

    after_count = len(list(staging_service.staging_dir.glob("*")))
    assert before_count == after_count, "Incomplete/empty file was not cleaned up!"
