"""
Unit Tests for Experience Extraction Engine
Phase 3 | Feature 15: Experience Analysis
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.services.experience.section_detector import detect_experience_section
from app.services.experience.normalizer import (
    normalize_company,
    normalize_job_title,
    detect_employment_type,
    extract_technologies_from_text,
)
from app.services.experience.date_duration_calculator import (
    parse_date_to_parts,
    normalize_date_string,
    extract_date_range_from_text,
    calculate_individual_duration_months,
    calculate_aggregate_experience_months,
    calculate_career_gaps,
)
from app.services.experience.content_extractor import (
    categorize_experience_bullets,
    extract_measurable_metrics,
    is_measurable_impact,
)
from app.services.experience.career_progression import analyze_career_progression
from app.services.experience.confidence_scorer import compute_experience_confidence
from app.services.experience.deterministic_extractor import extract_deterministic_experience
from app.services.experience.ai_extractor import ExperienceAIExtractor


SAMPLE_EXPERIENCE_TEXT = """
Raj Jadav
Bengaluru, India | raj.jadav@example.com

PROFESSIONAL EXPERIENCE

Acme Technologies | Senior AI Engineer
Bengaluru, India
06/2024 - Present
- Architected and deployed microservices using FastAPI and Docker
- Integrated LLM inference pipelines with Ollama and LangChain
- Improved query response times by 40% and reduced p95 latency to 120ms
- Led a team of 4 software engineers in agile sprints

Beta Soft | AI Engineer Intern
Bengaluru, India
01/2024 - 05/2024
- Developed automated data cleaning pipelines using Python and Pandas
- Built REST APIs for candidate evaluation
- Collaborated with senior engineers on PyTorch model fine-tuning

Gamma Freelance | Freelance Python Developer
Remote
06/2023 - 12/2023
- Built web scraping tools using BeautifulSoup and Requests
- Delivered 5 client projects with 100% on-time delivery rate

EDUCATION
Bachelor of Computer Applications (BCA)
Bangalore University, 2020 - 2023

