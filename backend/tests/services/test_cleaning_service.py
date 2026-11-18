"""Unit tests for the orchestrated TextCleaningService."""

import pytest
from app.services.cleaning.cleaning_service import TextCleaningService
from app.schemas.cleaning import CleaningStatus


def test_clean_empty_text():
    service = TextCleaningService()
    res = service.clean_text("", resume_id="test-resume-123")
    assert res.cleaning_status == CleaningStatus.EMPTY_INPUT
    assert res.cleaned_text == ""
    assert res.original_character_count == 0
    assert res.cleaned_character_count == 0
    assert len(res.cleaning_actions) == 0


def test_clean_already_clean_text():
    service = TextCleaningService()
    clean_sample = "John Doe\n\nSoftware Engineer with experience in Python and C++."
    res = service.clean_text(clean_sample, resume_id="test-resume-123")
    assert res.cleaning_status == CleaningStatus.NO_CHANGE
    assert res.cleaned_text == clean_sample
    assert res.cleaned_character_count == res.original_character_count
    assert len(res.cleaning_actions) == 0


def test_clean_full_pipeline_orchestration():
    service = TextCleaningService()
    raw = (
        "John  Doe  \r\n\r\n\r\n"
        "Senior \x00Engineer at \u201cTechCorp\u201d\r\n"
        "SKILLS\r\n"
        "- C++ programming & C#\r\n"
        "- .NET, Node.js, and Python\r\n"
        "- .NET, Node.js, and Python\r\n"
        "EXPERIENCE\r\n"
        "1) Led CI/CD pipelines\r\n"
        "Contact: user@domain.com, https://github.com/johndoe"
    )

    res = service.clean_text(raw, resume_id="test-resume-123")

    assert res.cleaning_status == CleaningStatus.SUCCESS
    assert res.cleaned_character_count > 0

    cleaned = res.cleaned_text

    # Verify whitespace and line endings
    assert "\r" not in cleaned
    assert "John Doe" in cleaned
    assert "Senior Engineer" in cleaned

    # Verify quotes normalized
    assert '"TechCorp"' in cleaned

    # Verify section headings spaced
    assert "\n\nSKILLS\n" in cleaned
    assert "\n\nEXPERIENCE\n" in cleaned

    # Verify bullet and list normalization
    assert "• C++ programming & C#" in cleaned
    assert "• .NET, Node.js, and Python" in cleaned
    assert "1. Led CI/CD pipelines" in cleaned

    # Verify consecutive duplicate removed
    assert cleaned.count("• .NET, Node.js, and Python") == 1

    # Verify technical symbols preserved exactly
    assert "C++" in cleaned
    assert "C#" in cleaned
    assert ".NET" in cleaned
    assert "Node.js" in cleaned
    assert "CI/CD" in cleaned
    assert "user@domain.com" in cleaned
    assert "https://github.com/johndoe" in cleaned

    # Verify action log
    actions = res.cleaning_actions
    assert "line_breaks_normalized" in actions
    assert "whitespace_normalized" in actions
    assert "bullets_normalized" in actions


def test_accented_names_preserved():
    service = TextCleaningService()
    raw = "Ren\u00e9 Fran\u00e7ois\nCurriculum Vitae"
    res = service.clean_text(raw, resume_id="test-resume-123")
    assert "René François" in res.cleaned_text
