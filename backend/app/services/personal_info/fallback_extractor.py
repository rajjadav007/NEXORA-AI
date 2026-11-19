"""
Deterministic Heuristic Fallback Extractor
Phase 3 | Feature 13: Personal Information Extraction
Extracts candidate name and location when local Ollama AI is offline or unavailable.
"""

import re
from typing import Optional, Dict, Any, Tuple

# Section titles and generic job titles to reject as names
REJECT_NAME_TOKENS = {
    "resume",
    "curriculum",
    "vitae",
    "cv",
    "contact",
    "profile",
    "summary",
    "experience",
    "education",
    "projects",
    "skills",
    "developer",
    "engineer",
    "architect",
    "manager",
    "intern",
    "fresher",
    "student",
    "designer",
    "analyst",
    "lead",
    "consultant",
    "about",
    "phone",
    "email",
    "address",
}

# Recognized common countries for location extraction
COMMON_COUNTRIES = {
    "india",
    "united states",
    "usa",
    "us",
    "united kingdom",
    "uk",
    "canada",
    "germany",
    "france",
    "australia",
    "singapore",
    "netherlands",
    "switzerland",
    "ireland",
    "uae",
    "japan",
    "spain",
    "brazil",
}

# Recognized major Indian / US states / abbreviations
COMMON_REGIONS = {
    "karnataka", "maharashtra", "delhi", "tamil nadu", "telangana", "uttar pradesh",
    "california", "texas", "new york", "florida", "washington", "massachusetts",
    "ca", "tx", "ny", "fl", "wa", "ma", "il", "on", "bc"
}


def extract_fallback_name(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extracts candidate full_name, first_name, last_name from the top header lines of resume.
    Returns (full_name, first_name, last_name).
    """
    if not text:
        return None, None, None

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    candidate_lines = lines[:6]

    for line in candidate_lines:
        # Skip if contains contact elements
        if "@" in line or "http" in line or "www." in line or "linkedin" in line or "github" in line:
            continue
        # Skip if contains digits (phone, date, etc)
        if any(char.isdigit() for char in line):
            continue
        # Skip if too long or too short
        if len(line) < 3 or len(line) > 50:
            continue

        words = line.split()
        if not (2 <= len(words) <= 4):
            continue

        # Check if words look like common job titles or section headers
        lower_words = [w.lower().strip(".,;:|") for w in words]
        if any(w in REJECT_NAME_TOKENS for w in lower_words):
            continue

        # Check that all words are purely alphabetic (with optional hyphens)
        if not all(re.match(r"^[A-Za-z\-']+$", w) for w in words):
            continue

        # Check title case or all caps
        if line.isupper() or all(w[0].isupper() for w in words):
            full_name = " ".join(words).title()
            first_name = words[0].title()
            last_name = words[-1].title() if len(words) > 1 else None
            return full_name, first_name, last_name

    return None, None, None


def extract_fallback_location(text: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Extracts candidate location (city, state, country) from top header lines.
    """
    if not text:
        return None

    lines = [line.strip() for line in text.split("\n") if line.strip()][:15]

    for line in lines:
        # Ignore lines with emails or URLs
        if "@" in line or "http" in line or "www." in line:
            continue

        # Look for comma-separated location tokens e.g. "Bengaluru, Karnataka, India" or "Austin, TX, USA"
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if 2 <= len(parts) <= 3:
            # Check if any token matches known country or region or contains no digits
            has_digits = any(any(c.isdigit() for c in p) for p in parts)
            if has_digits:
                # Could be a zip code, strip zip code
                parts = [re.sub(r"\b\d{5,6}\b", "", p).strip() for p in parts]
                parts = [p for p in parts if p]

            if not (2 <= len(parts) <= 3):
                continue

            last_part_lower = parts[-1].lower()
            mid_part_lower = parts[1].lower() if len(parts) == 3 else ""

            is_loc = False
            if last_part_lower in COMMON_COUNTRIES or last_part_lower in COMMON_REGIONS:
                is_loc = True
            elif mid_part_lower in COMMON_REGIONS:
                is_loc = True
            elif any(kw in line.lower() for kw in ("location:", "address:", "based in")):
                is_loc = True

            if is_loc:
                if len(parts) == 3:
                    return {
                        "city": parts[0].title(),
                        "state": parts[1].title(),
                        "country": parts[2].title(),
                    }
                else:
                    # 2 parts: city, state OR city, country
                    part2_title = parts[1].title()
                    if last_part_lower in COMMON_COUNTRIES:
                        return {"city": parts[0].title(), "state": None, "country": part2_title}
                    else:
                        return {"city": parts[0].title(), "state": part2_title, "country": None}

    return None
