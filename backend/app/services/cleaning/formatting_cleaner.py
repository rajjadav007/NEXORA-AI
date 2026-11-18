"""
Duplicate and Formatting Cleaner
Phase 2 | Feature 4: Text Cleaning (Task 4 & Task 5)
"""

import re
from typing import Tuple, List

# Common bullet characters used across Word, PDF, and text processors
BULLET_REGEX = re.compile(r"^(\s*)[•\*\-\+▪▫►■o·]\s+", re.MULTILINE)

# Numbered list format variations like "1) ", "(1) " at line starts
NUMBERED_LIST_PAREN = re.compile(r"^(\s*)\(?(\d{1,3})\)[\s]+", re.MULTILINE)

# Standard resume section headings to ensure proper paragraph spacing
KNOWN_HEADINGS = {
    "SUMMARY",
    "PROFESSIONAL SUMMARY",
    "EXECUTIVE SUMMARY",
    "EXPERIENCE",
    "WORK EXPERIENCE",
    "PROFESSIONAL EXPERIENCE",
    "EMPLOYMENT HISTORY",
    "EDUCATION",
    "ACADEMIC BACKGROUND",
    "SKILLS",
    "TECHNICAL SKILLS",
    "CORE COMPETENCIES",
    "PROJECTS",
    "KEY PROJECTS",
    "CERTIFICATIONS",
    "LICENSES & CERTIFICATIONS",
    "PUBLICATIONS",
    "AWARDS",
    "HONORS & AWARDS",
    "LANGUAGES",
    "VOLUNTEER EXPERIENCE",
}


class FormattingCleaner:
    """
    Normalizes bullet points, numbered lists, heading separation,
    and removes accidental consecutive duplicate blocks conservatively.
    """

    def normalize_bullets_and_lists(self, text: str) -> Tuple[str, bool]:
        """
        Normalize bullet characters at line beginnings to standard '• '.
        Normalizes parenthesized numbers like '1) ' to standard '1. '.
        Preserves leading indentation for nested lists.
        """
        if not text:
            return "", False

        original = text

        # 1. Standardize bullets preserving indentation
        result = BULLET_REGEX.sub(r"\1• ", text)

        # 2. Standardize numbered list markers like "1) " or "(1) " -> "1. "
        result = NUMBERED_LIST_PAREN.sub(r"\1\2. ", result)

        changed = result != original
        return result, changed

    def normalize_heading_spacing(self, text: str) -> Tuple[str, bool]:
        """
        Ensure clear blank line preceding major section headings
        to prevent them from fusing into previous paragraphs.
        """
        if not text:
            return "", False

        lines = text.split("\n")
        new_lines: List[str] = []
        changed = False

        for i, line in enumerate(lines):
            stripped = line.strip().rstrip(":")
            # If line matches a known heading (case-insensitive or all-caps)
            if stripped.upper() in KNOWN_HEADINGS and len(stripped) <= 35:
                # If not the first line and previous line is not already blank
                if i > 0 and new_lines and new_lines[-1] != "":
                    new_lines.append("")
                    changed = True
            new_lines.append(line)

        result = "\n".join(new_lines)
        return result, changed

    def remove_consecutive_duplicates(self, text: str) -> Tuple[str, bool]:
        """
        Conservatively remove accidental consecutive identical lines or paragraphs
        (such as repeated page headers or footers across page breaks).
        Never deletes non-consecutive repetitions (e.g. repeated skills or job titles).
        """
        if not text:
            return "", False

        lines = text.split("\n")
        deduped: List[str] = []
        last_non_empty = ""
        changed = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                deduped.append(line)
                continue

            if stripped == last_non_empty and len(stripped) > 5:
                changed = True
                continue

            last_non_empty = stripped
            deduped.append(line)

        result = "\n".join(deduped)
        return result, changed


formatting_cleaner = FormattingCleaner()
