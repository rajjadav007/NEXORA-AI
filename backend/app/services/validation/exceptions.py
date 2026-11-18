"""
Validation Error Codes and Exceptions
Phase 2 | Feature 2: File Validation
"""

from typing import Optional


class ValidationErrorCode:
    """Standardized validation error codes."""
    EMPTY_FILE = "EMPTY_FILE"
    FILE_TOO_SMALL = "FILE_TOO_SMALL"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    MIME_TYPE_MISMATCH = "MIME_TYPE_MISMATCH"
    INVALID_FILE_SIGNATURE = "INVALID_FILE_SIGNATURE"
    INVALID_DOCUMENT_STRUCTURE = "INVALID_DOCUMENT_STRUCTURE"
    CORRUPTED_FILE = "CORRUPTED_FILE"
    PASSWORD_PROTECTED_FILE = "PASSWORD_PROTECTED_FILE"
    FILE_VALIDATION_FAILED = "FILE_VALIDATION_FAILED"


class FileValidationError(Exception):
    """Base exception for all file validation failures."""

    def __init__(
        self,
        code: str,
        message: str,
        category: str = "validation",
        status_code: int = 400,
        details: Optional[dict] = None,
    ):
        self.code = code
        self.message = message
        self.category = category
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class UnsupportedFileTypeError(FileValidationError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ValidationErrorCode.UNSUPPORTED_FILE_TYPE,
            message=message,
            category="file_type",
            status_code=400,
            details=details,
        )


class EmptyFileError(FileValidationError):
    def __init__(self, message: str = "Uploaded file is empty (0 bytes)."):
        super().__init__(
            code=ValidationErrorCode.EMPTY_FILE,
            message=message,
            category="size",
            status_code=400,
        )


class FileTooSmallError(FileValidationError):
    def __init__(self, message: str = "File is too small to be a valid document."):
        super().__init__(
            code=ValidationErrorCode.FILE_TOO_SMALL,
            message=message,
            category="size",
            status_code=400,
        )


class FileTooLargeError(FileValidationError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ValidationErrorCode.FILE_TOO_LARGE,
            message=message,
            category="size",
            status_code=413,
            details=details,
        )


class MimeTypeMismatchError(FileValidationError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ValidationErrorCode.MIME_TYPE_MISMATCH,
            message=message,
            category="mime_type",
            status_code=400,
            details=details,
        )


class InvalidFileSignatureError(FileValidationError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ValidationErrorCode.INVALID_FILE_SIGNATURE,
            message=message,
            category="signature",
            status_code=400,
            details=details,
        )


class InvalidDocumentStructureError(FileValidationError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ValidationErrorCode.INVALID_DOCUMENT_STRUCTURE,
            message=message,
            category="structure",
            status_code=400,
            details=details,
        )


class CorruptedFileError(FileValidationError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ValidationErrorCode.CORRUPTED_FILE,
            message=message,
            category="integrity",
            status_code=400,
            details=details,
        )


class PasswordProtectedFileError(FileValidationError):
    def __init__(
        self,
        message: str = "The uploaded PDF is password-protected. Please remove the password and re-upload.",
    ):
        super().__init__(
            code=ValidationErrorCode.PASSWORD_PROTECTED_FILE,
            message=message,
            category="integrity",
            status_code=400,
        )
