"""
Evidence-Based Confidence Scorer for Education
Phase 3 | Feature 14: Education Analysis
Derives calibrated confidence scores from structural evidence.
"""

from typing import Dict, Any, List


def compute_education_confidence(
    entry: Dict[str, Any],
    is_explicit_section: bool = True,
) -> float:
    """
    Computes evidence-based confidence score (0.0 to 1.0) for an education entry.
    """
    has_degree = bool(entry.get("degree"))
    has_institution = bool(entry.get("institution"))
    has_dates = bool(entry.get("start_date") or entry.get("end_date"))
    has_grade = bool(entry.get("grade"))

    if not has_degree and not has_institution:
        return 0.0

    score = 0.0

    if has_degree and has_institution:
        score = 0.92 if is_explicit_section else 0.85
    elif has_degree:
        score = 0.75 if is_explicit_section else 0.65
    elif has_institution:
        score = 0.70 if is_explicit_section else 0.60

    if has_dates:
        score += 0.03
    if has_grade:
        score += 0.03

    return round(min(score, 0.98), 2)


compute_education_entry_confidence = compute_education_confidence


def compute_batch_confidence(entries: List[Dict[str, Any]]) -> float:
    """Computes aggregate confidence for a list of entries."""
    if not entries:
        return 0.0
    scores = [compute_education_confidence(e) for e in entries]
    return round(sum(scores) / len(scores), 2)
