"""
Unit tests for IntegrityValidator.
Phase 2 | Feature 2: File Validation (Task 5)
"""

import pytest
import zipfile
from pathlib import Path
import fitz
import docx

from app.services.validation.integrity_validator import integrity_validator
from app.services.validation.exceptions import (
    CorruptedFileError,
    PasswordProtectedFileError,
    InvalidDocumentStructureError,
)


@pytest.fixture
def valid_pdf_file(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "genuine_sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Jane Doe - Senior Software Engineer")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def encrypted_pdf_file(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "protected_resume.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Confidential Resume")
    # Save with user password
    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY
        | fitz.PDF_PERM_PRINT
        | fitz.PDF_PERM_COPY
        | fitz.PDF_PERM_ANNOTATE
    )
    doc.save(
        str(pdf_path),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw="secret",
        owner_pw="master_secret",
        permissions=perm,
    )
    doc.close()
    return pdf_path


@pytest.fixture
def valid_docx_file(tmp_path: Path) -> Path:
    docx_path = tmp_path / "genuine_sample.docx"
    doc = docx.Document()
    doc.add_heading("John Candidate", 0)
    doc.add_paragraph("Full Stack Python and React Developer")
    doc.save(str(docx_path))
    return docx_path


@pytest.fixture
def ordinary_zip_file(tmp_path: Path) -> Path:
    # A standard ZIP archive renamed as .docx (missing [Content_Types].xml, etc.)
    fake_docx_path = tmp_path / "ordinary_archive_renamed.docx"
    with zipfile.ZipFile(fake_docx_path, "w") as zf:
        zf.writestr("holiday_photo.jpg", b"fake jpeg image data")
        zf.writestr("readme.txt", b"just a normal text file")
    return fake_docx_path


def test_validate_pdf_integrity_valid(valid_pdf_file: Path):
    result = integrity_validator.validate_pdf_integrity(valid_pdf_file)
    assert result["format"] == "PDF"
    assert result["page_count"] >= 1
    assert result["is_encrypted"] is False


def test_validate_pdf_integrity_encrypted(encrypted_pdf_file: Path):
    with pytest.raises(PasswordProtectedFileError) as exc:
        integrity_validator.validate_pdf_integrity(encrypted_pdf_file)
    assert "password-protected" in str(exc.value).lower()


def test_validate_pdf_integrity_corrupted(tmp_path: Path):
    corrupted_pdf = tmp_path / "corrupted.pdf"
    # Starts with %PDF- but followed by random corrupted garbage
    corrupted_pdf.write_bytes(b"%PDF-1.4\ncorrupted garbage truncated header without xref")

    with pytest.raises(CorruptedFileError) as exc:
        integrity_validator.validate_pdf_integrity(corrupted_pdf)
    assert "corrupted" in str(exc.value).lower() or "damaged" in str(exc.value).lower()


def test_validate_docx_integrity_valid(valid_docx_file: Path):
    result = integrity_validator.validate_docx_integrity(valid_docx_file)
    assert result["format"] == "DOCX"
    assert result["is_encrypted"] is False
    assert result["uncompressed_bytes"] > 0


def test_validate_docx_integrity_rejects_ordinary_zip(ordinary_zip_file: Path):
    with pytest.raises(InvalidDocumentStructureError) as exc:
        integrity_validator.validate_docx_integrity(ordinary_zip_file)
    assert "standard ZIP archive" in str(exc.value)
    assert "[Content_Types].xml" in str(exc.value)


def test_validate_docx_integrity_corrupted(tmp_path: Path):
    corrupted_docx = tmp_path / "corrupted.docx"
    corrupted_docx.write_bytes(b"PK\x03\x04truncated invalid zip data")

    with pytest.raises(CorruptedFileError):
        integrity_validator.validate_docx_integrity(corrupted_docx)
