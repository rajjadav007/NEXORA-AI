"""
Deterministic Project Extractor
Phase 3 | Feature 18: Project Intelligence
Extracts project titles, dates, technologies, URLs, measurable metrics, and contribution indicators.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from app.services.projects.normalizer import (
    normalize_project_title,
    classify_project_category,
    extract_and_categorize_urls,
)
from app.services.projects.skill_linker import link_technologies_to_canonical_skills
from app.services.skills.dictionary import skill_dictionary

MONTH_YEAR_PATTERN = r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*(?:20\d\d|\d\d)\b"
YEAR_PATTERN = r"\b(?:19|20)\d{2}\b"
DATE_RANGE_PATTERN = rf"({MONTH_YEAR_PATTERN}|{YEAR_PATTERN})\s*(?:[-–—to]+)\s*({MONTH_YEAR_PATTERN}|{YEAR_PATTERN}|Present|Current|Ongoing)"


def extract_dates_and_ongoing(text: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Extracts start date, end date, and ongoing status from project text block.
    """
    range_match = re.search(DATE_RANGE_PATTERN, text, re.IGNORECASE)
    if range_match:
        start_str = range_match.group(1).strip()
        end_str = range_match.group(2).strip()
        is_ongoing = bool(re.search(r"\b(?:present|current|ongoing)\b", end_str, re.IGNORECASE))
        end_val = None if is_ongoing else end_str
        return start_str, end_val, is_ongoing

    # Check standalone single date
    single_match = re.search(MONTH_YEAR_PATTERN, text, re.IGNORECASE) or re.search(YEAR_PATTERN, text)
    if single_match:
        return single_match.group(0).strip(), None, False

    return None, None, False


def extract_team_information(text: str) -> Tuple[str, Optional[int], Optional[str]]:
    """
    Identifies team type (individual, team, unknown), team size, and extracted candidate role.
    """
    text_lower = text.lower()
    team_type = "unknown"
    team_size = None
    role = None

    # Check role
    role_match = re.search(r"\b(?:role|position)[:\s]+([A-Za-z0-9\s/-]{3,40})(?:\n|,|\.|$)", text, re.IGNORECASE)
    if role_match:
        role = role_match.group(1).strip()

    # Check team size keywords: "team of 4", "4-member team"
    size_match = re.search(r"\b(?:team\s+of\s+(\d{1,2})|(\d{1,2})[- ]member\s+team|group\s+of\s+(\d{1,2}))\b", text_lower)
    if size_match:
        team_size = int(size_match.group(1) or size_match.group(2) or size_match.group(3))
        team_type = "team"
    elif re.search(r"\b(?:team\s+lead|worked\s+in\s+a\s+team|collaborated\s+with|our\s+team|team\s+members)\b", text_lower):
        team_type = "team"
    elif re.search(r"\b(?:solo\s+project|independently\s+developed|individual\s+project|single-handedly|personal\s+project)\b", text_lower):
        team_type = "individual"

    return team_type, team_size, role


def extract_technologies_from_block(text: str) -> List[str]:
    """
    Detects technology keywords within a project block using canonical skill dictionary.
    """
    found_techs: List[str] = []
    seen = set()

    # 1. Look for explicit "Technologies: Python, React" lines
    explicit_line = re.search(r"\b(?:technologies|tech\s+stack|tools\s+used|built\s+with)[:\s]+([^\n\.]+)", text, re.IGNORECASE)
    if explicit_line:
        tokens = re.split(r"[,;•|/]\s*", explicit_line.group(1))
        for tok in tokens:
            cleaned = tok.strip().strip(".()[]")
            if cleaned and len(cleaned) <= 30:
                match = skill_dictionary.lookup(cleaned)
                cname = match[0]["name"] if match else cleaned
                if cname.lower() not in seen:
                    seen.add(cname.lower())
                    found_techs.append(cname)

    # 2. General word scanning for known catalog skills
    words = re.findall(r"\b[A-Za-z0-9\+#\.-]{2,30}\b", text)
    for w in words:
        if w.lower() in ("and", "the", "for", "with", "used", "built", "project", "system"):
            continue
        match = skill_dictionary.lookup(w)
        if match:
            cname = match[0]["name"]
            if cname.lower() not in seen:
                seen.add(cname.lower())
                found_techs.append(cname)

    return found_techs


