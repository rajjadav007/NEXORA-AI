"""
Resume Text Extraction Schemas
Phase 2 | Feature 3: Resume Text Extraction
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class ExtractionStatus(str, Enum):
    """Possible extraction outcome statuses."""
    SUCCESS = "SUCCESS"
    EMPTY_DOCUMENT = "EMPTY_DOCUMENT"
    NO_SELECTABLE_TEXT = "NO_SELECTABLE_TEXT"
    PARTIAL_EXTRACTION = "PARTIAL_EXTRACTION"
    FAILED = "FAILED"


class PageExtraction(BaseModel):
    """Page-level extraction details for multi-page documents (e.g. PDF)."""
    page_number: int
    text: str
    character_count: int
    word_count: int


class ContentBlock(BaseModel):
    """Document structural component (e.g. heading, paragraph, list item, table)."""
    type: str  # "heading" | "paragraph" | "list_item" | "table"
    content: str


class ExtractionData(BaseModel):
    """Consolidated extraction payload."""
    extraction_id: str
    resume_id: str
    original_filename: str
    file_type: str
    page_count: Optional[int] = None
    character_count: int
    word_count: int
    extraction_status: ExtractionStatus
    extraction_method: str  # "pymupdf" | "python-docx"
    extracted_at: str
    raw_text: str
    pages: List[PageExtraction] = []
    blocks: List[ContentBlock] = []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "extraction_id": "8f8b3c9b-6ef9-4081-9be5-4b16258414ad",
                "resume_id": "a5e8e821-6893-4a7b-a25d-4f1082c9e7bc",
                "original_filename": "candidate_resume.pdf",
                "file_type": "pdf",
                "page_count": 2,
                "character_count": 3412,
                "word_count": 580,
                "extraction_status": "SUCCESS",
                "extraction_method": "pymupdf",
                "extracted_at": "2026-11-18T22:30:00Z",
                "raw_text": "Jane Doe\nSenior Software Engineer...",
                "pages": [
                    {
                        "page_number": 1,
                        "text": "Jane Doe\nSenior Software Engineer...",
                        "character_count": 1800,
                        "word_count": 310,
                    }
                ],
                "blocks": [
                    {
                        "type": "heading",
                        "content": "PROFESSIONAL EXPERIENCE",
                    }
                ],
            }
        }
    )


class ExtractionResponse(BaseModel):
    """Standardized API response for resume extraction."""
    success: bool
    message: str
    data: ExtractionData
