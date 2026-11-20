"""
Date and Duration Calculator for Experience Analysis
Phase 3 | Feature 15: Experience Analysis
Normalizes dates, computes role durations, calculates non-overlapping career experience, and identifies career gaps.
"""

import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

CURRENT_KEYWORDS = [
    r"\bpresent\b",
    r"\bcurrent\b",
    r"\bnow\b",
    r"\btill\s+date\b",
    r"\bongoing\b",
    r"\bto\s+date\b",
]


def is_current_indicator(text: str) -> bool:
    """Checks if a string indicates active current employment."""
    if not text:
        return False
    lower = text.lower().strip()
    return any(re.search(pat, lower) for pat in CURRENT_KEYWORDS)


def parse_date_to_parts(date_str: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """
    Parses a date string into (year, month).
    Supports formats like 'YYYY-MM', 'YYYY', 'MMM YYYY', 'Month YYYY', 'MM/YYYY'.
    """
    if not date_str or not date_str.strip():
        return None, None

    cleaned = date_str.strip()

    # Format: YYYY-MM
    iso_match = re.match(r"^(\d{4})[-/.](\d{1,2})$", cleaned)
    if iso_match:
        year, month = int(iso_match.group(1)), int(iso_match.group(2))
        if 1 <= month <= 12 and 1950 <= year <= 2050:
            return year, month

    # Format: MM/YYYY or MM-YYYY
    slash_match = re.match(r"^(\d{1,2})[-/.](\d{4})$", cleaned)
    if slash_match:
        month, year = int(slash_match.group(1)), int(slash_match.group(2))
        if 1 <= month <= 12 and 1950 <= year <= 2050:
            return year, month

    # Format: Month YYYY (e.g. 'June 2025', 'Jun 2025')
    text_month_match = re.search(r"([a-zA-Z]{3,9})[\s,]+(\d{4})", cleaned)
    if text_month_match:
        m_str = text_month_match.group(1).lower()
        year = int(text_month_match.group(2))
        month = MONTH_NAMES.get(m_str)
        if month and 1950 <= year <= 2050:
            return year, month

    # Format: YYYY Month (e.g. '2025 June')
    year_first_match = re.search(r"(\d{4})[\s,]+([a-zA-Z]{3,9})", cleaned)
    if year_first_match:
        year = int(year_first_match.group(1))
        m_str = year_first_match.group(2).lower()
        month = MONTH_NAMES.get(m_str)
        if month and 1950 <= year <= 2050:
            return year, month

    # Format: Year only (e.g. '2023')
    year_only_match = re.search(r"\b(19\d{2}|20\d{2})\b", cleaned)
    if year_only_match:
        year = int(year_only_match.group(1))
        return year, None

    return None, None


def normalize_date_string(date_str: Optional[str]) -> Optional[str]:
    """
    Normalizes a date string into standard 'YYYY-MM' or 'YYYY' format.
    """
    year, month = parse_date_to_parts(date_str)
    if year is None:
        return None
    if month is not None:
        return f"{year:04d}-{month:02d}"
    return f"{year:04d}"


def extract_date_range_from_text(text: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Searches a line or chunk of text for a date range like 'June 2023 - Present' or '2021 - 2023'.
    Returns (start_date_normalized, end_date_normalized, is_current).
    """
    if not text:
        return None, None, False

    # Check for current indicator
    is_curr = False
    for pat in CURRENT_KEYWORDS:
        if re.search(pat, text, re.IGNORECASE):
            is_curr = True
            break

    # Look for ranges with separators (- / to / – / —)
    range_match = re.search(
        r"((?:[a-zA-Z]{3,9}\s+)?\d{4})\s*(?:[-–—]|to)\s*((?:[a-zA-Z]{3,9}\s+)?\d{4}|present|current|till\s+date|ongoing)",
        text,
        re.IGNORECASE,
    )
    if range_match:
        start_raw = range_match.group(1)
        end_raw = range_match.group(2)
        start_norm = normalize_date_string(start_raw)
        if is_current_indicator(end_raw):
            return start_norm, None, True
        else:
            end_norm = normalize_date_string(end_raw)
            return start_norm, end_norm, False

    # Month/Year - Month/Year e.g. 06/2021 - 09/2022
    slash_range = re.search(
        r"(\d{1,2}[/.-]\d{4})\s*(?:[-–—]|to)\s*(\d{1,2}[/.-]\d{4}|present|current)",
        text,
        re.IGNORECASE,
    )
    if slash_range:
        start_raw = slash_range.group(1)
        end_raw = slash_range.group(2)
        start_norm = normalize_date_string(start_raw)
        if is_current_indicator(end_raw):
            return start_norm, None, True
        else:
            return start_norm, normalize_date_string(end_raw), False

    return None, None, is_curr


def calculate_individual_duration_months(
    start_date: Optional[str],
    end_date: Optional[str],
    is_current: bool = False,
    ref_date: Optional[datetime] = None,
) -> Optional[int]:
    """
    Calculates duration in months for a single role.
    Handles month-level and year-only precision.
    If end_date is missing and not is_current, returns None.
    If range is invalid (start > end), returns None.
    """
    start_year, start_month = parse_date_to_parts(start_date)
    if start_year is None:
        return None

    if is_current:
        today = ref_date or datetime.now()
        end_year = today.year
        end_month = today.month
    else:
        if not end_date:
            return None
        end_year, end_month = parse_date_to_parts(end_date)
        if end_year is None:
            return None

    # Handle month vs year-only
    s_m = start_month if start_month is not None else 1
    e_m = end_month if end_month is not None else 12

    # Check validity
    if end_year < start_year or (end_year == start_year and e_m < s_m):
        return None

    # Duration calculation
    diff_months = (end_year - start_year) * 12 + (e_m - s_m)

    # For month-level, if same month or difference calculated, count difference or min 1
    if start_month is not None and end_month is not None:
        return max(1, diff_months)

    # Year-only difference
    year_diff = (end_year - start_year) * 12
    return max(1, year_diff)


def date_to_absolute_month(year: int, month: int) -> int:
    """Converts a (year, month) into absolute month count."""
    return year * 12 + month


def calculate_aggregate_experience_months(
    experiences: List[Dict[str, Any]],
    ref_date: Optional[datetime] = None,
) -> int:
    """
    Calculates total non-overlapping career experience in months.
    Uses the interval union algorithm: combines all active [start_month, end_month]
    intervals so overlapping employment is never double-counted.
    """
    intervals: List[Tuple[int, int]] = []
    today = ref_date or datetime.now()

    for exp in experiences:
        start_date = exp.get("start_date")
        end_date = exp.get("end_date")
        is_current = exp.get("is_current", False)

        start_year, start_month = parse_date_to_parts(start_date)
        if start_year is None:
            continue

        s_m = start_month if start_month is not None else 1
        start_abs = date_to_absolute_month(start_year, s_m)

        if is_current:
            end_abs = date_to_absolute_month(today.year, today.month)
        elif end_date:
            end_year, end_month = parse_date_to_parts(end_date)
            if end_year is None:
                continue
            e_m = end_month if end_month is not None else 12
            end_abs = date_to_absolute_month(end_year, e_m)
        else:
            continue

        if end_abs >= start_abs:
            intervals.append((start_abs, end_abs))

    if not intervals:
        return 0

    # Sort intervals by start
    intervals.sort(key=lambda x: x[0])

    # Merge overlapping intervals
    merged: List[Tuple[int, int]] = []
    current_start, current_end = intervals[0]

    for start, end in intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    merged.append((current_start, current_end))

    # Sum total unique months across disjoint intervals
    total_months = sum((end - start) for start, end in merged)
    return max(0, total_months)


def calculate_career_gaps(
    experiences: List[Dict[str, Any]],
    min_gap_months: int = 2,
) -> List[Dict[str, Any]]:
    """
    Identifies gaps in employment between chronological roles.
    Only calculates when dates support reliable calculation.
    """
    parsed_roles = []
    for exp in experiences:
        s_date = exp.get("start_date")
        e_date = exp.get("end_date")
        is_curr = exp.get("is_current", False)

        s_y, s_m = parse_date_to_parts(s_date)
        if not s_y:
            continue
        s_abs = date_to_absolute_month(s_y, s_m or 1)

        if is_curr:
            e_abs = date_to_absolute_month(datetime.now().year, datetime.now().month)
        elif e_date:
            e_y, e_m = parse_date_to_parts(e_date)
            if not e_y:
                continue
            e_abs = date_to_absolute_month(e_y, e_m or 12)
        else:
            continue

        if e_abs >= s_abs:
            parsed_roles.append({
                "company": exp.get("company"),
                "job_title": exp.get("job_title"),
                "start_abs": s_abs,
                "end_abs": e_abs,
                "start_date": s_date,
                "end_date": e_date,
            })

    if len(parsed_roles) < 2:
        return []

    # Sort chronologically by start date
    parsed_roles.sort(key=lambda x: x["start_abs"])

    gaps = []
    for i in range(len(parsed_roles) - 1):
        prev_end = parsed_roles[i]["end_abs"]
        next_start = parsed_roles[i + 1]["start_abs"]

        gap_months = next_start - prev_end
        if gap_months >= min_gap_months:
            # Format gap dates
            prev_y, prev_m = divmod(prev_end, 12)
            if prev_m == 0:
                prev_y -= 1
                prev_m = 12
            next_y, next_m = divmod(next_start, 12)
            if next_m == 0:
                next_y -= 1
                next_m = 12

            gaps.append({
                "from_date": f"{prev_y:04d}-{prev_m:02d}",
                "to_date": f"{next_y:04d}-{next_m:02d}",
                "duration_months": gap_months,
                "preceding_company": parsed_roles[i]["company"],
                "succeeding_company": parsed_roles[i + 1]["company"],
            })

    return gaps
