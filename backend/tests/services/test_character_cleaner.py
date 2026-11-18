"""
Unit tests for CharacterCleaner.
Phase 2 | Feature 4: Text Cleaning (Task 3)
"""

import pytest
from app.services.cleaning.character_cleaner import character_cleaner


def test_clean_control_characters():
    # \x00 null byte, \x07 bell, \x1b escape, while \n and \t should stay
    raw = "Header\x00Name\x07Text\x1b\nSubheading\tDetails"
    cleaned, changed = character_cleaner.clean_control_characters(raw)

    assert changed is True
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "\x1b" not in cleaned
    assert "HeaderNameText\nSubheading\tDetails" == cleaned


def test_normalize_smart_quotes_and_apostrophes():
    raw = '“Top Performer” in engineer’s team with ‘high impact’ results'
    cleaned, changed = character_cleaner.normalize_unicode_and_artifacts(raw)

    assert changed is True
    assert '"Top Performer" in engineer\'s team with \'high impact\' results' == cleaned


def test_normalize_ligatures():
    raw = "ﬁnancial systems, ﬂexible workﬂow, and eﬃcient algorithms"
    cleaned, changed = character_cleaner.normalize_unicode_and_artifacts(raw)

    assert changed is True
    assert "financial systems, flexible workflow, and efficient algorithms" == cleaned


def test_normalize_dashes_and_ellipses():
    raw = "Experience (2020—2024): Built services… and more"
    cleaned, changed = character_cleaner.normalize_unicode_and_artifacts(raw)

    assert changed is True
    assert "Experience (2020-2024): Built services... and more" == cleaned


def test_preserves_technical_terms():
    raw = (
        "Core Stack: C++, C#, .NET Core, Node.js, Next.js, HTML/CSS, CI/CD, TCP/IP.\n"
        "Contact: engineer@example.com | https://github.com/developer/project\n"
        "Compensation: $140,000 / €120,000\n"
        "International: José Müller, Renée Dubois"
    )
    cleaned, _ = character_cleaner.normalize_unicode_and_artifacts(raw)

    # Technical terms must remain identical
    assert "C++" in cleaned
    assert "C#" in cleaned
    assert ".NET Core" in cleaned
    assert "Node.js" in cleaned
    assert "Next.js" in cleaned
    assert "HTML/CSS" in cleaned
    assert "CI/CD" in cleaned
    assert "TCP/IP" in cleaned
    assert "engineer@example.com" in cleaned
    assert "https://github.com/developer/project" in cleaned
    assert "$140,000" in cleaned
    assert "€120,000" in cleaned
    assert "José Müller" in cleaned
    assert "Renée Dubois" in cleaned
