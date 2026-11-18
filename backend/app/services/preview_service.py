"""
Resume Preview Service
Phase 2 | Feature 5: Resume Preview
"""

import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from app.schemas.preview import PreviewStatus, ResumePreviewData
from app.schemas.extraction import ExtractionData, ContentBlock, ExtractionStatus
from app.schemas.cleaning import CleaningData
from app.services.storage import staging_service
from app.services.extraction import extraction_service
from app.services.cleaning import cleaning_service
from app.services.cleaning.formatting_cleaner import KNOWN_HEADINGS

logger = logging.getLogger(__name__)

LIST_ITEM_REGEX = re.compile(r"^(\s*)(?:[•\-\*·▪▫►■]|\d{1,3}\.)\s+(.+)$")


def parse_structured_blocks(text: str) -> List[ContentBlock]:
    """
    Parses cleaned resume text into structured content blocks (heading, list_item, paragraph)
    without modifying the underlying text or using AI classification.
    """
    if not text or not text.strip():
        return []

    blocks: List[ContentBlock] = []
    # Split text into paragraphs separated by double newlines or single newlines
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    for para in paragraphs:
        lines = [line for line in para.split("\n") if line.strip()]
        if not lines:
            continue

        # Check if single line is a section heading
        if len(lines) == 1:
            line_str = lines[0].strip()
            upper_clean = re.sub(r"[^A-Za-z\s&]", "", line_str).strip().upper()

            is_known = upper_clean in KNOWN_HEADINGS
            is_all_caps = (
                line_str.isupper()
                and 3 <= len(line_str) <= 50
                and not line_str.endswith((".", ",", ";"))
            )

            if is_known or is_all_caps:
                blocks.append(ContentBlock(type="heading", content=line_str))
                continue

        # Check for list items or mixed lines within paragraph
        current_paragraph_lines: List[str] = []

        for line in lines:
            match = LIST_ITEM_REGEX.match(line)
            if match:
                # Flush any preceding paragraph lines
                if current_paragraph_lines:
                    blocks.append(
                        ContentBlock(type="paragraph", content=" ".join(current_paragraph_lines))
                    )
                    current_paragraph_lines = []

                blocks.append(ContentBlock(type="list_item", content=line.strip()))
            else:
                # Check if this individual line looks like a heading
                line_clean = re.sub(r"[^A-Za-z\s&]", "", line).strip().upper()
                if line_clean in KNOWN_HEADINGS or (line.isupper() and 3 <= len(line) <= 50):
                    if current_paragraph_lines:
                        blocks.append(
                            ContentBlock(type="paragraph", content=" ".join(current_paragraph_lines))
                        )
                        current_paragraph_lines = []
                    blocks.append(ContentBlock(type="heading", content=line.strip()))
                else:
                    current_paragraph_lines.append(line.strip())

        if current_paragraph_lines:
            blocks.append(
                ContentBlock(type="paragraph", content=" ".join(current_paragraph_lines))
            )

    return blocks


class ResumePreviewService:
    """
    Assembles and caches resume preview data, avoiding redundant extraction or cleaning.
    Provides secure preview compilation and metadata generation.
    """

    def __init__(self):
        # In-memory staging caches keyed by resume_id
        self._extraction_cache: Dict[str, ExtractionData] = {}
        self._cleaning_cache: Dict[str, CleaningData] = {}

    def cache_extraction(self, resume_id: str, data: ExtractionData) -> None:
        """Cache extraction output to avoid re-extracting."""
        self._extraction_cache[resume_id] = data

    def cache_cleaning(self, resume_id: str, data: CleaningData) -> None:
        """Cache cleaning output to avoid re-cleaning."""
        self._cleaning_cache[resume_id] = data

    def get_cached_extraction(self, resume_id: str) -> Optional[ExtractionData]:
        return self._extraction_cache.get(resume_id)

    def get_cached_cleaning(self, resume_id: str) -> Optional[CleaningData]:
        return self._cleaning_cache.get(resume_id)

    def get_preview(self, resume_id: str) -> ResumePreviewData:
        """
        Retrieves or compiles preview data for a staged resume.
        Reuses cached Feature 3 and Feature 4 outputs whenever available.
        """
        staged_path = staging_service.get_staged_path(resume_id)
        if not staged_path or not staged_path.exists():
            raise FileNotFoundError(f"Staged resume not found or expired for ID: {resume_id}")

        filename = staged_path.name
        original_filename = filename.split("_", 1)[1] if "_" in filename else filename
        file_size = staged_path.stat().st_size
        file_type = Path(original_filename).suffix.lstrip(".").lower()

        # 1. Retrieve or run Feature 3 extraction
        extraction_data = self._extraction_cache.get(resume_id)
        if not extraction_data:
            extraction_data = extraction_service.extract_from_file(
                file_path=staged_path,
                original_filename=original_filename,
                resume_id=resume_id,
                file_type=file_type,
            )
            self._extraction_cache[resume_id] = extraction_data

        raw_text = extraction_data.raw_text

        # 2. Retrieve or run Feature 4 cleaning
        cleaning_data = self._cleaning_cache.get(resume_id)
        if not cleaning_data:
            cleaning_data = cleaning_service.clean_text(
                raw_text=raw_text,
                resume_id=resume_id,
                extraction_id=extraction_data.extraction_id,
            )
            self._cleaning_cache[resume_id] = cleaning_data

        cleaned_text = cleaning_data.cleaned_text

        # 3. Determine Preview Status
        if not cleaned_text.strip():
            preview_status = PreviewStatus.EMPTY
        elif extraction_data.extraction_status == ExtractionStatus.FAILED:
            preview_status = PreviewStatus.ERROR
        else:
            preview_status = PreviewStatus.READY

        # 4. Generate structured blocks
        structured_blocks = parse_structured_blocks(cleaned_text)
        if not structured_blocks and extraction_data.blocks:
            structured_blocks = extraction_data.blocks

        return ResumePreviewData(
            resume_id=resume_id,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file_size,
            preview_status=preview_status,
            cleaned_text=cleaned_text,
            raw_text=raw_text,
            blocks=structured_blocks,
            character_count=cleaning_data.cleaned_character_count,
            word_count=cleaning_data.cleaned_word_count,
            page_count=extraction_data.page_count,
            cleaning_actions=cleaning_data.cleaning_actions,
            extraction_method=extraction_data.extraction_method,
            extracted_at=extraction_data.extracted_at,
            cleaned_at=cleaning_data.cleaned_at,
            file_available=True,
            file_download_url=f"/api/v1/resumes/{resume_id}/file?download=true",
            file_view_url=f"/api/v1/resumes/{resume_id}/file",
        )


preview_service = ResumePreviewService()
