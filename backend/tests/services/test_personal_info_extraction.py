"""
Unit Tests for Personal Information Extraction Engine
Phase 3 | Feature 13: Personal Information Extraction
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.personal_info.deterministic_extractor import (
    extract_email,
    extract_phone_and_country_code,
    extract_urls,
    extract_deterministic_info,
)
from app.services.personal_info.fallback_extractor import (
    extract_fallback_name,
    extract_fallback_location,
)
from app.services.personal_info.validator import (
    validate_email,
    validate_phone,
    validate_country_code,
    validate_name,
    validate_url,
    validate_urls_list,
    validate_location,
)
from app.services.personal_info.normalizer import (
    normalize_name,
    normalize_email,
    normalize_phone,
    normalize_country_code,
    normalize_url,
    normalize_urls_list,
    normalize_location,
)
from app.services.personal_info.confidence_scorer import compute_confidence_scores
from app.services.personal_info.ai_extractor import AIExtractor
from app.services.personal_info.service import PersonalInfoExtractionService


SAMPLE_RESUME_TEXT = """
Raj Jadav
Bengaluru, Karnataka, India
Email: raj.jadav@example.com | Phone: +91 9876543210
LinkedIn: https://linkedin.com/in/rajjadav
GitHub: https://github.com/rajjadav
Portfolio: https://rajjadav.dev
Blog: https://medium.com/@rajjadav

