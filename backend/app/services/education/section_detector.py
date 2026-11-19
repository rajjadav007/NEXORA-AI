"""
Education Section Detector
Phase 3 | Feature 14: Education Analysis
Detects and isolates education sections in cleaned resume text.
"""

import re
from typing import Optional, Tuple, List

# Common education section headings (normalized uppercase)
EDUCATION_HEADINGS = [
    r"\bEDUCATIONAL\s+QUALIFICATIONS?\b",
    r"\bACADEMIC\s+QUALIFICATIONS?\b",
    r"\bACADEMIC\s+BACKGROUND\b",
    r"\bACADEMIC\s+HISTORY\b",
    r"\bEDUCATIONAL\s+BACKGROUND\b",
    r"\bACADEMIC\s+CREDENTIALS?\b",
    r"\bACADEMIC\s+DETAILS?\b",
    r"\bACADEMIC\s+PROFILE\b",
    r"\bEDUCATION\s+AND\s+QUALIFICATIONS?\b",
    r"\bEDUCATION\s+AND\s+TRAINING\b",
    r"\bEDUCATION\b",
    r"\bACADEMICS\b",
    r"\bQUALIFICATIONS\b",
    r"\bSTUDIES\b",
    r"\bDEGREES\b",
]

# Section boundary headings that indicate the end of education section
BOUNDARY_HEADINGS = [
    r"\bWORK\s+EXPERIENCE\b",
    r"\bPROFESSIONAL\s+EXPERIENCE\b",
    r"\bRELEVANT\s+EXPERIENCE\b",
    r"\bEXPERIENCE\b",
    r"\bEMPLOYMENT\s+HISTORY\b",
    r"\bPROJECTS\b",
    r"\bACADEMIC\s+PROJECTS\b",
    r"\bKEY\s+PROJECTS\b",
    r"\bTECHNICAL\s+SKILLS\b",
    r"\bSKILLS\s+AND\s+ABILITIES\b",
    r"\bSKILLS\b",
    r"\bCORE\s+COMPETENCIES\b",
    r"\bCERTIFICATIONS?\b",
    r"\bLICENSES?\b",
    r"\bPUBLICATIONS?\b",
    r"\bAWARDS?\s+AND\s+HONORS?\b",
    r"\bACHIEVEMENTS?\b",
    r"\bINTERNSHIPS?\b",
    r"\bVOLUNTEER\s+EXPERIENCE\b",
    r"\bVOLUNTEERING\b",
    r"\bLANGUAGES\b",
    r"\bINTERESTS\b",
    r"\bACTIVITIES\b",
    r"\bDECLARATION\b",
    r"\bREFERENCES\b",
]

EDU_REGEX = re.compile("|".join(EDUCATION_HEADINGS), re.IGNORECASE)
BOUNDARY_REGEX = re.compile("|".join(BOUNDARY_HEADINGS), re.IGNORECASE)


def detect_education_section(text: str) -> Tuple[Optional[str], bool]:
    """
    Detects and extracts the education section from cleaned resume text.
    Returns (section_text, is_explicit_section).
    """
    if not text or not text.strip():
        return None, False

    lines = text.split("\n")
    start_idx = None

    # 1. Search for explicit section heading line
    for i, line in enumerate(lines):
        clean_line = line.strip().strip(":=-_#*• ")
        if clean_line and EDU_REGEX.fullmatch(clean_line):
            start_idx = i + 1
            break
        # Also check short lines (<= 35 chars) starting with education keyword
        if clean_line and len(clean_line) <= 35 and EDU_REGEX.search(clean_line):
            words = clean_line.split()
            if len(words) <= 4:
                start_idx = i + 1
                break

    if start_idx is None:
        # No explicit section heading found; return full text for heuristic fallback
        return text, False

    # 2. Find end boundary of education section
    end_idx = len(lines)
    for j in range(start_idx, len(lines)):
        clean_line = lines[j].strip().strip(":=-_#*• ")
        if not clean_line:
            continue
        # Check if line is a major boundary heading
        if BOUNDARY_REGEX.fullmatch(clean_line) or (
            len(clean_line) <= 35 and BOUNDARY_REGEX.search(clean_line) and len(clean_line.split()) <= 4
        ):
            end_idx = j
            break

    section_lines = lines[start_idx:end_idx]
    section_text = "\n".join(section_lines).strip()
    return section_text, True
