"""
Validation Package Exports
Phase 2 | Feature 2: File Validation
"""

from app.services.validation.exceptions import (
    ValidationErrorCode,
    FileValidationError,
    UnsupportedFileTypeError,
    EmptyFileError,
    FileTooSmallError,
    FileTooLargeError,
    MimeTypeMismatchError,
    InvalidFileSignatureError,
    InvalidDocumentStructureError,
    CorruptedFileError,
    PasswordProtectedFileError,
)
from app.services.validation.manager import (
    FileValidationManager,
    ValidationResult,
    validation_manager,
)

__all__ = [
    "ValidationErrorCode",
    "FileValidationError",
    "UnsupportedFileTypeError",
    "EmptyFileError",
    "FileTooSmallError",
    "FileTooLargeError",
    "MimeTypeMismatchError",
    "InvalidFileSignatureError",
    "InvalidDocumentStructureError",
    "CorruptedFileError",
    "PasswordProtectedFileError",
    "FileValidationManager",
    "ValidationResult",
    "validation_manager",
]
