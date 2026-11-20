"""
Deterministic Extractor for Experience Analysis
Phase 3 | Feature 15: Experience Analysis
Rule-based deterministic extraction for professional experience entries.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from app.services.experience.normalizer import (
    normalize_company,
    normalize_job_title,
    detect_employment_type,
    extract_technologies_from_text,
)
from app.services.experience.date_duration_calculator import (
    extract_date_range_from_text,
    calculate_individual_duration_months,
)
from app.services.experience.content_extractor import categorize_experience_bullets

# Common role keywords
ROLE_KEYWORDS = [
    r"\bsoftware\s+engineer\b",
    r"\bsoftware\s+developer\b",
    r"\bai\s+engineer\b",
    r"\bml\s+engineer\b",
    r"\bmachine\s+learning\s+engineer\b",
    r"\bdata\s+scientist\b",
    r"\bdata\s+analyst\b",
    r"\bdata\s+engineer\b",
    r"\bbackend\s+developer\b",
    r"\bfrontend\s+developer\b",
    r"\bfull\s+stack\s+developer\b",
    r"\bweb\s+developer\b",
    r"\bpython\s+developer\b",
    r"\bdevops\s+engineer\b",
    r"\bresearch\s+intern\b",
    r"\bai/ml\s+intern\b",
    r"\bsoftware\s+intern\b",
    r"\bengineering\s+intern\b",
    r"\bproduct\s+manager\b",
    r"\bproject\s+manager\b",
    r"\bbusiness\s+analyst\b",
    r"\bqa\s+engineer\b",
    r"\bsystem\s+administrator\b",
    r"\bconsultant\b",
]


def is_job_header_line(line: str) -> bool:
    """Checks whether a line looks like an experience entry heading."""
    clean = line.strip()
    if not clean or len(clean) < 4:
        return False

    # Check for role keywords
    lower = clean.lower()
    for rk in ROLE_KEYWORDS:
        if re.search(rk, lower):
            return True

    # Check for 'at <Company>' pattern
    if re.search(r"\b(?:at|@)\s+[A-Z][a-zA-Z0-9\s.,&-]{2,}", clean):
        return True

    # Check for title/company separator e.g. "Software Engineer | Google" or "Google - Software Engineer"
    if ("|" in clean or " - " in clean or " – " in clean) and re.search(r"\b(?:engineer|developer|analyst|intern|manager|lead|architect|consultant|specialist|officer|assistant|scientist)\b", lower):
        return True

    return False


def parse_header_line(line: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parses a job header line to extract (job_title, company, location).
    Examples:
    - 'Software Engineer at Acme Corp, Bengaluru'
    - 'Acme Corp | Software Engineer | 2021 - 2023'
    - 'AI Engineer Intern - Example Technologies'
    """
    clean = line.strip()

    # Pattern: '<Title> at/@ <Company>[, <Location>]'
    at_match = re.search(r"^(.*?)\s+(?:at|@)\s+([^,]+)(?:,\s*(.+))?$", clean, re.IGNORECASE)
    if at_match:
        title = at_match.group(1).strip()
        comp = at_match.group(2).strip()
        loc = at_match.group(3).strip() if at_match.group(3) else None
        return normalize_job_title(title), normalize_company(comp), loc

    # Pattern with pipe: '<Part1> | <Part2> [| <Part3>]'
    if "|" in clean:
        parts = [p.strip() for p in clean.split("|")]
        # Identify which is title and which is company
        title = None
        comp = None
        loc = None
        for p in parts:
            if any(re.search(rk, p.lower()) for rk in ROLE_KEYWORDS) or re.search(r"\b(?:engineer|developer|intern|lead|manager|analyst)\b", p.lower()):
                title = p
            elif not comp and not re.search(r"\d{4}", p):
                comp = p
            elif not loc and not re.search(r"\d{4}", p):
                loc = p
        return normalize_job_title(title), normalize_company(comp), loc

    # Pattern with hyphen: '<Company> - <Title>' or '<Title> - <Company>'
    if " - " in clean or " – " in clean:
        parts = re.split(r"\s+[-–]\s+", clean)
        if len(parts) >= 2:
            part0, part1 = parts[0], parts[1]
            if any(re.search(rk, part0.lower()) for rk in ROLE_KEYWORDS):
                return normalize_job_title(part0), normalize_company(part1), None
            else:
                return normalize_job_title(part1), normalize_company(part0), None

    # Just title found
    for rk in ROLE_KEYWORDS:
        m = re.search(rk, clean, re.IGNORECASE)
        if m:
            return normalize_job_title(m.group(0)), None, None

    return None, None, None


def extract_deterministic_experience(section_text: str) -> List[Dict[str, Any]]:
    """
    Parses experience entries from raw section text using structural patterns.
    """
    if not section_text or not section_text.strip():
        return []

    lines = [line.strip() for line in section_text.splitlines() if line.strip()]
    if not lines:
        return []

    entries = []
    current_entry = None
    current_bullets = []

    def finalize_entry(entry, bullets):
        if not entry:
            return
        categorized = categorize_experience_bullets(bullets)
        entry["responsibilities"] = categorized["responsibilities"]
        entry["technical_contributions"] = categorized["technical_contributions"]
        entry["achievements"] = categorized["achievements"]
        entry["measurable_impact"] = categorized["measurable_impact"]

        # Extract technologies from all text
        combined_text = " ".join([
            entry.get("job_title") or "",
            entry.get("company") or "",
            " ".join(bullets),
        ])
        entry["technologies"] = extract_technologies_from_text(combined_text)

        # Detect employment type
        entry["employment_type"] = detect_employment_type(
            job_title=entry.get("job_title"),
            raw_text=combined_text,
            explicit_type=entry.get("employment_type"),
        )

        # Calculate duration
        entry["duration_months"] = calculate_individual_duration_months(
            entry.get("start_date"),
            entry.get("end_date"),
            entry.get("is_current", False),
        )

        entries.append(entry)

    for line in lines:
        # Check if line contains a date range
        s_date, e_date, is_curr = extract_date_range_from_text(line)

        # Check if line is a job header
        if is_job_header_line(line) or (s_date and any(rk in line.lower() for rk in ["engineer", "developer", "intern", "analyst", "manager", "specialist"])):
            if current_entry:
                finalize_entry(current_entry, current_bullets)
                current_bullets = []

            title, comp, loc = parse_header_line(line)

            current_entry = {
                "company": comp,
                "job_title": title,
                "employment_type": None,
                "location": loc,
                "start_date": s_date,
                "end_date": e_date,
                "is_current": is_curr,
                "source_evidence": [line],
            }
        elif current_entry:
            # If current entry is missing dates and this line has them
            if not current_entry.get("start_date") and s_date:
                current_entry["start_date"] = s_date
                current_entry["end_date"] = e_date
                current_entry["is_current"] = is_curr
                current_entry["source_evidence"].append(line)
            # Check if line contains company or location if still missing
            elif not current_entry.get("company") and ("|" in line or "," in line) and not line.startswith(("-", "•", "*")):
                _, comp, loc = parse_header_line(line)
                if comp:
                    current_entry["company"] = comp
                if loc and not current_entry.get("location"):
                    current_entry["location"] = loc
            else:
                # Add to bullets
                current_bullets.append(line)

    if current_entry:
        finalize_entry(current_entry, current_bullets)

    # Filter out entries where both company and title are missing
    valid_entries = [e for e in entries if e.get("company") or e.get("job_title")]
    return valid_entries
