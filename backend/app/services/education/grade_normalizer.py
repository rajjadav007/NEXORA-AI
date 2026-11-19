"""
Grade Normalizer and Scale Preserver
Phase 3 | Feature 14: Education Analysis
Parses and standardizes academic grades without speculative conversion.
"""

import re
from typing import Optional, Dict, Any

# Regex patterns for grades
CGPA_REGEX = re.compile(
    r"\b(?:cgpa|c\.g\.p\.a\.?)\b[:\s]*([0-9]{1,2}(?:\.[0-9]{1,3})?)\s*(?:/\s*([0-9]{1,2}(?:\.0)?))?",
    re.IGNORECASE,
)

GPA_REGEX = re.compile(
    r"\b(?:gpa|g\.p\.a\.?)\b[:\s]*([0-4](?:\.[0-9]{1,3})?)\s*(?:/\s*([0-4](?:\.0)?))?",
    re.IGNORECASE,
)

GENERIC_SCALE_REGEX = re.compile(
    r"\b([0-9]{1,2}(?:\.[0-9]{1,3})?)\s*/\s*([0-9]{1,2}(?:\.0)?)\b",
)

PERCENTAGE_REGEX = re.compile(
    r"\b(?:percentage|aggregate|marks)?[:\s]*([0-9]{1,2}(?:\.[0-9]{1,2})?|100)\s*%",
    re.IGNORECASE,
)

CLASSIFICATION_PATTERNS = [
    r"\bfirst\s+class\s+with\s+distinction\b",
    r"\bfirst\s+class\b",
    r"\bsecond\s+class\b",
    r"\bdistinction\b",
    r"\bsumma\s+cum\s+laude\b",
    r"\bmagna\s+cum\s+laude\b",
    r"\bcum\s+laude\b",
    r"\bdean['’]s\s+list\b",
]


def extract_and_normalize_grade(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts and structures academic grade from text.
    Preserves exact scale and original value without automatic conversion.
    """
    if not text or not text.strip():
        return None

    # 1. Check explicit CGPA pattern
    cgpa_match = CGPA_REGEX.search(text)
    if cgpa_match:
        val_str = cgpa_match.group(1)
        scale_str = cgpa_match.group(2)
        val = float(val_str)
        scale = float(scale_str) if scale_str else 10.0
        if val > scale:
            return None  # Invalid grade
        raw = cgpa_match.group(0).strip()
        return {
            "value": val,
            "type": "cgpa",
            "scale": scale,
            "raw_grade": raw,
        }

    # 2. Check explicit GPA pattern
    gpa_match = GPA_REGEX.search(text)
    if gpa_match:
        val_str = gpa_match.group(1)
        scale_str = gpa_match.group(2)
        val = float(val_str)
        scale = float(scale_str) if scale_str else 4.0
        if val > scale:
            return None
        raw = gpa_match.group(0).strip()
        return {
            "value": val,
            "type": "gpa",
            "scale": scale,
            "raw_grade": raw,
        }

    # 3. Check explicit Percentage pattern
    pct_match = PERCENTAGE_REGEX.search(text)
    if pct_match:
        val_str = pct_match.group(1)
        val = float(val_str)
        if val > 100.0:
            return None
        raw = pct_match.group(0).strip()
        return {
            "value": val,
            "type": "percentage",
            "scale": 100.0,
            "raw_grade": raw,
        }

    # 4. Check generic fraction format e.g. 7.47/10 or 3.8/4.0
    scale_match = GENERIC_SCALE_REGEX.search(text)
    if scale_match:
        val_str = scale_match.group(1)
        scale_str = scale_match.group(2)
        val = float(val_str)
        scale = float(scale_str)
        # Verify valid scale
        if scale in (4.0, 5.0, 10.0, 100.0) and val <= scale:
            grade_type = "cgpa" if scale in (10.0, 5.0) else "gpa" if scale == 4.0 else "percentage"
            return {
                "value": val,
                "type": grade_type,
                "scale": scale,
                "raw_grade": scale_match.group(0).strip(),
            }

    # 5. Check academic classification / honors
    for pattern in CLASSIFICATION_PATTERNS:
        class_match = re.search(pattern, text, re.IGNORECASE)
        if class_match:
            raw = class_match.group(0).title()
            return {
                "value": None,
                "type": "classification",
                "scale": None,
                "raw_grade": raw,
                "raw": raw,
            }

    return None


normalize_grade = extract_and_normalize_grade


def format_grade_display(grade: Optional[Dict[str, Any]]) -> str:
    """Formats structured grade into standard human display string."""
    if not grade:
        return ""
    g_type = str(grade.get("type", "")).lower()
    val = grade.get("value")
    scale = grade.get("scale")
    raw = grade.get("raw_grade") or grade.get("raw")

    if g_type == "classification":
        return raw or ""
    if g_type == "percentage" and val is not None:
        v_str = f"{int(val)}" if val == int(val) else f"{val}"
        return f"{v_str}%"
    if val is not None and scale is not None:
        return f"{val} / {scale} {g_type.upper()}"
    return raw or ""
