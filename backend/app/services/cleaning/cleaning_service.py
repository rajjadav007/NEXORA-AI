"""
Text Cleaning Orchestration Service
Phase 2 | Feature 4: Text Cleaning (Task 6)
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List

from app.schemas.cleaning import (
    CleaningStatus,
    CleaningAction,
    CleaningData,
)
from app.services.cleaning.whitespace_cleaner import whitespace_cleaner
from app.services.cleaning.character_cleaner import character_cleaner
from app.services.cleaning.formatting_cleaner import formatting_cleaner

logger = logging.getLogger(__name__)


class TextCleaningService:
    """
    Orchestrates the 6-stage text cleaning pipeline:
      1. Line break normalization
      2. Non-printable control character removal
      3. Unicode artifacts & ligature normalization
      4. Whitespace & tab collapsing
      5. Consecutive accidental duplicate block removal
      6. Bullet points & heading spacing normalization
    """

    def __init__(self):
        self.whitespace_cleaner = whitespace_cleaner
        self.character_cleaner = character_cleaner
        self.formatting_cleaner = formatting_cleaner

    def clean_text(
        self,
        raw_text: str,
        resume_id: str,
        extraction_id: Optional[str] = None,
    ) -> CleaningData:
        """
        Clean and normalize raw extracted resume text deterministically.
        Tracks before-and-after metrics and applied operations.
        """
        orig_text = raw_text or ""
        orig_char_count = len(orig_text)
        orig_word_count = len(orig_text.split())

        cleaning_id = str(uuid.uuid4())
        cleaned_at = datetime.now(timezone.utc).isoformat()
        actions: List[str] = []

        if not orig_text.strip():
            return CleaningData(
                cleaning_id=cleaning_id,
                extraction_id=extraction_id,
                resume_id=resume_id,
                original_text=orig_text,
                cleaned_text="",
                original_character_count=orig_char_count,
                cleaned_character_count=0,
                original_word_count=orig_word_count,
                cleaned_word_count=0,
                cleaning_status=CleaningStatus.EMPTY_INPUT,
                cleaning_actions=[],
                cleaned_at=cleaned_at,
            )

        current = orig_text

        # 1. Line breaks (\r\n, \r -> \n)
        current, changed_lb = self.whitespace_cleaner.normalize_line_breaks(current)
        if changed_lb:
            actions.append(CleaningAction.LINE_BREAKS_NORMALIZED.value)

        # 2. Control characters removal
        current, changed_cc = self.character_cleaner.clean_control_characters(current)
        if changed_cc:
            actions.append(CleaningAction.CONTROL_CHARACTERS_REMOVED.value)

        # 3. Unicode smart quotes, ligatures, dashes
        current, changed_uni = self.character_cleaner.normalize_unicode_and_artifacts(current)
        if changed_uni:
            actions.append(CleaningAction.UNICODE_NORMALIZED.value)

        # 4. Whitespace, tabs, and excess blank lines
        current, changed_ws = self.whitespace_cleaner.normalize_whitespace(current)
        if changed_ws:
            actions.append(CleaningAction.WHITESPACE_NORMALIZED.value)

        # 5. Consecutive duplicate blocks
        current, changed_dup = self.formatting_cleaner.remove_consecutive_duplicates(current)
        if changed_dup:
            actions.append(CleaningAction.DUPLICATE_BLOCKS_REMOVED.value)

        # 6. Bullets and numbered lists
        current, changed_bl = self.formatting_cleaner.normalize_bullets_and_lists(current)
        if changed_bl:
            actions.append(CleaningAction.BULLETS_NORMALIZED.value)

        # 7. Heading spacing
        current, changed_hd = self.formatting_cleaner.normalize_heading_spacing(current)
        if changed_hd:
            actions.append(CleaningAction.HEADING_SPACING_NORMALIZED.value)

        # Final trimming pass
        cleaned_text = current.strip()

        cleaned_char_count = len(cleaned_text)
        cleaned_word_count = len(cleaned_text.split())

        status = CleaningStatus.SUCCESS if actions else CleaningStatus.NO_CHANGE

        logger.info(
            "Cleaned text for resume_id=%s: chars %d -> %d, words %d -> %d, actions=%s",
            resume_id,
            orig_char_count,
            cleaned_char_count,
            orig_word_count,
            cleaned_word_count,
            actions,
        )

        return CleaningData(
            cleaning_id=cleaning_id,
            extraction_id=extraction_id,
            resume_id=resume_id,
            original_text=orig_text,
            cleaned_text=cleaned_text,
            original_character_count=orig_char_count,
            cleaned_character_count=cleaned_char_count,
            original_word_count=orig_word_count,
            cleaned_word_count=cleaned_word_count,
            cleaning_status=status,
            cleaning_actions=actions,
            cleaned_at=cleaned_at,
        )


cleaning_service = TextCleaningService()