PROJECTS
Smart Career Copilot
- Built an open-source tool for career planning using React and Python
"""


# ----------------------------------------------------------------------
# 1. Section Detection Tests
# ----------------------------------------------------------------------

def test_detect_experience_section_success():
    section_text, is_explicit = detect_experience_section(SAMPLE_EXPERIENCE_TEXT)
    assert is_explicit is True
    assert "Acme Technologies" in section_text
    assert "Beta Soft" in section_text
    assert "Gamma Freelance" in section_text
    assert "Bangalore University" not in section_text
    assert "Smart Career Copilot" not in section_text


def test_detect_experience_section_varied_headers():
    variants = [
        "WORK EXPERIENCE\nSoftware Engineer at Google\n2022 - 2024",
        "EMPLOYMENT HISTORY\nData Analyst at Meta\n2021 - 2023",
        "WORK HISTORY\nPython Developer at Startup\n2020 - 2021",
        "INTERNSHIPS\nAI Intern at Research Labs\n2023",
    ]
    for text in variants:
        sec, is_exp = detect_experience_section(text)
        assert is_exp is True
        assert len(sec) > 0


def test_detect_experience_section_empty():
    sec, is_exp = detect_experience_section("Raj Jadav\nNo experience listed.")
    assert is_exp is False
    assert sec == ""


# ----------------------------------------------------------------------
# 2. Company & Job Title Normalization Tests
# ----------------------------------------------------------------------

def test_normalize_company():
    assert normalize_company("  Acme Technologies, Inc.  ") == "Acme Technologies, Inc."
    assert normalize_company("• Google LLC") == "Google LLC"
    assert normalize_company("   ") is None
    assert normalize_company("X") is None


def test_normalize_job_title():
    assert normalize_job_title("software engineer") == "Software Engineer"
    assert normalize_job_title("AI ENGINEER") == "Ai Engineer"
    assert normalize_job_title("- Senior Developer -") == "Senior Developer"
    assert normalize_job_title("") is None


# ----------------------------------------------------------------------
# 3. Employment Type Detection Tests
# ----------------------------------------------------------------------

def test_detect_employment_type_variations():
    assert detect_employment_type(job_title="AI Engineer Intern") == "internship"
    assert detect_employment_type(job_title="Summer Intern") == "internship"
    assert detect_employment_type(job_title="Freelance Web Developer") == "freelance"
    assert detect_employment_type(job_title="Independent Contractor") == "freelance"
    assert detect_employment_type(job_title="Contract QA Engineer") == "contract"
    assert detect_employment_type(job_title="Part-time Software Tutor") == "part_time"
    assert detect_employment_type(job_title="Graduate Research Assistant") == "research"
    assert detect_employment_type(job_title="Volunteer Community Lead") == "volunteer"
    assert detect_employment_type(job_title="Senior Software Engineer") == "full_time"


# ----------------------------------------------------------------------
# 4. Date Extraction & Duration Calculation Tests
# ----------------------------------------------------------------------

def test_parse_date_and_normalization():
    assert normalize_date_string("2024-06") == "2024-06"
    assert normalize_date_string("June 2024") == "2024-06"
    assert normalize_date_string("06/2024") == "2024-06"
    assert normalize_date_string("2024") == "2024"
    assert normalize_date_string("invalid-date") is None


def test_extract_date_range_from_text():
    s, e, curr = extract_date_range_from_text("June 2023 - Present")
    assert s == "2023-06"
    assert e is None
    assert curr is True

    s, e, curr = extract_date_range_from_text("01/2022 to 08/2023")
    assert s == "2022-01"
    assert e == "2023-08"
    assert curr is False


def test_individual_duration_months():
    # June 2025 to Sept 2025
    assert calculate_individual_duration_months("2025-06", "2025-09", is_current=False) == 3

    # Year-only: 2021 to 2023 = 24 months
    assert calculate_individual_duration_months("2021", "2023", is_current=False) == 24

    # Ongoing role with fixed reference date
    ref = datetime(2025, 12, 1)
    dur = calculate_individual_duration_months("2025-06", None, is_current=True, ref_date=ref)
    assert dur == 6

    # Missing end date and not current = None
    assert calculate_individual_duration_months("2023-01", None, is_current=False) is None

    # Invalid range (start > end) = None
    assert calculate_individual_duration_months("2024-06", "2023-01", is_current=False) is None


# ----------------------------------------------------------------------
# 5. Overlapping Employment & Gap Calculation Tests (Prompt Test Case 9 & 10)
# ----------------------------------------------------------------------

def test_overlapping_employment_duration_not_double_counted():
    """
    Test Case 9: Overlapping jobs.
    Individual durations calculated separately and aggregate duration does not double-count overlapping periods.
    """
    # Role 1: Jan 2024 to Dec 2024 (12 months)
    # Role 2: Concurrent freelance role: June 2024 to Dec 2024 (6 months)
    # Total unique career experience must be 11 or 12 months, NOT 18 months!
    roles = [
        {"start_date": "2024-01", "end_date": "2024-12", "is_current": False},
        {"start_date": "2024-06", "end_date": "2024-12", "is_current": False},
    ]
    indiv1 = calculate_individual_duration_months("2024-01", "2024-12")
    indiv2 = calculate_individual_duration_months("2024-06", "2024-12")
    assert indiv1 == 11 or indiv1 == 12
    assert indiv2 == 6

    aggregate = calculate_aggregate_experience_months(roles)
    # Union of [Jan, Dec] and [Jun, Dec] is [Jan, Dec] = 11 months
    assert aggregate == 11
    assert aggregate < (indiv1 + indiv2)


def test_career_gaps_calculation():
    """Test Case 10: Employment gaps calculated only when dates support calculation."""
    roles = [
        {"company": "Company A", "job_title": "Developer", "start_date": "2022-01", "end_date": "2022-06"},
        {"company": "Company B", "job_title": "Senior Developer", "start_date": "2023-01", "end_date": "2023-12"},
    ]
    gaps = calculate_career_gaps(roles, min_gap_months=2)
    assert len(gaps) == 1
    assert gaps[0]["duration_months"] == 7
    assert gaps[0]["preceding_company"] == "Company A"
    assert gaps[0]["succeeding_company"] == "Company B"


# ----------------------------------------------------------------------
# 6. Content Categorization & Quantified Metrics Tests (Prompt Test Case 6 & 8)
# ----------------------------------------------------------------------

def test_responsibilities_without_achievements():
    """Test Case 6: Responsibilities without achievements extracted without inventing achievements."""
    bullets = [
        "Collaborated with project managers and frontend developers in daily standups",
        "Wrote clean code following organizational style guides",
        "Assisted in sprint reviews and backlog refinement",
    ]
    categorized = categorize_experience_bullets(bullets)
    assert len(categorized["responsibilities"]) >= 1
    assert len(categorized["achievements"]) == 0
    assert len(categorized["measurable_impact"]) == 0


def test_quantified_achievement_preserves_numeric_result():
    """Test Case 8: Quantified achievement preserves the actual numeric result."""
    bullets = [
        "Improved API throughput by 35% using asynchronous FastAPI workers",
        "Reduced database query latency from 800ms to 150ms",
        "Scaled user authentication system to handle 50,000 requests/min",
    ]
    categorized = categorize_experience_bullets(bullets)
    assert len(categorized["achievements"]) >= 2
    assert "35%" in categorized["measurable_impact"]
    assert any("800ms" in m or "150ms" in m for m in categorized["measurable_impact"])


# ----------------------------------------------------------------------
# 7. Technology Extraction Tests (Prompt Test Case 7)
# ----------------------------------------------------------------------

def test_extract_technologies_from_experience():
    """Test Case 7: Technologies mentioned in experience are correctly extracted."""
    text = "Developed Python and FastAPI backend services with PostgreSQL and Redis caching. Deployed with Docker on AWS."
    techs = extract_technologies_from_text(text)
    assert "Python" in techs
    assert "FastAPI" in techs
    assert "PostgreSQL" in techs
    assert "Redis" in techs
    assert "Docker" in techs
    assert "AWS" in techs


# ----------------------------------------------------------------------
# 8. Career Progression Tests
# ----------------------------------------------------------------------

def test_career_progression_internal_promotion():
    roles = [
        {"company": "Acme Corp", "job_title": "AI Engineer Intern", "employment_type": "internship", "start_date": "2023-01", "end_date": "2023-06"},
        {"company": "Acme Corp", "job_title": "Software Engineer", "employment_type": "full_time", "start_date": "2023-07", "end_date": "2024-12"},
    ]
    prog = analyze_career_progression(roles)
    timeline = prog["timeline"]
    assert len(timeline) == 2
    assert timeline[0]["transition_type"] == "initial"
    assert timeline[1]["transition_type"] == "promotion"
    assert timeline[1]["is_promotion"] is True
    assert any("Observed internal progression" in obs for obs in prog["observations"])


# ----------------------------------------------------------------------
# 9. Deterministic Extractor & Sample Test Cases (1, 2, 3, 4, 5, 11, 12)
# ----------------------------------------------------------------------

def test_test_case_1_single_internship():
    """Test Case 1: Single internship. Correct company, role, dates, and employment type."""
    text = """
    Acme Technologies | AI Engineer Intern
    06/2024 - 09/2024
    - Developed Python-based AI applications
    """
    entries = extract_deterministic_experience(text)
    assert len(entries) == 1
    assert "Acme Technologies" in entries[0]["company"]
    assert "Intern" in entries[0]["job_title"]
    assert entries[0]["employment_type"] == "internship"
    assert entries[0]["start_date"] == "2024-06"
    assert entries[0]["end_date"] == "2024-09"


def test_test_case_2_multiple_companies():
    """Test Case 2: Multiple companies. All distinct roles extracted."""
    entries = extract_deterministic_experience(SAMPLE_EXPERIENCE_TEXT)
    assert len(entries) >= 2
    companies = [e.get("company") for e in entries if e.get("company")]
    assert any("Acme" in c for c in companies)
    assert any("Beta" in c for c in companies)


def test_test_case_3_current_employment():
    """Test Case 3: Current employment. is_current = true only when supported by evidence."""
    text = "Software Engineer at Acme Corp\n2023 - Present\n- Core services"
    entries = extract_deterministic_experience(text)
    assert len(entries) == 1
    assert entries[0]["is_current"] is True
    assert entries[0]["end_date"] is None


def test_test_case_4_missing_end_date():
    """Test Case 4: Missing end date. end_date = null unless current employment is explicitly indicated."""
    text = "Software Engineer at Acme Corp\n2022\n- Core development"
    entries = extract_deterministic_experience(text)
    assert len(entries) == 1
    assert entries[0]["is_current"] is False


def test_test_case_5_missing_company_name():
    """Test Case 5: Missing company name. company = null."""
    text = "Software Engineer\n2021 - 2022\n- Built internal utilities"
    entries = extract_deterministic_experience(text)
    assert len(entries) == 1
    assert entries[0]["job_title"] == "Software Engineer"
    assert entries[0]["company"] is None


def test_test_case_11_no_professional_experience():
    """Test Case 11: No professional experience. Return empty experience list."""
    sec, is_exp = detect_experience_section("John Doe\nSummary: Looking for entry-level roles.\nEDUCATION\nBS Computer Science")
    assert sec == ""
    assert is_exp is False


def test_test_case_12_academic_project_only():
    """Test Case 12: Academic project only. Do not classify academic projects as employment."""
    resume_with_projects_only = """
    John Doe
    ACADEMIC PROJECTS
    E-Commerce Website | React & Node.js
    Built full stack website for university final year submission.
    """
    sec, is_exp = detect_experience_section(resume_with_projects_only)
    assert is_exp is False
    assert sec == ""


# ----------------------------------------------------------------------
# 10. AI Extractor Fallback Tests
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ai_extractor_fallback_on_timeout():
    extractor = ExperienceAIExtractor(timeout=0.001, base_url="http://invalid-localhost:9999")
    res = await extractor.extract_experience_entries("Software Engineer at Google 2023 - Present")
    assert res is None  # Graceful fallback, no uncaught exception
