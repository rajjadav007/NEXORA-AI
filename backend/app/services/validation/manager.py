"""
File Validation Manager (Pipeline Orchestrator)
Phase 2 | Feature 2: File Validation
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.services.validation.mime_validator import mime_validator
from app.services.validation.signature_validator import signature_validator
from app.services.validation.integrity_validator import integrity_validator
from app.services.validation.exceptions import (
    FileValidationError,
    CorruptedFileError,
)

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Normalized validation output."""
    is_valid: bool = True
    file_type: str
    detected_mime: str
    file_size: int
    is_encrypted: bool = False
    details: Dict[str, Any] = {}


class FileValidationManager:
    """
    Orchestrates the 6-stage validation pipeline:
      1. File existence & size check
      2. Extension normalization & allowlist
      3. Content-based MIME detection
      4. Magic byte signature verification
      5. Document integrity & structure check
      6. Security / encryption / ZIP bomb validation
    """

    def __init__(self):
        self.mime_validator = mime_validator
        self.signature_validator = signature_validator
        self.integrity_validator = integrity_validator

    def validate_file(
        self,
        file_path: Path,
        original_filename: str,
        client_content_type: Optional[str] = None,
    ) -> ValidationResult:
        """
        Execute full validation pipeline against a staged file.
        Raises FileValidationError subclass if validation fails.
        """
        if not file_path.exists():
            raise CorruptedFileError("File does not exist on disk for validation.")

        file_size = file_path.stat().st_size

        # 1. Size bounds check (empty, minimum, maximum limit)
        self.signature_validator.validate_size(file_size)

        # 2. Extension validation & normalization
        ext = self.mime_validator.validate_extension(original_filename)

        # 3. Read header bytes for content-based MIME and magic byte checks
        with open(file_path, "rb") as f:
            header_bytes = f.read(1024)

        # 4. Content-based MIME detection and mismatch checking
        detected_mime = self.mime_validator.validate_content_mime(
            header_bytes=header_bytes,
            extension=ext,
            client_content_type=client_content_type,
        )

        # 5. Magic byte signature validation
        self.signature_validator.validate_signature(file_path=file_path, extension=ext)

        # 6. Deep document integrity & encryption inspection
        details: Dict[str, Any] = {}
        if ext == ".pdf":
            details = self.integrity_validator.validate_pdf_integrity(file_path)
            file_type = "pdf"
        elif ext == ".docx":
            details = self.integrity_validator.validate_docx_integrity(file_path)
            file_type = "docx"
        else:
            raise FileValidationError("UNSUPPORTED_FILE_TYPE", f"Unsupported extension: {ext}")

        logger.info(
            "File validation passed for %s: type=%s, size=%d bytes",
            original_filename,
            file_type,
            file_size,
        )

        return ValidationResult(
            is_valid=True,
            file_type=file_type,
            detected_mime=detected_mime,
            file_size=file_size,
            is_encrypted=False,
            details=details,
        )


validation_manager = FileValidationManager()