def extract_measurable_outcomes_and_achievements(lines: List[str]) -> Tuple[List[str], List[str]]:
    """
    Extracts explicit quantifiable metrics (%, latencies, counts) and awards/rankings.
    Never invents metrics.
    """
    achievements: List[str] = []
    measurable: List[str] = []

    for line in lines:
        clean = line.strip().lstrip("-•*").strip()
        if not clean:
            continue

        clean_lower = clean.lower()

        # Measurable outcomes (contains numbers, percentages, or latencies, metrics)
        if re.search(r"(?:\d+(?:\.\d+)?%|\b(?:reduced|improved|increased|decreased|accelerated|handled|served)\b.*?\d+|\b\d+(?:,\d+)*\+?\s*(?:ms|seconds|x\s+faster|fps|users|requests|qps|active\s+users|records|transactions))\b", clean_lower):
            measurable.append(clean)
        # Achievements (awards, hackathon rankings, published papers)
        elif re.search(r"\b(?:won|1st|2nd|3rd|first|second|third|winner|runner-up|finalist|awarded|best\s+project|published|accepted\s+at)\b", clean_lower):
            achievements.append(clean)

    return achievements, measurable


def extract_deterministic_project(
    block_text: str,
    section_name: str = "Projects",
) -> Dict[str, Any]:
    """
    Performs full deterministic extraction on a single project text block.
    """
    lines = [l.strip() for l in block_text.split("\n") if l.strip()]
    if not lines:
        return {}

    raw_title_line = lines[0]
    normalized_title = normalize_project_title(raw_title_line)

    # Project Links
    links = extract_and_categorize_urls(block_text)

    # Dates
    start_date, end_date, is_ongoing = extract_dates_and_ongoing(block_text)

    # Team Info
    team_type, team_size, role = extract_team_information(block_text)

    # Category
    category = classify_project_category(block_text, section_name)

    # Technologies
    raw_techs = extract_technologies_from_block(block_text)
    canonical_techs, linked_skills = link_technologies_to_canonical_skills(raw_techs, block_text)

    # Descriptions & Bullets
    body_lines = lines[1:] if len(lines) > 1 else lines
    bullet_lines = [l.lstrip("-•*").strip() for l in body_lines if l.startswith("-") or l.startswith("•") or l.startswith("*")]

    # Achievements & Metrics
    achievements, measurable_outcomes = extract_measurable_outcomes_and_achievements(body_lines)

    short_desc = body_lines[0] if body_lines else raw_title_line
    detailed_desc = "\n".join(body_lines) if body_lines else short_desc

    responsibilities = bullet_lines if bullet_lines else [short_desc]

    return {
        "project_title": raw_title_line,
        "normalized_title": normalized_title,
        "project_category": category,
        "short_description": short_desc[:300],
        "detailed_description": detailed_desc,
        "problem_statement": None,
        "proposed_solution": None,
        "domain": None,
        "project_role": role,
        "team_type": team_type,
        "team_size": team_size,
        "start_date": start_date,
        "end_date": end_date,
        "is_ongoing": is_ongoing,
        "technologies": canonical_techs,
        "skills": linked_skills,
        "responsibilities": responsibilities,
        "achievements": achievements,
        "measurable_outcomes": measurable_outcomes,
        "project_links": links,
        "source_section": section_name,
        "source_evidence": [l for l in lines[:5]],
        "extraction_method": "deterministic",
        "review_status": "pending",
    }
