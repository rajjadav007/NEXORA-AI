"""
Resume Upload Staging Service
Phase 2 | Feature 1: Resume Upload

Provides safe temporary file staging for uploaded resumes.
Enforces size limits, validates extensions, prevents path traversal,
and ensures automatic cleanup on failed uploads.
"""

import os
import re
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.services.validation.exceptions import (
    FileValidationError,
    ValidationErrorCode,
)

logger = logging.getLogger(__name__)

# Allowed extensions and accepted content types
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_CONTENT_TYPES = {
    # PDF
    "application/pdf",
    # DOCX standard and common browser variations
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",
}


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class InvalidFileTypeError(StorageError, FileValidationError):
    """Raised when the uploaded file type is unsupported."""
    def __init__(self, message: str = "Unsupported file type", details: Optional[dict] = None):
        StorageError.__init__(self, message)
        FileValidationError.__init__(
            self,
            code=ValidationErrorCode.UNSUPPORTED_FILE_TYPE,
            message=message,
            category="file_type",
            status_code=400,
            details=details,
        )


class FileTooLargeError(StorageError, FileValidationError):
    """Raised when the uploaded file exceeds maximum size limit."""
    def __init__(self, message: str = "File size exceeds the maximum limit.", details: Optional[dict] = None):
        StorageError.__init__(self, message)
        FileValidationError.__init__(
            self,
            code=ValidationErrorCode.FILE_TOO_LARGE,
            message=message,
            category="size",
            status_code=413,
            details=details,
        )


class EmptyFileError(StorageError, FileValidationError):
    """Raised when the uploaded file is empty (0 bytes)."""
    def __init__(self, message: str = "Uploaded file is empty (0 bytes)."):
        StorageError.__init__(self, message)
        FileValidationError.__init__(
            self,
            code=ValidationErrorCode.EMPTY_FILE,
            message=message,
            category="size",
            status_code=400,
        )


class StagedUploadMetadata(BaseModel):
    """Metadata describing a safely staged resume file."""
    upload_id: str
    original_filename: str
    file_size: int
    content_type: str
    status: str = "staged"


def sanitize_filename(filename: Optional[str]) -> str:
    """
    Sanitize an uploaded filename to prevent path traversal and shell injection.
    Strips directory paths, control characters, and unsafe symbols.
    """
    if not filename:
        return "unnamed_resume"

    # Strip any directory path components (both POSIX and Windows)
    basename = Path(filename).name
    basename = basename.split("/")[-1].split("\\")[-1]

    # Normalize name: keep alphanumeric, dot, underscore, dash
    clean_name = re.sub(r"[^\w\.\-]", "_", basename)
    # Remove leading dots or multiple dots that could be traversal attempts
    clean_name = re.sub(r"^\.+", "", clean_name)
    clean_name = re.sub(r"\.{2,}", ".", clean_name)

    if not clean_name:
        return "resume"

    # Truncate length if excessively long
    if len(clean_name) > 150:
        stem = Path(clean_name).stem[:140]
        suffix = Path(clean_name).suffix
        clean_name = f"{stem}{suffix}"

    return clean_name


