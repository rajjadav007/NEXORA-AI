"""
Project Section Detector and Chunker
Phase 3 | Feature 18: Project Intelligence
Locates project sections and segments resume text into distinct individual project blocks.
"""

import re
from typing import List, Dict, Any, Optional

PROJECT_HEADERS = [
    r"(?:academic\s+projects|technical\s+projects|personal\s+projects|key\s+projects)",
    r"(?:hackathon\s+projects|open\s+source\s+contributions|research\s+projects)",
    r"(?:selected\s+projects|featured\s+projects|projects\s*(?:&|and)\s*initiatives)",
    r"(?:projects|project\s+experience)",
]

OTHER_SECTION_HEADERS = [
    r"(?:experience|work\s+experience|professional\s+experience|employment)",
    r"(?:education|academic\s+background|qualifications)",
    r"(?:technical\s+skills|skills|core\s+competencies|technologies)",
    r"(?:certifications|certificates|licenses|awards|honors)",
    r"(?:publications|patents|references|volunteer\s+experience)",
]


def extract_project_sections(resume_text: str) -> List[Dict[str, Any]]:
    """
    Identifies sections dedicated to projects.
    Returns list of dicts: {'section_name': str, 'text': str, 'start_line': int}
    """
    if not resume_text:
        return []

    lines = [line.strip() for line in resume_text.split("\n")]
    project_sections: List[Dict[str, Any]] = []

    in_project_section = False
    current_section_name = "Projects"
    current_lines: List[str] = []
    section_start = 0

    for idx, line in enumerate(lines):
        line_lower = line.lower().strip()
        if not line_lower:
            if in_project_section and current_lines:
                current_lines.append("")
            continue

        # Check if line matches a project header
        matched_proj = False
        for pat in PROJECT_HEADERS:
            if re.match(rf"^(?:#+\s*)?{pat}[:\s]*$", line_lower):
                if in_project_section and current_lines:
                    project_sections.append({
                        "section_name": current_section_name,
                        "text": "\n".join(current_lines).strip(),
                        "start_line": section_start,
                    })
                    current_lines = []
                in_project_section = True
                current_section_name = line.strip("# :")
                section_start = idx
                matched_proj = True
                break

        if matched_proj:
            continue

        # Check if line matches an unrelated section header
        if in_project_section:
            matched_other = False
            for pat in OTHER_SECTION_HEADERS:
                if re.match(rf"^(?:#+\s*)?{pat}[:\s]*$", line_lower):
                    project_sections.append({
                        "section_name": current_section_name,
                        "text": "\n".join(current_lines).strip(),
                        "start_line": section_start,
                    })
                    current_lines = []
                    in_project_section = False
                    matched_other = True
                    break
            if matched_other:
                continue

        if in_project_section:
            current_lines.append(line)

    if in_project_section and current_lines:
        project_sections.append({
            "section_name": current_section_name,
            "text": "\n".join(current_lines).strip(),
            "start_line": section_start,
        })

    return project_sections


def split_section_into_project_blocks(section_text: str) -> List[str]:
    """
    Splits a project section into individual project text blocks.
    Identifies boundaries using blank lines, bold/markdown headings, or distinct project title cues
    (such as pipe separators, date indicators, or github links).
    """
    if not section_text or not section_text.strip():
        return []

    lines = [line.strip() for line in section_text.split("\n")]
    blocks: List[str] = []
    current_block: List[str] = []

    for line in lines:
        if not line:
            if current_block and len("\n".join(current_block)) > 40:
                # Potential boundary on double space or blank line
                # Look ahead or finalize block
                pass
            continue

        # Check if line looks like a new project title
        is_title = False

        # Pattern 1: Title with pipe, dash, or parentheses containing techs/urls
        # e.g., "AI Career Copilot | Python, React, FastAPI" or "Smart Portfolio (GitHub)"
        if re.search(r"^[A-Z0-9][\w\s\.-]{2,50}\s+[\|\–\-]\s+[A-Za-z0-9]", line) and not line.startswith("-") and not line.startswith("•"):
            is_title = True
        # Pattern 2: Markdown headers ### Project Name
        elif re.match(r"^#{1,4}\s+[A-Z0-9]", line):
            is_title = True
        # Pattern 3: Line with project name followed by GitHub link or date
        elif re.search(r"^[A-Z0-9][\w\s]{2,40}\s*\((?:https?://|github\.com|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d\d)", line):
            is_title = True
        # Pattern 4: Title line followed by bullets, where title has no bullet itself
        elif (
            not line.startswith("-")
            and not line.startswith("•")
            and not line.startswith("*")
            and not line.lower().startswith("technolog")
            and not line.lower().startswith("tools:")
            and not line.lower().startswith("role:")
            and len(line) <= 70
            and not line.endswith(".")
            and current_block
            and any(b.startswith("-") or b.startswith("•") or b.startswith("*") for b in current_block)
        ):
            is_title = True

        if is_title and current_block:
            blocks.append("\n".join(current_block).strip())
            current_block = [line]
        else:
            current_block.append(line)

    if current_block:
        blocks.append("\n".join(current_block).strip())

    return [b for b in blocks if len(b) > 20]
