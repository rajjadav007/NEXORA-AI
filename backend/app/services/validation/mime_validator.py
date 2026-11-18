"""
File Type & MIME Validation Service
Phase 2 | Feature 2: File Validation (Task 1 & Task 3)
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from app.services.validation.exceptions import (
    UnsupportedFileTypeError,
    MimeTypeMismatchError,
    InvalidFileSignatureError,
)

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

EXPECTED_MIME_BY_EXT = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def normalize_extension(filename: Optional[str]) -> str:
    """Extract and normalize the file extension in lowercase."""
    if not filename or not filename.strip():
        raise UnsupportedFileTypeError("Filename is missing or empty.")

    clean_name = filename.strip()
    ext = Path(clean_name).suffix.lower()

    if not ext:
        raise UnsupportedFileTypeError(
            "File has no extension. Please upload a .pdf or .docx document."
        )

    return ext


def detect_mime_from_bytes(header_bytes: bytes) -> Tuple[str, str]:
    """
    Detect the MIME type and a human-readable format label from leading header bytes.
    Does not rely on client headers or file extension.
    """
    if not header_bytes:
        return "application/octet-stream", "empty"

    # PDF: begins with %PDF- (standard offset 0, tolerant up to first 1024 bytes)
    if header_bytes.startswith(b"%PDF-") or b"%PDF-" in header_bytes[:1024]:
        return "application/pdf", "pdf"

    # Office Open XML / ZIP signature: begins with PK\x03\x04
    if header_bytes.startswith(b"PK\x03\x04"):
        # Could be docx or standard zip; detailed package inspection is in integrity validator
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx_or_zip"

    # Legacy MS Office Compound Document (OLE2) .doc / .xls / .ppt
    if header_bytes.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "application/msword", "legacy_doc"

    # Executables (Windows PE / DOS)
    if header_bytes.startswith(b"MZ"):
        return "application/x-dosexec", "executable"

    # Images
    if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if header_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpeg"
    if header_bytes.startswith(b"GIF87a") or header_bytes.startswith(b"GIF89a"):
        return "image/gif", "gif"

    # Shell script or text
    if header_bytes.startswith(b"#!") or header_bytes.startswith(b"<?xml") or header_bytes.startswith(b"<html"):
        return "text/plain", "text"

    return "application/octet-stream", "unknown"


class MimeValidator:
    """Validates extension and content-based MIME types."""

    def validate_extension(self, filename: str) -> str:
        """Validate filename extension against allowlist."""
        ext = normalize_extension(filename)

        if ext == ".doc":
            raise UnsupportedFileTypeError(
                "Legacy Word (.doc) format is not supported. Please convert and upload as .docx or .pdf.",
                details={"extension": ext, "suggested": [".docx", ".pdf"]},
            )

        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file format '{ext}'. Only PDF (.pdf) and Word (.docx) documents are allowed.",
                details={"extension": ext, "supported": list(SUPPORTED_EXTENSIONS)},
            )

        return ext

    def validate_content_mime(
        self,
        header_bytes: bytes,
        extension: str,
        client_content_type: Optional[str] = None,
    ) -> str:
        """
        Verify that file bytes match the expected MIME type for the extension.
        Rejects renamed executables, images, text, and mismatched formats.
        """
        detected_mime, format_label = detect_mime_from_bytes(header_bytes)
        expected_mime = EXPECTED_MIME_BY_EXT.get(extension.lower())

        if not expected_mime:
            raise UnsupportedFileTypeError(f"Unsupported extension: {extension}")

        # Check for specific disguised malicious/unsupported formats
        if format_label == "executable":
            raise InvalidFileSignatureError(
                "Executable file detected. Executables cannot be uploaded as resumes.",
                details={"detected_mime": detected_mime, "extension": extension},
            )

        if format_label == "legacy_doc":
            raise UnsupportedFileTypeError(
                "Legacy binary .doc file detected. Please convert to modern .docx or .pdf.",
                details={"detected_mime": detected_mime},
            )

        if format_label in {"png", "jpeg", "gif"}:
            raise MimeTypeMismatchError(
                f"Image file detected ({format_label.upper()}). Image files cannot be uploaded as {extension.upper()} resumes.",
                details={"detected_mime": detected_mime, "extension": extension},
            )

        # Mismatch check: PDF extension but not PDF bytes
        if extension.lower() == ".pdf" and detected_mime != "application/pdf":
            raise MimeTypeMismatchError(
                f"File content does not match PDF format. Detected type: {detected_mime}.",
                details={"expected": "application/pdf", "detected": detected_mime},
            )

        # Mismatch check: DOCX extension but not ZIP/OpenXML bytes
        if extension.lower() == ".docx" and not header_bytes.startswith(b"PK\x03\x04"):
            raise MimeTypeMismatchError(
                f"File content does not match Word document (.docx) format. Detected type: {detected_mime}.",
                details={"expected": expected_mime, "detected": detected_mime},
            )

        return expected_mime


mime_validator = MimeValidator()
