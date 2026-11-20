"""
Experience Section Detector
Phase 3 | Feature 15: Experience Analysis
Identifies and segments the professional experience section from cleaned resume text.
"""

import re
from typing import Tuple, List

# Section header patterns indicating experience
EXPERIENCE_HEADER_PATTERNS = [
    r"(?i)^(?:professional\s+experience|work\s+experience|employment\s+history|work\s+history|professional\s+background|career\s+history|relevant\s+experience|experience|internships|internship\s+experience)(?:\s*[:\-])?$",
    r"(?i)^[#*_\s]*(?:professional\s+experience|work\s+experience|employment\s+history|work\s+history|professional\s+background|career\s+history|relevant\s+experience|experience|internships|internship\s+experience)[#*_\s]*$",
]

# Next section headers that mark the end of experience
TERMINATING_SECTION_PATTERNS = [
    r"(?i)^[#*_\s]*(?:education|academic\s+qualifications|academic\s+background|educational\s+qualifications)[#*_\s]*$",
    r"(?i)^[#*_\s]*(?:projects|academic\s+projects|personal\s+projects|key\s+projects|notable\s+projects)[#*_\s]*$",
    r"(?i)^[#*_\s]*(?:skills|technical\s+skills|core\s+competencies|technologies|tools\s+and\s+technologies)[#*_\s]*$",
    r"(?i)^[#*_\s]*(?:certifications|certificates|licenses|courses)[#*_\s]*$",
    r"(?i)^[#*_\s]*(?:publications|papers|patents)[#*_\s]*$",
    r"(?i)^[#*_\s]*(?:awards|honors|achievements|honors\s+and\s+awards)[#*_\s]*$",
    r"(?i)^[#*_\s]*(?:volunteer\s+work|volunteering|extracurricular\s+activities|activities)[#*_\s]*$",
    r"(?i)^[#*_\s]*(?:languages|spoken\s+languages)[#*_\s]*$",
    r"(?i)^[#*_\s]*(?:interests|hobbies)[#*_\s]*$",
    r"(?i)^[#*_\s]*(?:references|declarations)[#*_\s]*$",
]


def detect_experience_section(cleaned_text: str) -> Tuple[str, bool]:
    """
    Locates the experience section in the resume text.
    Returns:
        (extracted_section_text, is_explicit_section)
    """
    if not cleaned_text or not cleaned_text.strip():
        return "", False

    lines = cleaned_text.splitlines()
    start_idx = -1
    is_explicit = False

    # 1. Search for explicit experience header
    for idx, line in enumerate(lines):
        clean_line = line.strip()
        if not clean_line:
            continue
        for pattern in EXPERIENCE_HEADER_PATTERNS:
            if re.match(pattern, clean_line):
                start_idx = idx + 1
                is_explicit = True
                break
        if start_idx != -1:
            break

    if start_idx == -1:
        # Fallback: check if line is simply 'EXPERIENCE' in all caps or standalone
        for idx, line in enumerate(lines):
            clean_line = line.strip()
            if clean_line.upper() in ["EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE", "EMPLOYMENT"]:
                start_idx = idx + 1
                is_explicit = True
                break

    if start_idx == -1:
        return "", False

    # 2. Search for terminating header
    end_idx = len(lines)
    for idx in range(start_idx, len(lines)):
        clean_line = lines[idx].strip()
        if not clean_line:
            continue
        for term_pat in TERMINATING_SECTION_PATTERNS:
            if re.match(term_pat, clean_line):
                end_idx = idx
                break
        if end_idx != len(lines):
            break

    section_lines = lines[start_idx:end_idx]
    section_text = "\n".join(section_lines).strip()
    return section_text, is_explicit
