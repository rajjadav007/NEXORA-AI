"""
Academic Information Validation Engine
Phase 3 | Feature 14: Education Analysis
Enforces data integrity, boundary checks, and anti-hallucination rules.
"""

import re
from typing import Optional, Dict, Any, List, Tuple


def _parse_year(date_str: Any) -> Optional[int]:
    if not date_str or not isinstance(date_str, str):
        return None
    m = re.search(r"\b((?:19|20)\d{2})\b", date_str)
    return int(m.group(1)) if m else None


def validate_education_entry(entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a single education entry for required fields and logical constraints.
    Returns (is_valid, list_of_error_messages).
    """
    errors: List[str] = []
    if not entry or not isinstance(entry, dict):
        return False, ["Entry must be a non-empty dictionary."]

    degree = entry.get("degree")
    institution = entry.get("institution")

    if not degree or not str(degree).strip():
        errors.append("Degree name is required.")

    # Chronology validation: start_date <= end_date
    start_year = _parse_year(entry.get("start_date"))
    end_year = _parse_year(entry.get("end_date"))
    if start_year and end_year and start_year > end_year:
        errors.append(f"Invalid chronology: start date ({start_year}) cannot be after end date ({end_year}).")

    # Grade validation
    grade = entry.get("grade")
    if grade and isinstance(grade, dict):
        val = grade.get("value")
        scale = grade.get("scale")
        grade_type = str(grade.get("type", "")).lower()

        if val is not None and isinstance(val, (int, float)):
            if scale and val > (scale * 1.05):
                errors.append(f"Grade value ({val}) exceeds maximum scale ({scale}).")
            if grade_type == "percentage" and (val < 0 or val > 100):
                errors.append(f"Percentage ({val}) must be between 0 and 100.")

    return len(errors) == 0, errors


def validate_education_entries(entries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Validates a batch of education entries.
    Returns (valid_entries, all_errors).
    """
    valid = []
    all_errors = []
    for idx, e in enumerate(entries):
        ok, errs = validate_education_entry(e)
        if ok:
            valid.append(e)
        else:
            all_errors.extend([f"Entry #{idx + 1}: {err}" for err in errs])
    return valid, all_errors


def validate_academic_entry(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Sanitizes and validates a single candidate education record.
    Returns sanitized dictionary or None if invalid or fabricated.
    """
    if not entry or not isinstance(entry, dict):
        return None

    degree = entry.get("degree")
    institution = entry.get("institution")

    # Anti-hallucination: An entry MUST have either a degree or an institution
    if not degree and not institution:
        return None

    # Clean strings
    def _clean(val: Any) -> Optional[str]:
        if not val or not isinstance(val, str):
            return None
        s = val.strip()
        if len(s) < 2 or len(s) > 255:
            return None
        # Reject URLs or emails in degree/institution
        if "@" in s or any(s.lower().startswith(p) for p in ("http://", "https://", "www.")):
            return None
        return s

    cleaned_degree = _clean(degree)
    cleaned_institution = _clean(institution)
    cleaned_field = _clean(entry.get("field_of_study"))
    cleaned_spec = _clean(entry.get("specialization"))
    cleaned_loc = _clean(entry.get("location"))

    if not cleaned_degree and not cleaned_institution:
        return None

    # Validate grade
    grade = entry.get("grade")
    valid_grade = None
    if grade and isinstance(grade, dict):
        val = grade.get("value")
        scale = grade.get("scale")
        grade_type = grade.get("type")
        raw = grade.get("raw_grade") or grade.get("raw")

        # Sanity check: CGPA <= scale, percentage <= 100
        is_valid = True
        if val is not None and isinstance(val, (int, float)):
            if scale and val > (scale * 1.05):
                is_valid = False
            if str(grade_type).lower() == "percentage" and (val < 0 or val > 100):
                is_valid = False

        if is_valid:
            valid_grade = {
                "value": val,
                "type": grade_type,
                "scale": scale,
                "raw_grade": raw,
            }

    # Validate lists
    def _clean_list(lst: Any) -> List[str]:
        if not lst or not isinstance(lst, list):
            return []
        res = []
        for item in lst:
            if isinstance(item, str) and item.strip():
                clean_item = item.strip()
                if len(clean_item) <= 255 and clean_item not in res:
                    res.append(clean_item)
        return res

    return {
        **entry,
        "degree": cleaned_degree,
        "institution": cleaned_institution,
        "field_of_study": cleaned_field,
        "specialization": cleaned_spec,
        "location": cleaned_loc,
        "grade": valid_grade,
        "achievements": _clean_list(entry.get("achievements")),
        "coursework": _clean_list(entry.get("coursework")),
        "honors": _clean_list(entry.get("honors")),
        "source_evidence": _clean_list(entry.get("source_evidence")),
    }
