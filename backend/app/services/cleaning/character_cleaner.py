"""
Special Character and Encoding Cleaner
Phase 2 | Feature 4: Text Cleaning (Task 3)
"""

import re
from typing import Tuple

# Non-printable control characters (ASCII 0-8, 11-12, 14-31, DEL 127)
# Standard \t (9) and \n (10) are explicitly excluded
CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Standard unicode punctuation replacements
QUOTE_REPLACEMENTS = {
    "“": '"',
    "”": '"',
    "„": '"',
    "‟": '"',
    "‘": "'",
    "’": "'",
    "‚": "'",
    "‛": "'",
    "`": "'",
}

LIGATURE_REPLACEMENTS = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬅ": "ft",
    "ﬆ": "st",
}

DASH_REPLACEMENTS = {
    "—": "-",  # em-dash
    "–": "-",  # en-dash
    "―": "-",  # horizontal bar
    "‒": "-",  # figure dash
    "‐": "-",  # hyphen
    "−": "-",  # minus sign
}


class CharacterCleaner:
    """
    Cleans non-printable control characters, normalizes Unicode artifacts,
    while strictly preserving technical terms (C++, C#, .NET, Node.js),
    international characters, URLs, and emails.
    """

    def clean_control_characters(self, text: str) -> Tuple[str, bool]:
        """Strip non-printable ASCII control characters."""
        if not text:
            return "", False

        cleaned = CONTROL_CHARS_PATTERN.sub("", text)
        changed = cleaned != text
        return cleaned, changed

    def normalize_unicode_and_artifacts(self, text: str) -> Tuple[str, bool]:
        """
        Normalize smart quotes, ligatures, dashes, and ellipses.
        Does NOT alter technical symbols or international characters.
        """
        if not text:
            return "", False

        original = text
        result = text

        # 1. Normalize ligatures
        for lig, repl in LIGATURE_REPLACEMENTS.items():
            if lig in result:
                result = result.replace(lig, repl)

        # 2. Normalize smart quotes and apostrophes
        for q, repl in QUOTE_REPLACEMENTS.items():
            if q in result:
                result = result.replace(q, repl)

        # 3. Normalize typographic dashes
        for d, repl in DASH_REPLACEMENTS.items():
            if d in result:
                result = result.replace(d, repl)

        # 4. Normalize ellipses
        if "…" in result:
            result = result.replace("…", "...")

        changed = result != original
        return result, changed


character_cleaner = CharacterCleaner()
