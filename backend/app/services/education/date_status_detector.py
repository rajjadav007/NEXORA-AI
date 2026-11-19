"""
Academic Date and Status Detector
Phase 3 | Feature 14: Education Analysis
Parses academic timelines and resolves completion/ongoing/expected status.
"""

import re
from typing import Optional, Tuple
from datetime import datetime

# Regex for academic date spans: e.g. "2020 - 2024", "2021 - Present", "Aug 2019 - May 2023", "2022 - Expected 2026"
YEAR_SPAN_REGEX = re.compile(
    r"\b((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+)?(?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+)?(?:(?:19|20)\d{2}|Present|Current|Ongoing|Pursuing|Expected\s+(?:19|20)\d{2}))\b",
    re.IGNORECASE,
)

SINGLE_YEAR_REGEX = re.compile(r"\b((?:19|20)\d{2})\b")

ONGOING_KEYWORDS = ["present", "current", "pursuing", "ongoing", "in progress", "currently enrolled"]
EXPECTED_KEYWORDS = ["expected", "exp.", "anticipating"]
DISCONTINUED_KEYWORDS = ["discontinued", "incomplete", "dropped out", "left"]


def parse_date_string(date_str: Optional[str]) -> Optional[str]:
    """Cleans and standardizes raw date strings into year or YYYY-MM if possible."""
    if not date_str:
        return None
    clean = date_str.strip()
    m = re.search(r"\b((?:19|20)\d{2})\b", clean)
    return m.group(1) if m else clean


def extract_dates_and_status(text: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Extracts (start_date, end_date, graduation_status) from education text.
    Status can be 'completed', 'ongoing', 'expected', 'discontinued'.
    """
    if not text or not text.strip():
        return None, None, "completed"

    text_lower = text.lower()

    # Check for discontinued status first
    if any(k in text_lower for k in DISCONTINUED_KEYWORDS):
        status = "discontinued"
    elif any(k in text_lower for k in ONGOING_KEYWORDS):
        status = "ongoing"
    elif any(k in text_lower for k in EXPECTED_KEYWORDS):
        status = "expected"
    else:
        status = "completed"

    start_date = None
    end_date = None

    # Search for span first
    span_match = YEAR_SPAN_REGEX.search(text)
    if span_match:
        start_date = span_match.group(1).strip()
        end_raw = span_match.group(2).strip()

        if any(k in end_raw.lower() for k in ONGOING_KEYWORDS):
            end_date = "Present"
            status = "ongoing"
        elif "expected" in end_raw.lower():
            end_year = re.search(r"(?:19|20)\d{2}", end_raw)
            end_date = end_year.group(0) if end_year else end_raw
            status = "expected"
        else:
            end_date = end_raw
            # Check if end year is in the future
            curr_year = datetime.now().year
            end_year_match = re.search(r"(?:19|20)\d{2}", end_date)
            if end_year_match:
                end_y = int(end_year_match.group(0))
                if end_y > curr_year and status == "completed":
                    status = "ongoing"

        return start_date, end_date, status

    # Search single years if no span
    years = SINGLE_YEAR_REGEX.findall(text)
    if len(years) >= 2:
        start_date = years[0]
        end_date = years[1]
        curr_year = datetime.now().year
        if int(end_date) > curr_year and status == "completed":
            status = "ongoing"
    elif len(years) == 1:
        # Single year could be graduation year
        end_date = years[0]

    return start_date, end_date, status
