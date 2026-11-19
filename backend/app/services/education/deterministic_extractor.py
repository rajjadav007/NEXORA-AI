"""
Deterministic Rule-Based Extractor for Education
Phase 3 | Feature 14: Education Analysis
Parses education entries from section text using structured patterns.
"""

import re
from typing import List, Dict, Any, Optional

from app.services.education.degree_normalizer import normalize_degree, DEGREE_MAPPING_RULES
from app.services.education.grade_normalizer import extract_and_normalize_grade
from app.services.education.date_status_detector import extract_dates_and_status

INSTITUTION_KEYWORDS = [
    r"\b(?:university|institute|college|academy|polytechnic|vidyalaya|campus|faculty)\b",
    r"(?<!secondary\s)(?<!high\s)\bschool\b",
]
INST_REGEX = re.compile("|".join(INSTITUTION_KEYWORDS), re.IGNORECASE)

FIELD_OF_STUDY_REGEX = re.compile(
    r"\b(?:in|of)\s+([A-Za-z\s&]{3,40})(?:\s*[,|\-•]|\s*$)",
    re.IGNORECASE,
)

COURSEWORK_REGEX = re.compile(
    r"\b(?:relevant\s+coursework|coursework|courses)\b[:\s]*([^\n]+)",
    re.IGNORECASE,
)


def extract_deterministic_education(section_text: str) -> List[Dict[str, Any]]:
    """
    Parses education text blocks into structured education entries.
    """
    if not section_text or not section_text.strip():
        return []

    # Smart line-based grouping
    lines = [line.strip() for line in section_text.splitlines() if line.strip()]
    blocks = []
    current_block = []

    for line in lines:
        has_degree = any(re.search(pat, line, re.IGNORECASE) for pat, _ in DEGREE_MAPPING_RULES)
        has_inst = bool(INST_REGEX.search(line))
        curr_has_inst = bool(INST_REGEX.search("\n".join(current_block))) if current_block else False

        if current_block and (has_degree or (has_inst and curr_has_inst)):
            blocks.append("\n".join(current_block))
            current_block = [line]
        else:
            current_block.append(line)

    if current_block:
        blocks.append("\n".join(current_block))

    entries: List[Dict[str, Any]] = []

    for block in blocks:
        # Check if this block contains any educational indicators
        has_degree = False
        raw_degree = None
        for pattern, (canonical, _) in DEGREE_MAPPING_RULES:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                has_degree = True
                # Extract full degree phrase from matching line
                for line in block.split("\n"):
                    if re.search(pattern, line, re.IGNORECASE):
                        raw_degree = line.strip("•-* ")
                        break
                break

        inst_match = INST_REGEX.search(block)
        institution = None
        location = None
        if inst_match:
            for line in block.split("\n"):
                if INST_REGEX.search(line):
                    inst_line = line.strip("•-* ")
                    # If degree is also in this line, split them
                    if raw_degree and raw_degree == inst_line and ("|" in line or "," in line or "-" in line):
                        parts = re.split(r"[,|\-•]", line)
                        for p in parts:
                            p_clean = p.strip()
                            if INST_REGEX.search(p_clean):
                                institution = p_clean
                            elif any(re.search(pat, p_clean, re.IGNORECASE) for pat, _ in DEGREE_MAPPING_RULES):
                                raw_degree = p_clean
                    else:
                        institution = inst_line

                    # Try extracting location if institution line has comma e.g. "Bangalore University, Bengaluru"
                    if institution and "," in institution:
                        parts = institution.split(",")
                        candidate_inst = parts[0].strip()
                        if INST_REGEX.search(candidate_inst):
                            institution = candidate_inst
                            location = ", ".join(p.strip() for p in parts[1:]).strip()

                    break

        # If neither degree nor institution, skip block
        if not has_degree and not institution:
            continue

        # Extract dates and status
        start_date, end_date, status = extract_dates_and_status(block)

        # Extract grade
        grade_info = extract_and_normalize_grade(block)

        # Extract field of study / specialization
        field_of_study = None
        specialization = None
        if raw_degree:
            fos_match = FIELD_OF_STUDY_REGEX.search(raw_degree)
            if fos_match:
                field_of_study = fos_match.group(1).strip()
            else:
                # Check block for field of study
                fos_match2 = FIELD_OF_STUDY_REGEX.search(block)
                if fos_match2:
                    field_of_study = fos_match2.group(1).strip()

        # Extract coursework
        coursework = []
        cw_match = COURSEWORK_REGEX.search(block)
        if cw_match:
            cw_str = cw_match.group(1).strip()
            coursework = [c.strip() for c in re.split(r"[,;•]", cw_str) if c.strip() and len(c.strip()) > 2]

        # Normalize degree title and level
        norm_degree, deg_level = normalize_degree(raw_degree)

        entry = {
            "degree": raw_degree or norm_degree,
            "normalized_degree": norm_degree,
            "degree_level": deg_level,
            "field_of_study": field_of_study,
            "specialization": specialization,
            "institution": institution,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "graduation_status": status,
            "grade": grade_info,
            "achievements": [],
            "coursework": coursework,
            "honors": [],
            "source_evidence": [block[:250]],
        }
        entries.append(entry)

    return entries


extract_education_deterministic = extract_deterministic_education
