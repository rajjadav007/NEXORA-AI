"""
Unit tests for WhitespaceCleaner.
Phase 2 | Feature 4: Text Cleaning (Task 1 & Task 2)
"""

import pytest
from app.services.cleaning.whitespace_cleaner import whitespace_cleaner


def test_normalize_line_breaks_crlf_and_cr():
    raw = "Line 1\r\nLine 2\rLine 3\nLine 4\fLine 5"
    normalized, changed = whitespace_cleaner.normalize_line_breaks(raw)

    assert changed is True
    assert "\r" not in normalized
    assert "\f" not in normalized
    assert normalized == "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"


def test_normalize_whitespace_tabs_and_multiple_spaces():
    raw = "Senior   Software    Engineer\t\tin   Silicon Valley  "
    cleaned, changed = whitespace_cleaner.normalize_whitespace(raw)

    assert changed is True
    assert "Senior Software Engineer in Silicon Valley" == cleaned


def test_normalize_whitespace_excessive_blank_lines():
    raw = "Paragraph 1\n\n\n\n\n\nParagraph 2\n\n\nParagraph 3"
    cleaned, changed = whitespace_cleaner.normalize_whitespace(raw)

    assert changed is True
    assert "Paragraph 1\n\nParagraph 2\n\nParagraph 3" == cleaned


def test_normalize_whitespace_unicode_spaces():
    # Non-breaking space \u00a0 and zero-width space \u200b
    raw = "FastAPI\u00a0Developer\u200bwith Python"
    cleaned, changed = whitespace_cleaner.normalize_whitespace(raw)

    assert changed is True
    assert "FastAPI Developerwith Python" == cleaned


def test_normalize_whitespace_empty():
    cleaned, changed = whitespace_cleaner.normalize_whitespace("")
    assert cleaned == ""
    assert changed is False
