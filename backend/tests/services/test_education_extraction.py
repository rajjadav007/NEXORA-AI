"""
Unit Tests for Education Extraction Engine
Phase 3 | Feature 14: Education Analysis
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.education.section_detector import detect_education_section
from app.services.education.degree_normalizer import (
    normalize_degree,
    infer_field_of_study,
    classify_degree_level,
)
from app.services.education.grade_normalizer import (
    normalize_grade,
    format_grade_display,
)
from app.services.education.date_status_detector import (
    extract_dates_and_status,
    parse_date_string,
)
from app.services.education.timeline_generator import (
    generate_education_timeline,
    detect_timeline_overlaps,
)
from app.services.education.validator import (
    validate_education_entry,
    validate_education_entries,
)
from app.services.education.confidence_scorer import (
    compute_education_entry_confidence,
    compute_batch_confidence,
)
from app.services.education.deterministic_extractor import (
    extract_education_deterministic,
)
from app.services.education.ai_extractor import EducationAIExtractor


SAMPLE_EDUCATION_TEXT = """
Raj Jadav
Software Engineer

EDUCATION
Bachelor of Computer Applications (BCA)
Bangalore University, Bengaluru, Karnataka, India
2020 - 2023
CGPA: 8.42 / 10.0
Achievements: First rank in Department of Computer Science
Coursework: Data Structures, Algorithms, Database Management Systems

Higher Secondary Certificate (12th Grade)
National Public School, Bengaluru
2018 - 2020
Percentage: 88.5%

