"""
Evidence-Based Confidence Scorer
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Calculates evidence-backed structural confidence scores between 0.0 and 1.0.
Does not rely on LLM self-reported scores.
"""

from typing import Dict, Any


def compute_certification_confidence(cert: Dict[str, Any]) -> float:
    """
    Computes evidence-based confidence for a certification record:
    - Clear title: +0.30
    - Recognized issuer: +0.25
    - Credential ID or URL: +0.20
    - Issue / expiry date: +0.15
    - Linked skills or source evidence: +0.10
    """
    score = 0.0

    title = cert.get("certification_name") or ""
    if len(title) >= 3 and title.lower() != "unknown certification":
        score += 0.30

    issuer = cert.get("issuing_organization")
    if issuer and len(issuer) >= 2:
        score += 0.25

    if cert.get("credential_id") or cert.get("credential_url"):
        score += 0.20

    if cert.get("issue_date") or cert.get("expiry_date"):
        score += 0.15

    skills = cert.get("related_skills") or []
    evidence = cert.get("source_evidence") or []
    if len(skills) > 0 or len(evidence) >= 2:
        score += 0.10

    return round(min(score, 1.0), 2)


def compute_achievement_confidence(achieve: Dict[str, Any]) -> float:
    """
    Computes evidence-based confidence for an achievement record:
    - Clear title: +0.30
    - Recognized event or organizer: +0.20
    - Explicit rank / position: +0.20
    - Date: +0.10
    - Description / role: +0.10
    - Project link or supporting URL: +0.10
    """
    score = 0.0

    title = achieve.get("achievement_title") or ""
    if len(title) >= 3 and title.lower() != "unknown achievement":
        score += 0.30

    if achieve.get("event_name") or achieve.get("organization"):
        score += 0.20

    if achieve.get("rank_or_position"):
        score += 0.20

    if achieve.get("achievement_date"):
        score += 0.10

    if achieve.get("description") or achieve.get("candidate_role"):
        score += 0.10

    if achieve.get("related_project_id") or achieve.get("achievement_url"):
        score += 0.10

    return round(min(score, 1.0), 2)
