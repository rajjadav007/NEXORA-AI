"""
Unit tests for SignatureValidator.
Phase 2 | Feature 2: File Validation (Task 2 & Task 4)
"""

import pytest
from pathlib import Path

from app.services.validation.signature_validator import SignatureValidator
from app.services.validation.exceptions import (
    EmptyFileError,
    FileTooSmallError,
    FileTooLargeError,
    InvalidFileSignatureError,
)


@pytest.fixture
def validator():
    # 1 MB max size for test boundaries
    return SignatureValidator(max_size_bytes=1024 * 1024)


def test_validate_size_empty(validator: SignatureValidator):
    with pytest.raises(EmptyFileError):
        validator.validate_size(0)


def test_validate_size_too_small(validator: SignatureValidator):
    with pytest.raises(FileTooSmallError):
        validator.validate_size(20)  # Min is 64 bytes


def test_validate_size_valid(validator: SignatureValidator):
    assert validator.validate_size(1024) == 1024
    assert validator.validate_size(1024 * 1024) == 1024 * 1024


def test_validate_size_too_large(validator: SignatureValidator):
    with pytest.raises(FileTooLargeError):
        validator.validate_size(1024 * 1024 + 1)


def test_validate_pdf_signature_valid(tmp_path: Path, validator: SignatureValidator):
    pdf_path = tmp_path / "valid.pdf"
    pdf_path.write_bytes(
        b"%PDF-1.4\n"
        b"% Sample valid PDF header comment with extra padding to exceed minimum byte boundary\n"
        b"1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    )

    assert validator.validate_signature(pdf_path, ".pdf") is True


def test_validate_pdf_signature_invalid(tmp_path: Path, validator: SignatureValidator):
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"This is a text file renamed to pdf with enough bytes to pass size check" * 2)

    with pytest.raises(InvalidFileSignatureError) as exc:
        validator.validate_signature(fake_pdf, ".pdf")
    assert "Invalid PDF file signature" in str(exc.value)


def test_validate_docx_signature_valid(tmp_path: Path, validator: SignatureValidator):
    docx_path = tmp_path / "valid.docx"
    docx_path.write_bytes(b"PK\x03\x04" + b"0" * 100)

    assert validator.validate_signature(docx_path, ".docx") is True


def test_validate_docx_signature_invalid(tmp_path: Path, validator: SignatureValidator):
    fake_docx = tmp_path / "fake.docx"
    fake_docx.write_bytes(b"%PDF-1.4 but renamed to docx with plenty of content padding" * 2)

    with pytest.raises(InvalidFileSignatureError) as exc:
        validator.validate_signature(fake_docx, ".docx")
    assert "Invalid DOCX file signature" in str(exc.value)
