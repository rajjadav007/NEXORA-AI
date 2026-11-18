"""Unit tests for formatting_cleaner service."""

import pytest
from app.services.cleaning.formatting_cleaner import formatting_cleaner


def test_normalize_bullets_various_styles():
    raw = (
        "- First item\n"
        "* Second item\n"
        "+ Third item\n"
        "▪ Fourth item\n"
        "▫ Fifth item\n"
        "► Sixth item\n"
        "• Seventh item"
    )
    cleaned, modified = formatting_cleaner.normalize_bullets_and_lists(raw)
    assert modified is True
    lines = cleaned.split("\n")
    assert all(line.startswith("• ") for line in lines)
    assert len(lines) == 7


def test_normalize_numbered_lists():
    raw = (
        "1) Step one\n"
        "2) Step two\n"
        "3. Step three"
    )
    cleaned, modified = formatting_cleaner.normalize_bullets_and_lists(raw)
    assert modified is True
    assert "1. Step one" in cleaned
    assert "2. Step two" in cleaned
    assert "3. Step three" in cleaned


def test_normalize_bullets_preserves_nested_indentation():
    raw = "  * Sub-bullet with spaces\n    - Deeper bullet"
    cleaned, modified = formatting_cleaner.normalize_bullets_and_lists(raw)
    assert modified is True
    assert cleaned == "  • Sub-bullet with spaces\n    • Deeper bullet"


def test_normalize_bullets_no_change_when_already_standard():
    raw = "• Item 1\n• Item 2\n1. Numbered 1"
    cleaned, modified = formatting_cleaner.normalize_bullets_and_lists(raw)
    assert modified is False
    assert cleaned == raw


def test_normalize_heading_spacing():
    raw = (
        "John Doe\n"
        "Software Engineer\n"
        "EXPERIENCE\n"
        "Senior Developer at Tech Corp\n"
        "EDUCATION\n"
        "B.S. in Computer Science\n"
        "SKILLS\n"
        "Python, React, SQL"
    )
    cleaned, modified = formatting_cleaner.normalize_heading_spacing(raw)
    assert modified is True
    assert "\n\nEXPERIENCE\n" in cleaned
    assert "\n\nEDUCATION\n" in cleaned
    assert "\n\nSKILLS\n" in cleaned


def test_normalize_heading_spacing_no_double_padding():
    raw = "John Doe\n\nEXPERIENCE\nSenior Developer"
    cleaned, modified = formatting_cleaner.normalize_heading_spacing(raw)
    assert modified is False
    assert cleaned == raw


def test_remove_consecutive_duplicates():
    raw = (
        "Header Page 1\n"
        "Header Page 1\n"
        "Experience Section\n"
        "Built microservices with Go.\n"
        "Built microservices with Go.\n"
        "Education Section"
    )
    cleaned, modified = formatting_cleaner.remove_consecutive_duplicates(raw)
    assert modified is True
    assert cleaned.count("Header Page 1") == 1
    assert cleaned.count("Built microservices with Go.") == 1


def test_remove_consecutive_duplicates_preserves_legitimate_non_consecutive_skills():
    raw = (
        "Role 1:\n"
        "Python\n"
        "Role 2:\n"
        "Python\n"
        "Role 3:\n"
        "Python"
    )
    cleaned, modified = formatting_cleaner.remove_consecutive_duplicates(raw)
    assert modified is False
    assert cleaned.count("Python") == 3
