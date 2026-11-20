"""
Skill Text and Format Normalizer
Phase 3 | Feature 17: Skill Normalization
Handles Layer 1 normalization: casing, whitespace, safe Unicode, and punctuation cleanup.
"""

import re
import unicodedata
from typing import Optional


def normalize_skill_text(raw_text: Optional[str]) -> str:
    """
    Standardizes raw skill text while preserving meaningful technical symbols (like C++, C#, .NET).
    Performs Unicode normalization, strips extraneous punctuation, and folds excessive whitespace.
    """
    if not raw_text:
        return ""

    # Safe NFKC Unicode normalization
    text = unicodedata.normalize("NFKC", str(raw_text).strip())

    # Replace fancy quotes, bullet points, brackets, and em-dashes
    text = re.sub(r"[\u2018\u2019\u201a\u201b]", "'", text)
    text = re.sub(r"[\u201c\u201d\u201e\u201f]", '"', text)
    text = re.sub(r"[\u2013\u2014]", "-", text)
    text = re.sub(r"[•·▪\*\t\r\n]", " ", text)

    # Strip enclosing parentheses, brackets, quotes
    text = re.sub(r"^[\(\[\{\"\']+", "", text)
    text = re.sub(r"[\)\]\}\"\']+$", "", text)

    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def create_lookup_key(text: Optional[str]) -> str:
    """
    Generates a deterministic lookup key for dictionary and alias index mapping.
    Lowercases, collapses spaces, and standardizes separators.
    Preserves crucial symbols: '+', '#', '.', '-'
    Example: 'Node.js' -> 'nodejs', 'React.js' -> 'reactjs', 'C++' -> 'c++', 'Postgre SQL' -> 'postgresql'
    """
    if not text:
        return ""

    norm = normalize_skill_text(text).lower()

    # Special handling for common dot variations like node.js, vue.js, next.js
    norm = re.sub(r"\.js\b", "js", norm)
    norm = re.sub(r"\.net\b", "net", norm)

    # Remove internal dots, hyphens, and whitespace for key matching if not C++ / C#
    if norm in ("c++", "c#", "f#", ".net", "net"):
        return norm

    # Remove punctuation except plus and hash
    key = re.sub(r"[^\w\+#]", "", norm)
    return key
