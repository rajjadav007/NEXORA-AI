"""
Resume API Schemas
Phase 2 | Feature 2: File Validation
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ResumeUploadData(BaseModel):
    """Metadata payload returned on successful resume staging and validation."""
    upload_id: str
    original_filename: str
    file_size: int
    content_type: str
    status: str
    file_type: Optional[str] = None
    is_valid: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "upload_id": "a5e8e821-6893-4a7b-a25d-4f1082c9e7bc",
                "original_filename": "candidate_resume.pdf",
                "file_size": 245760,
                "content_type": "application/pdf",
                "status": "staged",
                "file_type": "pdf",
                "is_valid": True,
            }
        }
    )


class ResumeUploadResponse(BaseModel):
    """Standardized API response for successful resume upload & validation."""
    success: bool = True
    message: str = "Resume uploaded successfully"
    data: ResumeUploadData


class ValidationErrorDetail(BaseModel):
    """Standardized validation error payload."""
    code: str
    message: str
    category: str = "validation"
    details: Optional[Dict[str, Any]] = None


class ResumeUploadErrorResponse(BaseModel):
    """Structured error response returned on upload/validation failures."""
    success: bool = False
    error: ValidationErrorDetail
    detail: str  # Backwards compatibility with standard FastAPI error clients
