"""
File Size & Signature Validation Service
Phase 2 | Feature 2: File Validation (Task 2 & Task 4)
"""

import logging
from typing import Optional
from pathlib import Path

from app.core.config import settings
from app.services.validation.exceptions import (
    EmptyFileError,
    FileTooSmallError,
    FileTooLargeError,
    InvalidFileSignatureError,
)

logger = logging.getLogger(__name__)

# Minimum viable bytes for a minimal valid PDF or empty OpenXML zip
MINIMUM_FILE_SIZE_BYTES = 64

PDF_HEADER_MAGIC = b"%PDF-"
ZIP_LOCAL_HEADER_MAGIC = b"PK\x03\x04"


class SignatureValidator:
    """Validates file size boundaries and binary magic byte signatures."""

    def __init__(self, max_size_bytes: Optional[int] = None):
        self.max_size_bytes = max_size_bytes or settings.RESUME_UPLOAD_MAX_SIZE_BYTES

    def validate_size(self, size_bytes: int) -> int:
        """
        Validate file size against minimum and maximum boundaries.
        Returns validated size_bytes.
        """
        if size_bytes == 0:
            raise EmptyFileError("Uploaded file is empty (0 bytes).")

        if size_bytes < MINIMUM_FILE_SIZE_BYTES:
            raise FileTooSmallError(
                f"File size ({size_bytes} bytes) is too small to be a valid document."
            )

        if size_bytes > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            current_mb = size_bytes / (1024 * 1024)
            raise FileTooLargeError(
                f"File size ({current_mb:.2f} MB) exceeds the maximum allowed limit of {max_mb:.0f} MB.",
                details={"max_bytes": self.max_size_bytes, "actual_bytes": size_bytes},
            )

        return size_bytes

    def validate_signature(self, file_path: Path, extension: str) -> bool:
        """
        Inspect binary signature at file header and tail to ensure genuine structure.
        """
        if not file_path.exists():
            raise InvalidFileSignatureError("File does not exist for signature inspection.")

        file_size = file_path.stat().st_size
        self.validate_size(file_size)

        norm_ext = extension.lower()

        # Read first 1024 bytes for header signature
        with open(file_path, "rb") as f:
            header_chunk = f.read(1024)

            # Also read the tail for PDF end-of-file validation
            f.seek(max(0, file_size - 1024))
            tail_chunk = f.read(1024)

        if norm_ext == ".pdf":
            # PDF must start with %PDF- (or contain it in first 1024 bytes per spec)
            if not header_chunk.startswith(PDF_HEADER_MAGIC) and PDF_HEADER_MAGIC not in header_chunk:
                raise InvalidFileSignatureError(
                    "Invalid PDF file signature. The file does not start with standard PDF header '%PDF-'.",
                    details={"extension": norm_ext},
                )

            # Standard PDFs contain %%EOF near the end
            if b"%%EOF" not in tail_chunk:
                # Warning: Some damaged/truncated PDFs miss %%EOF
                logger.warning("PDF file %s is missing '%%%%EOF' marker in tail chunk", file_path.name)

            return True

        elif norm_ext == ".docx":
            # DOCX must begin with ZIP local header signature PK\x03\x04
            if not header_chunk.startswith(ZIP_LOCAL_HEADER_MAGIC):
                raise InvalidFileSignatureError(
                    "Invalid DOCX file signature. The file does not contain a valid ZIP package signature.",
                    details={"extension": norm_ext},
                )
            return True

        else:
            raise InvalidFileSignatureError(f"Unsupported extension for signature check: {norm_ext}")


signature_validator = SignatureValidator()
