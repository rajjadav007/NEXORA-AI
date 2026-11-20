"""
Evidence-Based Confidence Scorer for Experience Analysis
Phase 3 | Feature 15: Experience Analysis
Calculates objective confidence metrics based on evidence completeness.
"""

from typing import Dict, Any


def compute_experience_confidence(
    entry: Dict[str, Any],
    is_explicit_section: bool = True,
) -> float:
    """
    Computes a deterministic, evidence-based extraction confidence score [0.0 - 1.0].
    Weights:
    - Company name present: +0.25
    - Job title present: +0.25
    - Valid start date: +0.15
    - Valid end date or verified current employment: +0.10
    - Responsibilities / contributions: +0.10
    - Identified technologies / measurable achievements: +0.05
    - Explicit section heading: +0.10
    """
    score = 0.0

    if entry.get("company"):
        score += 0.25

    if entry.get("job_title"):
        score += 0.25

    if entry.get("start_date"):
        score += 0.15

    if entry.get("end_date") or entry.get("is_current"):
        score += 0.10

    if entry.get("responsibilities") or entry.get("technical_contributions"):
        score += 0.10

    if entry.get("technologies") or entry.get("achievements"):
        score += 0.05

    if is_explicit_section:
        score += 0.10

    return round(min(1.0, score), 2)