EXPERIENCE
Software Engineer at Acme Corp (2023 - Present)
"""


# ----------------------------------------------------------------------
# 1. Section Detection Tests
# ----------------------------------------------------------------------

def test_detect_education_section_success():
    section_text, is_explicit = detect_education_section(SAMPLE_EDUCATION_TEXT)
    assert "Bachelor of Computer Applications" in section_text
    assert "Higher Secondary Certificate" in section_text
    assert "Software Engineer at Acme Corp" not in section_text
    assert is_explicit is True


def test_detect_education_section_varied_headers():
    variants = [
        "ACADEMIC QUALIFICATIONS\nB.Tech in Computer Science\nNIT Trichy",
        "EDUCATIONAL BACKGROUND\nMaster of Science\nMIT",
        "ACADEMIC HISTORY\nPhD in Physics\nStanford University",
    ]
    for text in variants:
        sec, is_explicit = detect_education_section(text)
        assert len(sec) > 0
        assert is_explicit is True


def test_detect_education_section_missing():
    text = "John Doe\nSummary\nProficient in Python and JavaScript.\nSkills: React, Node.js"
    sec, is_explicit = detect_education_section(text)
    # When no section header is found, fallback returns full text with False
    assert text.strip() in sec
    assert is_explicit is False


# ----------------------------------------------------------------------
# 2. Degree Normalization Tests
# ----------------------------------------------------------------------

def test_normalize_common_degrees():
    assert normalize_degree("BCA")[0] == "Bachelor of Computer Applications"
    assert normalize_degree("B.Tech")[0] == "Bachelor of Technology"
    assert normalize_degree("BTech in Computer Science")[0] == "Bachelor of Technology"
    assert normalize_degree("M.Sc")[0] == "Master of Science"
    assert normalize_degree("MCA")[0] == "Master of Computer Applications"
    assert normalize_degree("Ph.D.")[0] == "Doctor of Philosophy"
    assert "12th" in normalize_degree("12th Grade")[0]
    assert "10th" in normalize_degree("10th Standard")[0]


def test_classify_degree_level():
    assert classify_degree_level("Bachelor of Computer Applications") == "undergraduate"
    assert classify_degree_level("Master of Science") == "postgraduate"
    assert classify_degree_level("PhD in Physics") == "doctorate"
    assert classify_degree_level("Diploma in Mechanical Engineering") == "diploma"
    assert classify_degree_level("Higher Secondary School (12th)") == "higher_secondary"
    assert classify_degree_level("Secondary School Examination (10th)") in ("high_school", "secondary")
    assert classify_degree_level("AWS Certified Solutions Architect") in ("certification", "other")


def test_normalize_unknown_degree():
    # Must preserve raw degree without corrupting or hallucinating
    raw = "Certificate of Quantum Cryptographic Studies"
    norm, level = normalize_degree(raw)
    assert norm == raw
    assert level in ("certification", "other")


def test_infer_field_of_study():
    field = infer_field_of_study("B.Tech in Computer Science & Engineering")
    assert "Computer Science" in field

    field_app = infer_field_of_study("Bachelor of Computer Applications")
    assert "Computer Applications" in field_app


# ----------------------------------------------------------------------
# 3. Grade Normalization Tests (Preserve Scale, No Auto-Conversion)
# ----------------------------------------------------------------------

def test_normalize_cgpa():
    grade = normalize_grade("CGPA: 7.47 / 10")
    assert grade is not None
    assert grade["type"] == "cgpa"
    assert grade["value"] == 7.47
    assert grade["scale"] == 10.0
    # Crucial rule: never auto-convert CGPA to percentage
    assert grade["value"] != 74.7


def test_normalize_gpa():
    grade = normalize_grade("GPA: 3.8 / 4.0")
    assert grade is not None
    assert grade["type"] == "gpa"
    assert grade["value"] == 3.8
    assert grade["scale"] == 4.0


def test_normalize_percentage():
    grade = normalize_grade("88.5%")
    assert grade is not None
    assert grade["type"] == "percentage"
    assert grade["value"] == 88.5
    assert grade["scale"] == 100.0


def test_normalize_honors_classification():
    grade = normalize_grade("First Class with Distinction")
    assert grade is not None
    assert grade["type"] == "classification"
    assert "First Class" in grade["raw"]


def test_normalize_invalid_grade():
    # CGPA above scale
    grade = normalize_grade("CGPA: 11.5 / 10.0")
    assert grade is None


def test_format_grade_display():
    cgpa = {"type": "cgpa", "value": 8.5, "scale": 10.0}
    assert format_grade_display(cgpa) == "8.5 / 10.0 CGPA"

    pct = {"type": "percentage", "value": 92.0, "scale": 100.0}
    assert format_grade_display(pct) == "92%"

    cls_grade = {"type": "classification", "raw": "Summa Cum Laude"}
    assert format_grade_display(cls_grade) == "Summa Cum Laude"


# ----------------------------------------------------------------------
# 4. Date and Status Detection Tests
# ----------------------------------------------------------------------

def test_extract_dates_completed_range():
    start, end, status = extract_dates_and_status("2019 - 2023")
    assert start == "2019"
    assert end == "2023"
    assert status == "completed"


def test_extract_dates_ongoing():
    start, end, status = extract_dates_and_status("August 2022 - Present")
    assert start is not None and "2022" in start
    assert end in (None, "Present")
    assert status == "ongoing"


def test_extract_dates_expected():
    start, end, status = extract_dates_and_status("2023 - Expected 2026")
    assert start == "2023"
    assert end == "2026"
    assert status == "expected"


def test_extract_dates_single_year():
    start, end, status = extract_dates_and_status("Graduated in 2021")
    assert end == "2021"
    assert status == "completed"


# ----------------------------------------------------------------------
# 5. Timeline Generation Tests
# ----------------------------------------------------------------------

def test_timeline_sorting():
    entries = [
        {"degree": "10th", "start_date": "2016", "end_date": "2018", "graduation_status": "completed"},
        {"degree": "BCA", "start_date": "2020", "end_date": "2023", "graduation_status": "completed"},
        {"degree": "MCA", "start_date": "2023", "end_date": "2025", "graduation_status": "ongoing"},
        {"degree": "12th", "start_date": "2018", "end_date": "2020", "graduation_status": "completed"},
    ]
    sorted_entries = generate_education_timeline(entries)

    # Ongoing should be first
    assert sorted_entries[0]["degree"] == "MCA"
    # Then completed descending by end_date
    assert sorted_entries[1]["degree"] == "BCA"
    assert sorted_entries[2]["degree"] == "12th"
    assert sorted_entries[3]["degree"] == "10th"


def test_detect_timeline_overlaps():
    entries = [
        {"degree": "BCA", "start_date": "2020", "end_date": "2023"},
        {"degree": "Diploma", "start_date": "2021", "end_date": "2022"},
    ]
    overlaps = detect_timeline_overlaps(entries)
    assert len(overlaps) == 1
    assert "BCA" in overlaps[0] and "Diploma" in overlaps[0]


# ----------------------------------------------------------------------
# 6. Validation and Anti-Hallucination Tests
# ----------------------------------------------------------------------

def test_validate_entry_success():
    entry = {
        "degree": "Bachelor of Technology",
        "institution": "National Institute of Technology",
        "start_date": "2018",
        "end_date": "2022",
        "grade": {"type": "cgpa", "value": 8.1, "scale": 10.0},
    }
    is_valid, errors = validate_education_entry(entry)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_entry_invalid_date_order():
    entry = {
        "degree": "B.Tech",
        "institution": "NIT",
        "start_date": "2023",
        "end_date": "2020",  # Invalid
    }
    is_valid, errors = validate_education_entry(entry)
    assert is_valid is False
    assert any("before" in e.lower() or "chronology" in e.lower() for e in errors)


def test_validate_entry_missing_mandatory_fields():
    entry = {"start_date": "2020"}
    is_valid, errors = validate_education_entry(entry)
    assert is_valid is False
    assert any("degree" in e.lower() for e in errors)


# ----------------------------------------------------------------------
# 7. Confidence Scorer Tests
# ----------------------------------------------------------------------

def test_compute_entry_confidence():
    entry = {
        "degree": "Bachelor of Computer Applications",
        "normalized_degree": "Bachelor of Computer Applications",
        "institution": "Bangalore University",
        "start_date": "2020",
        "end_date": "2023",
        "grade": {"type": "cgpa", "value": 8.42, "scale": 10.0},
        "source_evidence": ["Bachelor of Computer Applications", "Bangalore University"],
    }
    score = compute_education_entry_confidence(entry)
    assert score >= 0.85
    assert score <= 1.0


def test_compute_entry_confidence_partial():
    entry = {
        "degree": "Unknown Program",
        "institution": None,
        "start_date": None,
        "end_date": None,
    }
    score = compute_education_entry_confidence(entry, is_explicit_section=False)
    assert score <= 0.65

    # Completely empty entry
    assert compute_education_entry_confidence({}) == 0.0


# ----------------------------------------------------------------------
# 8. Deterministic Multi-Entry Extractor Tests
# ----------------------------------------------------------------------

def test_deterministic_multi_entry_extraction():
    entries = extract_education_deterministic(SAMPLE_EDUCATION_TEXT)
    assert len(entries) >= 2

    degrees = [e["normalized_degree"] for e in entries]
    assert "Bachelor of Computer Applications" in degrees
    assert any("12th" in d or "Higher Secondary" in d for d in degrees)

    bca_entry = next(e for e in entries if "Computer Applications" in e["normalized_degree"])
    assert "Bangalore University" in bca_entry["institution"]
    assert bca_entry["grade"] is not None
    assert bca_entry["grade"]["type"] == "cgpa"
    assert bca_entry["grade"]["value"] == 8.42
    assert bca_entry["graduation_status"] == "completed"


from app.services.education.service import EducationExtractionService


# ----------------------------------------------------------------------
# 9. AI Extractor Graceful Fallback Tests
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ai_extractor_fallback_on_llm_error():
    service = EducationExtractionService()

    # Simulate network/LLM error in sandbox
    with patch("app.services.education.service.education_ai_extractor.extract_education_entries", AsyncMock(return_value=None)):
        entries = await service.extract_education(
            resume_id="test-resume-123",
            cleaned_text_override=SAMPLE_EDUCATION_TEXT,
        )
        # Should gracefully fall back to deterministic extraction
        assert len(entries) >= 2
        normalized_degrees = [e.normalized_degree for e in entries]
        assert "Bachelor of Computer Applications" in normalized_degrees
