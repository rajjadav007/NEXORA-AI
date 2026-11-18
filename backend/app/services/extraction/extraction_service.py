"""
Extraction Orchestration and Metadata Service
Phase 2 | Feature 3: Resume Text Extraction (Task 3, 5, 6)
"""

import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.schemas.extraction import (
    ExtractionStatus,
    ExtractionData,
    PageExtraction,
    ContentBlock,
)
from app.services.extraction.pdf_extractor import pdf_extractor
from app.services.extraction.docx_extractor import docx_extractor

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Coordinates extraction routing, calculates document statistics,
    and formats standardized ExtractionData.
    """

    def __init__(self):
        self.pdf_extractor = pdf_extractor
        self.docx_extractor = docx_extractor

    def extract_from_file(
        self,
        file_path: Path,
        original_filename: str,
        resume_id: str,
        file_type: Optional[str] = None,
    ) -> ExtractionData:
        """
        Execute format-specific extraction on a staged file and return structured ExtractionData.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Staged resume file not found: {file_path}")

        # Resolve file type from explicit argument or filename extension
        resolved_type = (file_type or Path(original_filename).suffix.lstrip(".").lower()).lower()

        extraction_id = str(uuid.uuid4())
        extracted_at = datetime.now(timezone.utc).isoformat()

        if resolved_type == "pdf":
            pdf_result = self.pdf_extractor.extract(file_path)
            raw_text = pdf_result.raw_text
            char_count = len(raw_text)
            word_count = len(raw_text.split())

            return ExtractionData(
                extraction_id=extraction_id,
                resume_id=resume_id,
                original_filename=original_filename,
                file_type="pdf",
                page_count=pdf_result.page_count,
                character_count=char_count,
                word_count=word_count,
                extraction_status=pdf_result.status,
                extraction_method="pymupdf",
                extracted_at=extracted_at,
                raw_text=raw_text,
                pages=pdf_result.pages,
                blocks=pdf_result.blocks,
            )

        elif resolved_type == "docx":
            docx_result = self.docx_extractor.extract(file_path)
            raw_text = docx_result.raw_text
            char_count = len(raw_text)
            word_count = len(raw_text.split())

            return ExtractionData(
                extraction_id=extraction_id,
                resume_id=resume_id,
                original_filename=original_filename,
                file_type="docx",
                page_count=None,  # DOCX has flow layout without fixed pagination
                character_count=char_count,
                word_count=word_count,
                extraction_status=docx_result.status,
                extraction_method="python-docx",
                extracted_at=extracted_at,
                raw_text=raw_text,
                pages=[],
                blocks=docx_result.blocks,
            )

        else:
            raise ValueError(f"Unsupported file type for text extraction: '{resolved_type}'")


extraction_service = ExtractionService()
