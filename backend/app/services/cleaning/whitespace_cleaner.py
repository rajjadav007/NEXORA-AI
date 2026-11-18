"""
Whitespace and Line Break Cleaner
Phase 2 | Feature 4: Text Cleaning (Task 1 & Task 2)
"""

import re
from typing import Tuple

# Pattern matching 3 or more consecutive newlines
CONSECUTIVE_BLANK_LINES = re.compile(r"\n{3,}")
# Pattern matching repeated horizontal spaces/tabs
REPEATED_SPACES = re.compile(r"[ \t]{2,}")
# Non-breaking and alternative Unicode spaces
UNICODE_SPACES = re.compile(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]")
# Zero-width spaces and formatting marks
ZERO_WIDTH_CHARS = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")


class WhitespaceCleaner:
    """Normalizes line endings, tabs, horizontal spacing, and excessive blank lines."""

    def normalize_line_breaks(self, text: str) -> Tuple[str, bool]:
        """
        Normalize all line endings (CRLF and CR) to standard Unix LF (\n).
        Replaces form feeds and vertical tabs with standard newlines.
        """
        if not text:
            return "", False

        original = text
        # Convert CRLF to LF
        normalized = text.replace("\r\n", "\n")
        # Convert standalone CR to LF
        normalized = normalized.replace("\r", "\n")
        # Convert form feed (\f) and vertical tab (\v)
        normalized = normalized.replace("\f", "\n").replace("\v", "\n")

        changed = normalized != original
        return normalized, changed

    def normalize_whitespace(self, text: str) -> Tuple[str, bool]:
        """
        Normalize tabs, repeated spaces, and excessive blank lines.
        Strips trailing spaces from lines, collapses horizontal spaces,
        and limits consecutive blank lines to at most two.
        """
        if not text:
            return "", False

        original = text

        # 1. Strip zero-width invisible characters
        normalized = ZERO_WIDTH_CHARS.sub("", text)

        # 2. Convert Unicode spaces (non-breaking, em-space, etc.) to standard space
        normalized = UNICODE_SPACES.sub(" ", normalized)

        # 3. Process line-by-line: collapse repeated horizontal spaces & strip trailing
        lines = []
        for line in normalized.split("\n"):
            # Collapse tabs and multi-spaces within the line
            line_clean = REPEATED_SPACES.sub(" ", line)
            # Strip trailing whitespace from line (preserve leading for list indent if small)
            line_clean = line_clean.rstrip()
            lines.append(line_clean)

        normalized = "\n".join(lines)

        # 4. Collapse 3 or more consecutive newlines down to 2 (paragraph break)
        normalized = CONSECUTIVE_BLANK_LINES.sub("\n\n", normalized)

        # 5. Trim leading and trailing whitespace of document
        normalized = normalized.strip()

        changed = normalized != original
        return normalized, changed


whitespace_cleaner = WhitespaceCleaner()
