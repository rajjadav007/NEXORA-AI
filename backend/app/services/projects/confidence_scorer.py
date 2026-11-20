"""
Project Confidence Scorer
Phase 3 | Feature 18: Project Intelligence
Calculates an evidence-backed confidence score between 0.0 and 1.0.
Does not rely on LLM self-reported confidence.
"""

from typing import Dict, Any


def compute_project_confidence(project: Dict[str, Any]) -> float:
    """
    Computes an evidence-based confidence score based on structural indicators:
    - Title clarity: +0.25
    - Description depth: +0.25
    - Explicit technologies: +0.20
    - Links (GitHub/live demo): +0.15
    - Dates / timeline: +0.10
    - Measurable outcomes or achievements: +0.05
    """
    score = 0.0

    # Title clarity
    title = project.get("normalized_title") or ""
    if title and title != "Untitled Project" and len(title) >= 3:
        score += 0.25

    # Description depth
    desc = project.get("detailed_description") or project.get("short_description") or ""
    if len(desc) >= 60:
        score += 0.25
    elif len(desc) >= 20:
        score += 0.15

    # Technologies
    techs = project.get("technologies") or []
    if len(techs) >= 2:
        score += 0.20
    elif len(techs) == 1:
        score += 0.10

    # Project Links
    links = project.get("project_links") or []
    if len(links) > 0:
        score += 0.15

    # Dates
    if project.get("start_date"):
        score += 0.10

    # Measurable outcomes or achievements
    outcomes = project.get("measurable_outcomes") or project.get("achievements") or []
    if len(outcomes) > 0:
        score += 0.05

    return round(min(score, 1.0), 2)