class ResumeStagingService:
    """
    Temporary staging service for resume uploads.
    Lifecycle:
      1. Receive file stream.
      2. Verify extension & mime type.
      3. Assign UUID upload_id and safe internal filename.
      4. Stream to private staging directory in bounded chunks.
      5. Enforce max size limit and non-empty check.
      6. Return StagedUploadMetadata (never leaking physical path).
      7. On failure, immediately unlink incomplete file.
    """

    def __init__(
        self,
        staging_dir: Optional[Path | str] = None,
        max_size_bytes: Optional[int] = None,
    ):
        base_dir = staging_dir or settings.RESUME_UPLOAD_STAGING_DIR
        self.staging_dir = Path(base_dir).resolve()
        self.max_size_bytes = max_size_bytes or settings.RESUME_UPLOAD_MAX_SIZE_BYTES
        self._ensure_staging_dir()

    def _ensure_staging_dir(self) -> None:
        """Create private staging directory if it doesn't exist."""
        try:
            self.staging_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Failed to create staging directory %s: %s", self.staging_dir, e)
            raise StorageError(f"Staging directory initialization failed: {e}") from e

    def validate_file_metadata(
        self, original_filename: Optional[str], content_type: Optional[str]
    ) -> Tuple[str, str]:
        """
        Validate extension and content type before streaming.
        Returns normalized (extension, content_type).
        """
        if not original_filename:
            raise InvalidFileTypeError("Missing filename")

        safe_name = sanitize_filename(original_filename)
        ext = Path(safe_name).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileTypeError(
                f"Unsupported file format '{ext}'. Only PDF (.pdf) and Word (.docx) documents are allowed."
            )

        # Normalize content type
        normalized_ct = (content_type or "").lower().split(";")[0].strip()
        if not normalized_ct:
            normalized_ct = (
                "application/pdf" if ext == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        if normalized_ct not in ALLOWED_CONTENT_TYPES:
            # If MIME is generic binary/octet-stream, allow if extension is valid
            if normalized_ct not in {"application/octet-stream", "binary/octet-stream"}:
                logger.warning("Unusual content type %s for extension %s", normalized_ct, ext)

        return ext, normalized_ct

    async def stage_upload(self, file: UploadFile) -> StagedUploadMetadata:
        """
        Stream an uploaded file to the staging directory safely.
        """
        if not file:
            raise StorageError("No upload file provided")

        raw_filename = file.filename or ""
        ext, normalized_ct = self.validate_file_metadata(raw_filename, file.content_type)

        upload_id = str(uuid.uuid4())
        safe_base = sanitize_filename(raw_filename)
        # Internal safe filename incorporating UUID
        safe_stored_name = f"{upload_id}_{safe_base}"
        target_path = (self.staging_dir / safe_stored_name).resolve()

        # Path traversal guard
        if not str(target_path).startswith(str(self.staging_dir)):
            logger.error("Path traversal attempt detected: %s -> %s", raw_filename, target_path)
            raise StorageError("Invalid storage target path")

        total_bytes = 0
        chunk_size = 64 * 1024  # 64 KB

        try:
            with open(target_path, "wb") as out_file:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    total_bytes += len(chunk)

                    if total_bytes > self.max_size_bytes:
                        out_file.close()
                        self._safe_unlink(target_path)
                        max_mb = self.max_size_bytes / (1024 * 1024)
                        logger.warning(
                            "Upload exceeded limit: %d bytes > %d bytes", total_bytes, self.max_size_bytes
                        )
                        raise FileTooLargeError(
                            f"File size exceeds the maximum limit of {max_mb:.0f} MB."
                        )

                    out_file.write(chunk)

            if total_bytes == 0:
                self._safe_unlink(target_path)
                logger.warning("Empty file uploaded: %s", raw_filename)
                raise EmptyFileError("Uploaded file is empty (0 bytes).")

            logger.info(
                "Staged resume upload successfully: upload_id=%s, size=%d bytes",
                upload_id,
                total_bytes,
            )

            return StagedUploadMetadata(
                upload_id=upload_id,
                original_filename=raw_filename,
                file_size=total_bytes,
                content_type=normalized_ct,
                status="staged",
            )

        except (FileTooLargeError, EmptyFileError, InvalidFileTypeError):
            raise
        except Exception as e:
            self._safe_unlink(target_path)
            logger.error("Unexpected error writing staged upload file: %s", e)
            raise StorageError(f"Failed to stage upload file: {e}") from e

    def get_staged_path(self, upload_id: str) -> Optional[Path]:
        """
        Internal lookup for staged file path by upload_id.
        Never exposed to the public API.
        """
        if not upload_id or ".." in upload_id or "/" in upload_id or "\\" in upload_id:
            return None

        # Search matching file in staging directory starting with upload_id
        for path in self.staging_dir.glob(f"{upload_id}_*"):
            if path.is_file():
                return path
        return None

    def cleanup_file(self, upload_id: str) -> bool:
        """
        Delete a staged upload file by upload_id.
        """
        path = self.get_staged_path(upload_id)
        if path and path.is_file():
            return self._safe_unlink(path)
        return False

    def _safe_unlink(self, path: Path) -> bool:
        """Helper to safely unlink a file without throwing if already removed."""
        try:
            if path.exists():
                path.unlink()
                return True
        except OSError as e:
            logger.error("Failed to delete staged file %s: %s", path, e)
        return False


# Global default instance
staging_service = ResumeStagingService()