PROFESSIONAL SUMMARY
Senior Software Engineer with 5+ years of experience in distributed systems.
"""


# ----------------------------------------------------------------------
# 1. Deterministic Extraction Tests
# ----------------------------------------------------------------------

def test_extract_valid_email():
    email = extract_email(SAMPLE_RESUME_TEXT)
    assert email == "raj.jadav@example.com"


def test_extract_email_missing():
    text = "John Doe\nSoftware Developer\nNo contact info"
    assert extract_email(text) is None


def test_extract_phone_and_country_code():
    phone, country_code = extract_phone_and_country_code(SAMPLE_RESUME_TEXT)
    assert phone == "+91 9876543210"
    assert country_code == "+91"


def test_extract_phone_us_format():
    text = "Alice Smith\nContact: +1 (555) 234-5678\nAustin, Texas"
    phone, country_code = extract_phone_and_country_code(text)
    assert "555" in phone
    assert country_code == "+1"


def test_extract_phone_missing():
    text = "Just a resume without phone numbers."
    phone, country_code = extract_phone_and_country_code(text)
    assert phone is None
    assert country_code is None


def test_extract_urls_classification():
    urls = extract_urls(SAMPLE_RESUME_TEXT)
    assert urls["linkedin_url"] == "https://linkedin.com/in/rajjadav"
    assert urls["github_url"] == "https://github.com/rajjadav"
    assert urls["portfolio_url"] == "https://rajjadav.dev"
    assert any("medium.com" in u for u in urls["other_urls"])


def test_extract_urls_without_linkedin():
    text = "Jane Doe\nGitHub: https://github.com/janedoe\nPortfolio: https://jane.me"
    urls = extract_urls(text)
    assert urls["linkedin_url"] is None
    assert urls["github_url"] == "https://github.com/janedoe"
    assert urls["portfolio_url"] == "https://jane.me"


def test_extract_urls_duplicate_handling():
    text = "https://github.com/user https://github.com/user https://github.com/user"
    urls = extract_urls(text)
    assert urls["github_url"] == "https://github.com/user"
    assert urls["other_urls"] == []


# ----------------------------------------------------------------------
# 2. Heuristic Fallback & Anti-Hallucination Tests
# ----------------------------------------------------------------------

def test_fallback_name_extraction():
    full_name, first, last = extract_fallback_name(SAMPLE_RESUME_TEXT)
    assert full_name == "Raj Jadav"
    assert first == "Raj"
    assert last == "Jadav"


def test_fallback_name_rejects_header_keywords():
    text = "CURRICULUM VITAE\nSOFTWARE ENGINEER\nRaj Jadav\nContact"
    full_name, first, last = extract_fallback_name(text)
    assert full_name == "Raj Jadav"


def test_fallback_name_empty_text():
    full_name, first, last = extract_fallback_name("")
    assert full_name is None
    assert first is None
    assert last is None


def test_fallback_location_extraction_three_parts():
    loc = extract_fallback_location(SAMPLE_RESUME_TEXT)
    assert loc is not None
    assert loc["city"] == "Bengaluru"
    assert loc["state"] == "Karnataka"
    assert loc["country"] == "India"


def test_fallback_location_two_parts():
    text = "John Smith\nAustin, Texas\nEngineer"
    loc = extract_fallback_location(text)
    assert loc is not None
    assert loc["city"] == "Austin"
    assert loc["state"] == "Texas"


def test_fallback_location_missing():
    text = "No location here at all\nJust technical skills\nPython, Docker"
    loc = extract_fallback_location(text)
    assert loc is None


# ----------------------------------------------------------------------
# 3. Validation Tests
# ----------------------------------------------------------------------

def test_validate_email_valid():
    assert validate_email("candidate@domain.com") == "candidate@domain.com"


def test_validate_email_invalid_syntax():
    assert validate_email("invalid-email-without-at") is None
    assert validate_email("user@.com") is None
    assert validate_email("user@domain") is None
    assert validate_email("user with spaces@domain.com") is None


def test_validate_phone_valid():
    assert validate_phone("+91 9876543210") == "+91 9876543210"
    assert validate_phone("9876543210") == "9876543210"


def test_validate_phone_invalid_length():
    assert validate_phone("12345") is None  # Too short
    assert validate_phone("12345678901234567890") is None  # Too long


def test_validate_country_code():
    assert validate_country_code("+91") == "+91"
    assert validate_country_code("+1") == "+1"
    assert validate_country_code("91") is None
    assert validate_country_code("+12345") is None


def test_validate_name_rejects_emails_and_numbers():
    assert validate_name("Raj Jadav") == "Raj Jadav"
    assert validate_name("raj@example.com") is None
    assert validate_name("Engineer123") is None
    assert validate_name("https://github.com") is None


def test_validate_url_valid_and_malformed():
    assert validate_url("https://linkedin.com/in/user") == "https://linkedin.com/in/user"
    assert validate_url("http://example.com") == "http://example.com"
    assert validate_url("not a url") is None
    assert validate_url("ftp://example.com") is None


# ----------------------------------------------------------------------
# 4. Normalization Tests
# ----------------------------------------------------------------------

def test_normalize_name():
    assert normalize_name("  raj  jadav  ") == "Raj Jadav"
    assert normalize_name("RAJ JADAV") == "Raj Jadav"


def test_normalize_email():
    assert normalize_email("  RAJ.JADAV@Example.COM  ") == "raj.jadav@example.com"


def test_normalize_url():
    assert normalize_url("http://github.com/user/") == "https://github.com/user"
    assert normalize_url("www.linkedin.com/in/user") == "https://linkedin.com/in/user"


# ----------------------------------------------------------------------
# 5. Confidence Scoring Tests
# ----------------------------------------------------------------------

def test_confidence_scores_calculation():
    data = {
        "full_name": "Raj Jadav",
        "first_name": "Raj",
        "last_name": "Jadav",
        "email": "raj@example.com",
        "phone": "+91 9876543210",
        "country_code": "+91",
        "location": {"city": "Bengaluru", "state": "Karnataka", "country": "India"},
        "linkedin_url": "https://linkedin.com/in/raj",
        "github_url": "https://github.com/raj",
        "portfolio_url": None,
    }
    sources = {"full_name": "ai", "location": "ai"}
    scores = compute_confidence_scores(data, sources)

    assert scores["email"] == 1.0
    assert scores["phone"] == 0.95
    assert scores["full_name"] == 0.98
    assert scores["location"] == 0.85
    assert scores["portfolio_url"] == 0.0


# ----------------------------------------------------------------------
# 6. AI Extractor & Graceful Fallback Tests
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ai_extractor_graceful_fallback_when_offline():
    extractor = AIExtractor(base_url="http://localhost:9999", timeout=0.5)
    result = await extractor.extract_identity_and_location("Some Resume Text")
    assert result is None  # Safe return None, trigger fallback


@pytest.mark.asyncio
async def test_full_pipeline_with_ai_offline():
    service = PersonalInfoExtractionService()
    # When Ollama is offline or returns None, service seamlessly uses deterministic + heuristic
    result = await service.extract_personal_information(
        resume_id="temp-staging-id",
        cleaned_text_override=SAMPLE_RESUME_TEXT,
        db=None,
    )
    assert result.full_name == "Raj Jadav"
    assert result.email == "raj.jadav@example.com"
    assert result.phone == "+91 9876543210"
    assert result.country_code == "+91"
    assert result.location is not None
    assert result.location.city == "Bengaluru"
    assert result.linkedin_url == "https://linkedin.com/in/rajjadav"
    assert result.github_url == "https://github.com/rajjadav"
    assert result.portfolio_url == "https://rajjadav.dev"
    assert result.extraction_status == "completed"
