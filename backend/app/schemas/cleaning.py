"""
Resume Text Cleaning Schemas
Phase 2 | Feature 4: Text Cleaning
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class CleaningStatus(str, Enum):
    """Status indicating outcome of the cleaning pipeline."""
    SUCCESS = "SUCCESS"
    EMPTY_INPUT = "EMPTY_INPUT"
    NO_CHANGE = "NO_CHANGE"
    PARTIAL = "PARTIAL"


class CleaningAction(str, Enum):
    """Documented cleaning operations performed on the text."""
    WHITESPACE_NORMALIZED = "whitespace_normalized"
    LINE_BREAKS_NORMALIZED = "line_breaks_normalized"
    CONTROL_CHARACTERS_REMOVED = "control_characters_removed"
    UNICODE_NORMALIZED = "unicode_normalized"
    DUPLICATE_BLOCKS_REMOVED = "duplicate_blocks_removed"
    BULLETS_NORMALIZED = "bullets_normalized"
    HEADING_SPACING_NORMALIZED = "heading_spacing_normalized"


class CleanRequest(BaseModel):
    """Optional request body to supply specific text to clean."""
    raw_text: Optional[str] = None
    extraction_id: Optional[str] = None


class CleaningData(BaseModel):
    """Detailed cleaning result payload."""
    cleaning_id: str
    extraction_id: Optional[str] = None
    resume_id: str
    original_text: str
    cleaned_text: str
    original_character_count: int
    cleaned_character_count: int
    original_word_count: int
    cleaned_word_count: int
    cleaning_status: CleaningStatus
    cleaning_actions: List[str]
    cleaned_at: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cleaning_id": "7b3f940b-044f-4a0b-8d76-e889a7216a30",
                "extraction_id": "8f8b3c9b-6ef9-4081-9be5-4b16258414ad",
                "resume_id": "a5e8e821-6893-4a7b-a25d-4f1082c9e7bc",
                "original_text": "Jane Doe \r\n\r\nSenior Software Engineer\t\t\n\n• C++ and .NET",
                "cleaned_text": "Jane Doe\n\nSenior Software Engineer\n\n• C++ and .NET",
                "original_character_count": 68,
                "cleaned_character_count": 60,
                "original_word_count": 9,
                "cleaned_word_count": 9,
                "cleaning_status": "SUCCESS",
                "cleaning_actions": [
                    "line_breaks_normalized",
                    "whitespace_normalized",
                    "bullets_normalized"
                ],
                "cleaned_at": "2026-11-18T22:35:00Z"
            }
        }
    )


class CleaningResponse(BaseModel):
    """Standardized API response for cleaned resume text."""
    success: bool
    message: str
    data: CleaningData
