"""
Section Detector and Chunker for Certifications and Achievements
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Identifies dedicated sections and parses them into individual candidate blocks.
"""

import re
from typing import List, Dict, Any, Tuple

# Section header patterns
CERTIFICATION_HEADERS = [
    r"(?:licenses\s*(?:&|and)\s*certifications?)",
    r"(?:professional\s*certifications?)",
    r"(?:technical\s*certifications?)",
    r"(?:certifications?\s*(?:&|and)\s*licenses?)",
    r"(?:certifications?\s*(?:&|and)\s*courses?)",
    r"(?:certifications?\s*(?:&|and)\s*credentials?)",
    r"(?:certifications?)",
    r"(?:certificates?)",
    r"(?:credentials?)",
    r"(?:online\s*courses?)",
    r"(?:courses?\s*(?:&|and)\s*trainings?)",
    r"(?:professional\s*development)",
    r"(?:training\s*(?:&|and)\s*certifications?)",
]

ACHIEVEMENT_HEADERS = [
    r"(?:honors?\s*(?:&|and)\s*awards?)",
    r"(?:awards?\s*(?:&|and)\s*honors?)",
    r"(?:awards?\s*(?:&|and)\s*achievements?)",
    r"(?:achievements?\s*(?:&|and)\s*awards?)",
    r"(?:achievements?)",
    r"(?:awards?)",
    r"(?:honors?)",
    r"(?:hackathons?\s*(?:&|and)\s*competitions?)",
    r"(?:hackathons?)",
    r"(?:competitions?)",
    r"(?:contests?)",
    r"(?:research\s*publications?)",
    r"(?:publications?)",
    r"(?:papers?\s*(?:&|and)\s*publications?)",
    r"(?:scholarships?)",
    r"(?:leadership\s*(?:&|and)\s*(?:awards?|activities))",
    r"(?:extracurricular\s*(?:activities|achievements)?)",
    r"(?:accomplishments?)",
]

CERT_REGEX = re.compile(
    r"^(?:[\s\W]*)(?:" + "|".join(CERTIFICATION_HEADERS) + r")(?:[\s\W]*)$",
    re.IGNORECASE | re.MULTILINE,
)

ACHIEVE_REGEX = re.compile(
    r"^(?:[\s\W]*)(?:" + "|".join(ACHIEVEMENT_HEADERS) + r")(?:[\s\W]*)$",
    re.IGNORECASE | re.MULTILINE,
)

GENERIC_SECTION_BREAK = re.compile(
    r"^(?:[A-Z\s/&]{3,40}|#{1,4}\s+[A-Za-z\s/&]+)[:]?\s*$",
    re.MULTILINE,
)


def extract_certification_and_achievement_sections(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scans cleaned resume text to isolate certification sections and achievement sections.
    Returns:
    {
        "certifications": [{"section_name": str, "text": str}],
        "achievements": [{"section_name": str, "text": str}]
    }
    """
    if not text or not text.strip():
        return {"certifications": [], "achievements": []}

    lines = text.split("\n")
    n = len(lines)

    header_indices: List[Tuple[int, str, str]] = []  # (line_idx, header_text, section_type)

    for idx, line in enumerate(lines):
        clean_line = line.strip().strip("#*-_: ")
        if not clean_line or len(clean_line) > 55:
            continue

        if CERT_REGEX.match(clean_line):
            header_indices.append((idx, clean_line, "certifications"))
        elif ACHIEVE_REGEX.match(clean_line):
            header_indices.append((idx, clean_line, "achievements"))
        elif GENERIC_SECTION_BREAK.match(clean_line) and clean_line.isupper() and len(clean_line) >= 4:
            # Check if this is a boundary break
            header_indices.append((idx, clean_line, "other"))

    cert_sections: List[Dict[str, Any]] = []
    achieve_sections: List[Dict[str, Any]] = []

    for i, (idx, htext, stype) in enumerate(header_indices):
        if stype not in ("certifications", "achievements"):
            continue

        # Section body runs until next header index or end of document
        end_idx = n
        if i + 1 < len(header_indices):
            end_idx = header_indices[i + 1][0]

        section_body = "\n".join(lines[idx + 1:end_idx]).strip()
        if not section_body:
            continue

        entry = {"section_name": htext, "text": section_body}
        if stype == "certifications":
            cert_sections.append(entry)
        else:
            achieve_sections.append(entry)

    return {
        "certifications": cert_sections,
        "achievements": achieve_sections,
    }


def split_section_into_blocks(section_text: str) -> List[str]:
    """
    Splits a section into distinct item blocks based on bullet points,
    double line breaks, or numbered lines.
    """
    if not section_text or not section_text.strip():
        return []

    lines = section_text.split("\n")
    blocks: List[str] = []
    curr: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if curr:
                blocks.append("\n".join(curr).strip())
                curr = []
            continue

        # Check if line begins a new item (bullet, number, or markdown bold header)
        is_new_bullet = bool(re.match(r"^(\*|\-|\u2022|\u25cf|\u25cb|\d+[\.\)])\s+", stripped))
        is_bold_title = bool(re.match(r"^\*\*[^*]+\*\*", stripped))

        if (is_new_bullet or is_bold_title) and curr:
            blocks.append("\n".join(curr).strip())
            curr = [stripped]
        else:
            curr.append(stripped)

    if curr:
        blocks.append("\n".join(curr).strip())

    # Filter out empty or whitespace blocks
    return [b for b in blocks if len(b) > 4]
