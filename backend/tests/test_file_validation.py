"""
Comprehensive Integration & Negative Tests for Resume File Validation.
Phase 2 | Feature 2: File Validation (All Tasks 1-6)
"""

import io
import pytest
import zipfile
import fitz
import docx
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.storage import staging_service
from app.services.validation.exceptions import ValidationErrorCode

client = TestClient(app)
ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"


def create_genuine_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "John Doe - Resume Content")
    stream = doc.write()
    doc.close()
    return stream


def create_encrypted_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Confidential Resume")
    stream = doc.write(
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw="secret_pass",
        owner_pw="master_pass",
    )
    doc.close()
    return stream


def create_genuine_docx_bytes() -> bytes:
    doc = docx.Document()
    doc.add_heading("Jane Doe", 0)
    doc.add_paragraph("Lead Software Engineer")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def create_ordinary_zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("notes.txt", b"plain text")
        zf.writestr("image.jpg", b"\xff\xd8\xffdummy jpeg")
    return buf.getvalue()


def test_validation_genuine_pdf():
    pdf_bytes = create_genuine_pdf_bytes()
    files = {"file": ("genuine_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["is_valid"] is True
    assert data["data"]["file_type"] == "pdf"
    assert data["data"]["content_type"] == "application/pdf"

    # Cleanup
    staging_service.cleanup_file(data["data"]["upload_id"])


def test_validation_genuine_docx():
    docx_bytes = create_genuine_docx_bytes()
    files = {
        "file": (
            "genuine_resume.docx",
            io.BytesIO(docx_bytes),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["is_valid"] is True
    assert data["data"]["file_type"] == "docx"

    # Cleanup
    staging_service.cleanup_file(data["data"]["upload_id"])


def test_validation_rejects_password_protected_pdf():
    enc_pdf = create_encrypted_pdf_bytes()
    files = {"file": ("locked_resume.pdf", io.BytesIO(enc_pdf), "application/pdf")}

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ValidationErrorCode.PASSWORD_PROTECTED_FILE
    assert "password-protected" in data["error"]["message"].lower()


def test_validation_rejects_corrupted_pdf():
    # Starts with %PDF- and is > 64 bytes, but is abruptly truncated and lacks xref table
    corrupted_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"corrupted_truncated_unexpected_eof_content_without_xref_or_trailer" * 4
    )
    files = {"file": ("corrupted.pdf", io.BytesIO(corrupted_pdf), "application/pdf")}

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ValidationErrorCode.CORRUPTED_FILE


def test_validation_rejects_ordinary_zip_renamed_docx():
    zip_bytes = create_ordinary_zip_bytes()
    files = {
        "file": (
            "fake_archive.docx",
            io.BytesIO(zip_bytes),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ValidationErrorCode.INVALID_DOCUMENT_STRUCTURE
    assert "standard ZIP archive" in data["error"]["message"]


def test_validation_rejects_disguised_executable():
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"0" * 100
    files = {"file": ("malware_resume.pdf", io.BytesIO(exe_bytes), "application/pdf")}

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ValidationErrorCode.INVALID_FILE_SIGNATURE
    assert "Executable" in data["error"]["message"]


def test_validation_rejects_disguised_png():
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"0" * 100
    files = {"file": ("photo_resume.pdf", io.BytesIO(png_bytes), "application/pdf")}

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ValidationErrorCode.MIME_TYPE_MISMATCH


def test_validation_rejects_legacy_doc():
    ole_bytes = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"0" * 100
    files = {"file": ("old_resume.doc", io.BytesIO(ole_bytes), "application/msword")}

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ValidationErrorCode.UNSUPPORTED_FILE_TYPE
    assert ".doc" in data["error"]["message"]


def test_validation_rejects_file_too_small():
    tiny_bytes = b"%PDF-"  # Only 5 bytes
    files = {"file": ("tiny.pdf", io.BytesIO(tiny_bytes), "application/pdf")}

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ValidationErrorCode.FILE_TOO_SMALL


def test_validation_cleanup_on_failure(tmp_path: Path):
    """Verify that any file failing validation is immediately unlinked from staging."""
    before_files = set(staging_service.staging_dir.glob("*"))

    corrupted_pdf = b"%PDF-1.4\ncorrupted without xref"
    files = {"file": ("cleanup_test.pdf", io.BytesIO(corrupted_pdf), "application/pdf")}

    response = client.post(ENDPOINT, files=files)
    assert response.status_code == 400

    after_files = set(staging_service.staging_dir.glob("*"))
    assert before_files == after_files, "Staging directory left behind failed validation file!"
