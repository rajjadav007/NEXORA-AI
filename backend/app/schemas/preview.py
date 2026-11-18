"""
Resume Preview Schemas
Phase 2 | Feature 5: Resume Preview
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.extraction import ContentBlock


class PreviewStatus(str, Enum):
    """Resume preview lifecycle and display statuses."""
    READY = "READY"
    PROCESSING = "PROCESSING"
    EMPTY = "EMPTY"
    ERROR = "ERROR"


class ResumePreviewData(BaseModel):
    """Structured resume preview payload."""
    resume_id: str
    original_filename: str
    file_type: str  # "pdf" | "docx"
    file_size: int
    preview_status: PreviewStatus
    cleaned_text: str
    raw_text: Optional[str] = None
    blocks: List[ContentBlock] = []
    character_count: int
    word_count: int
    page_count: Optional[int] = None
    cleaning_actions: List[str] = []
    extraction_method: Optional[str] = None
    extracted_at: Optional[str] = None
    cleaned_at: Optional[str] = None
    file_available: bool = True
    file_download_url: str
    file_view_url: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resume_id": "a5e8e821-6893-4a7b-a25d-4f1082c9e7bc",
                "original_filename": "candidate_resume.pdf",
                "file_type": "pdf",
                "file_size": 245760,
                "preview_status": "READY",
                "cleaned_text": "Jane Doe\n\nPROFESSIONAL SUMMARY\n\nSenior Software Engineer...",
                "raw_text": "Jane Doe\r\n\r\nPROFESSIONAL SUMMARY\r\n\r\nSenior Software Engineer...",
                "blocks": [
                    {"type": "heading", "content": "PROFESSIONAL SUMMARY"},
                    {"type": "paragraph", "content": "Senior Software Engineer with 8+ years experience..."}
                ],
                "character_count": 3200,
                "word_count": 520,
                "page_count": 2,
                "cleaning_actions": ["whitespace_normalized", "bullets_normalized"],
                "extraction_method": "pymupdf",
                "extracted_at": "2026-11-18T22:30:00Z",
                "cleaned_at": "2026-11-18T22:35:00Z",
                "file_available": True,
                "file_download_url": "/api/v1/resumes/a5e8e821-6893-4a7b-a25d-4f1082c9e7bc/file?download=true",
                "file_view_url": "/api/v1/resumes/a5e8e821-6893-4a7b-a25d-4f1082c9e7bc/file",
            }
        }
    )


class ResumePreviewResponse(BaseModel):
    """Standardized API response for resume preview."""
    success: bool = True
    message: str = "Resume preview loaded successfully"
    data: ResumePreviewData
