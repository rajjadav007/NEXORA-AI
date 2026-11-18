"""
Unit tests for MimeValidator.
Phase 2 | Feature 2: File Validation (Task 1 & Task 3)
"""

import pytest
from app.services.validation.mime_validator import (
    mime_validator,
    detect_mime_from_bytes,
    normalize_extension,
)
from app.services.validation.exceptions import (
    UnsupportedFileTypeError,
    MimeTypeMismatchError,
    InvalidFileSignatureError,
)


def test_normalize_extension_valid():
    assert normalize_extension("resume.pdf") == ".pdf"
    assert normalize_extension("RESUME.PDF") == ".pdf"
    assert normalize_extension("my.cv.v2.docx") == ".docx"
    assert normalize_extension("Candidate.Docx") == ".docx"


def test_normalize_extension_missing():
    with pytest.raises(UnsupportedFileTypeError):
        normalize_extension("")

    with pytest.raises(UnsupportedFileTypeError):
        normalize_extension("filename_without_extension")


def test_validate_extension_rejections():
    # Unsupported extensions
    for ext in ["resume.txt", "resume.png", "resume.jpg", "resume.exe", "resume.odt"]:
        with pytest.raises(UnsupportedFileTypeError) as exc:
            mime_validator.validate_extension(ext)
        assert "Unsupported file format" in str(exc.value)

    # Legacy .doc special message
    with pytest.raises(UnsupportedFileTypeError) as exc:
        mime_validator.validate_extension("legacy_resume.doc")
    assert "Legacy Word (.doc) format is not supported" in str(exc.value)


def test_detect_mime_from_bytes_pdf():
    pdf_header = b"%PDF-1.4\n1 0 obj"
    mime, label = detect_mime_from_bytes(pdf_header)
    assert mime == "application/pdf"
    assert label == "pdf"


def test_detect_mime_from_bytes_docx():
    docx_header = b"PK\x03\x04\x14\x00"
    mime, label = detect_mime_from_bytes(docx_header)
    assert "openxmlformats" in mime
    assert label == "docx_or_zip"


def test_detect_mime_from_bytes_disguised_executable():
    exe_header = b"MZ\x90\x00\x03\x00\x00\x00"
    mime, label = detect_mime_from_bytes(exe_header)
    assert mime == "application/x-dosexec"
    assert label == "executable"

    # Reject executable renamed as .pdf
    with pytest.raises(InvalidFileSignatureError) as exc:
        mime_validator.validate_content_mime(exe_header, ".pdf")
    assert "Executable file detected" in str(exc.value)


def test_detect_mime_from_bytes_disguised_image():
    png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    mime, label = detect_mime_from_bytes(png_header)
    assert mime == "image/png"
    assert label == "png"

    # Reject PNG renamed as .pdf
    with pytest.raises(MimeTypeMismatchError) as exc:
        mime_validator.validate_content_mime(png_header, ".pdf")
    assert "Image file detected" in str(exc.value)


def test_mime_extension_mismatch():
    # PDF header but .docx extension
    pdf_header = b"%PDF-1.7 mock"
    with pytest.raises(MimeTypeMismatchError) as exc:
        mime_validator.validate_content_mime(pdf_header, ".docx")
    assert "does not match Word document" in str(exc.value)

    # Random binary but .pdf extension
    garbage_header = b"\x01\x02\x03\x04\x05"
    with pytest.raises(MimeTypeMismatchError) as exc:
        mime_validator.validate_content_mime(garbage_header, ".pdf")
    assert "does not match PDF format" in str(exc.value)
