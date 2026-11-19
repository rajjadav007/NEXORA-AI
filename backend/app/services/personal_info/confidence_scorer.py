"""
Evidence-Based Confidence Scorer
Phase 3 | Feature 13: Personal Information Extraction
Computes calibrated confidence metrics based on extraction source and validation rules.
"""

from typing import Dict, Any, Optional


def compute_confidence_scores(
    data: Dict[str, Any],
    source_attribution: Optional[Dict[str, str]] = None,
) -> Dict[str, float]:
    """
    Computes evidence-based confidence scores for extracted personal info fields.
    Does not rely on LLM self-evaluation; derives scores from structural evidence.
    """
    scores: Dict[str, float] = {}
    sources = source_attribution or {}

    # 1. Email confidence
    if data.get("email"):
        scores["email"] = 1.0
    else:
        scores["email"] = 0.0

    # 2. Phone confidence
    if data.get("phone"):
        scores["phone"] = 0.95
    else:
        scores["phone"] = 0.0

    # 3. Country code confidence
    if data.get("country_code"):
        scores["country_code"] = 0.95
    else:
        scores["country_code"] = 0.0

    # 4. Full name confidence
    if data.get("full_name"):
        name_source = sources.get("full_name", "heuristic")
        if name_source == "ai":
            scores["full_name"] = 0.98
        elif name_source == "user":
            scores["full_name"] = 1.0
        else:
            scores["full_name"] = 0.80
    else:
        scores["full_name"] = 0.0

    # 5. First & Last name confidence
    if data.get("first_name"):
        scores["first_name"] = scores.get("full_name", 0.80)
    else:
        scores["first_name"] = 0.0

    if data.get("last_name"):
        scores["last_name"] = scores.get("full_name", 0.80)
    else:
        scores["last_name"] = 0.0

    # 6. Location confidence
    loc = data.get("location")
    if loc and isinstance(loc, dict) and any(loc.values()):
        components = sum(1 for v in (loc.get("city"), loc.get("state"), loc.get("country")) if v)
        if components >= 2:
            scores["location"] = 0.85
        else:
            scores["location"] = 0.70
    else:
        scores["location"] = 0.0

    # 7. LinkedIn URL
    if data.get("linkedin_url"):
        scores["linkedin_url"] = 0.98
    else:
        scores["linkedin_url"] = 0.0

    # 8. GitHub URL
    if data.get("github_url"):
        scores["github_url"] = 0.98
    else:
        scores["github_url"] = 0.0

    # 9. Portfolio URL
    if data.get("portfolio_url"):
        scores["portfolio_url"] = 0.92
    else:
        scores["portfolio_url"] = 0.0

    return scores
