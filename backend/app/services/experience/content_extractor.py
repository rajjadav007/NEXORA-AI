"""
Content Extractor for Experience Analysis
Phase 3 | Feature 15: Experience Analysis
Extracts responsibilities, technical contributions, achievements, and quantified measurable impacts.
"""

import re
from typing import List, Tuple, Dict, Any

# Regex patterns extracting specific quantifiable metric values
METRIC_EXTRACTION_PATTERNS = [
    r"\b\d+(?:\.\d+)?%",  # percentages e.g. 35%, 12.5%
    r"\b\d+x\b",  # multipliers e.g. 2x, 5x
    r"\$\s*\d+(?:[.,]\d+)?\s*(?:k|m|b|million|billion|thousand)?\b",  # financial e.g. $50k
    r"\b\d+\s*(?:ms|seconds|minutes|hours|days|weeks)\b",  # time/latency e.g. 300ms, 2 seconds
    r"\b\d+(?:,\d+)*(?:\+)?\s+(?:users|requests|queries|clients|customers|records|transactions|lines\s+of\s+code)(?:/(?:sec|min|hour|day))?\b",
]

# Patterns detecting sentences containing quantifiable results
QUANTIFIABLE_PATTERNS = METRIC_EXTRACTION_PATTERNS + [
    r"\b(?:reduced|increased|improved|decreased|accelerated|boosted|saved|scaled)\s+[a-zA-Z\s]{1,30}?\b(?:by\s+)?(?:\d+(?:\.\d+)?%|\d+x|\$\d+|\d+)",
]

# Keywords indicating technical development/architectural contributions
TECHNICAL_INDICATORS = [
    r"\b(?:built|developed|implemented|architected|engineered|designed|coded|programmed|integrated|deployed|refactored|optimized|configured|containerized|automated|migrated|trained|fine-tuned|modeled)\b",
    r"\b(?:api|apis|pipeline|pipelines|backend|frontend|microservice|database|sql|nosql|docker|kubernetes|llm|ml|ai|model|models|etl|algorithm|rest|graphql)\b",
]

# Keywords indicating achievements
ACHIEVEMENT_INDICATORS = [
    r"\b(?:awarded|awarded\s+as|won|achieved|honored|recognized|promoted|published|patent|first\s+place|top\s+performer|dean's\s+list|star\s+award)\b",
    r"\b(?:reduced|increased|improved|decreased|accelerated|boosted|saved|scaled|maximized|minimized)\b",
]


def is_measurable_impact(text: str) -> bool:
    """Checks whether a sentence or bullet contains quantified measurable results."""
    for pat in QUANTIFIABLE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def is_technical_contribution(text: str) -> bool:
    """Checks whether a sentence or bullet represents technical software/AI contributions."""
    for pat in TECHNICAL_INDICATORS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def is_achievement_bullet(text: str) -> bool:
    """Checks whether a statement represents an achievement or award."""
    # If it has measurable quantified impact, it's an achievement
    if is_measurable_impact(text):
        return True
    for pat in ACHIEVEMENT_INDICATORS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def extract_measurable_metrics(text: str) -> List[str]:
    """Extracts the exact quantified metrics mentioned in the text."""
    metrics = []
    for pat in METRIC_EXTRACTION_PATTERNS:
        matches = re.finditer(pat, text, re.IGNORECASE)
        for m in matches:
            metric_str = m.group(0).strip()
            if metric_str and metric_str not in metrics:
                metrics.append(metric_str)
    return metrics


def categorize_experience_bullets(
    bullets: List[str]
) -> Dict[str, List[str]]:
    """
    Categorizes raw experience bullet points into:
    - responsibilities
    - technical_contributions
    - achievements
    - measurable_impact
    Does not fabricate missing fields.
    """
    responsibilities = []
    technical_contributions = []
    achievements = []
    measurable_impact = []

    seen = set()

    for raw_bullet in bullets:
        clean = re.sub(r"^[\s\-_•*–—\d.)]+", "", raw_bullet).strip()
        if not clean or len(clean) < 5 or clean.lower() in seen:
            continue
        seen.add(clean.lower())

        # Check for measurable impact
        metrics = extract_measurable_metrics(clean)
        if metrics:
            measurable_impact.extend(metrics)

        # Check for achievement
        if is_achievement_bullet(clean):
            achievements.append(clean)
        elif is_technical_contribution(clean):
            technical_contributions.append(clean)
        else:
            responsibilities.append(clean)

    # If technical_contributions or responsibilities are empty, preserve factual bullet
    if not responsibilities and technical_contributions:
        # Clone primary technical bullets into responsibilities if responsibilities list is empty
        responsibilities = list(technical_contributions)
    elif not technical_contributions and responsibilities:
        # Check if any responsibilities qualify as technical
        tech_matched = [r for r in responsibilities if is_technical_contribution(r)]
        if tech_matched:
            technical_contributions = tech_matched

    # Deduplicate metrics
    unique_metrics = []
    for m in measurable_impact:
        if m not in unique_metrics:
            unique_metrics.append(m)

    return {
        "responsibilities": responsibilities,
        "technical_contributions": technical_contributions,
        "achievements": achievements,
        "measurable_impact": unique_metrics,
    }
