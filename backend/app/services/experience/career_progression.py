"""
Career Progression Analysis for Experience Engine
Phase 3 | Feature 15: Experience Analysis
Builds chronological career progression, classifies role transitions, and produces factual observations.
"""

from typing import List, Dict, Any, Tuple
from app.services.experience.date_duration_calculator import (
    parse_date_to_parts,
    date_to_absolute_month,
    calculate_career_gaps,
)


SENIORITY_HIERARCHY = {
    "intern": 1,
    "trainee": 1,
    "apprentice": 1,
    "junior": 2,
    "associate": 2,
    "engineer": 3,
    "developer": 3,
    "analyst": 3,
    "specialist": 3,
    "consultant": 3,
    "mid-level": 3,
    "senior": 4,
    "sr": 4,
    "lead": 5,
    "staff": 5,
    "principal": 6,
    "manager": 6,
    "director": 7,
    "head": 7,
    "vp": 8,
    "chief": 9,
    "cto": 9,
    "ceo": 9,
}


def infer_seniority_level(job_title: str) -> int:
    """Infers seniority tier if explicitly indicated in title."""
    if not job_title:
        return 3
    lower = job_title.lower()
    for token, rank in SENIORITY_HIERARCHY.items():
        if token in lower.split():
            return rank
    return 3


def analyze_career_progression(
    experiences: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyzes chronological movement across positions, title promotions, and transitions.
    Returns:
        {
            "timeline": List[Dict],
            "gaps": List[Dict],
            "observations": List[str],
        }
    """
    if not experiences:
        return {
            "timeline": [],
            "gaps": [],
            "observations": ["No professional experience records found."],
        }

    # Sort experiences chronologically by start date
    def get_sort_key(exp):
        s_date = exp.get("start_date")
        y, m = parse_date_to_parts(s_date)
        if y is None:
            return 0
        return date_to_absolute_month(y, m or 1)

    sorted_roles = sorted(experiences, key=get_sort_key)

    timeline = []
    observations = []

    companies_seen = set()
    total_roles = len(sorted_roles)

    for i, role in enumerate(sorted_roles):
        company = role.get("company")
        title = role.get("job_title")
        emp_type = role.get("employment_type", "full_time")
        duration = role.get("duration_months")

        if company:
            companies_seen.add(company.lower())

        is_promotion = False
        transition_type = "initial" if i == 0 else "lateral"

        if i > 0:
            prev_role = sorted_roles[i - 1]
            prev_comp = prev_role.get("company", "").lower()
            curr_comp = (company or "").lower()

            # Same company title progression
            if prev_comp and curr_comp and prev_comp == curr_comp:
                curr_rank = infer_seniority_level(title or "")
                prev_rank = infer_seniority_level(prev_role.get("job_title") or "")
                if curr_rank > prev_rank or (prev_role.get("employment_type") == "internship" and emp_type == "full_time"):
                    is_promotion = True
                    transition_type = "promotion"
                else:
                    transition_type = "internal_transfer"
            else:
                transition_type = "new_company"

        timeline.append({
            "company": company,
            "job_title": title,
            "employment_type": emp_type,
            "start_date": role.get("start_date"),
            "end_date": role.get("end_date"),
            "duration_months": duration,
            "is_promotion": is_promotion,
            "transition_type": transition_type,
        })

    # Generate factual observations
    if total_roles == 1:
        single_role = sorted_roles[0]
        observations.append(
            f"Candidate has 1 professional role as {single_role.get('job_title') or 'Professional'} at {single_role.get('company') or 'Organization'}."
        )
    else:
        observations.append(
            f"Candidate has held {total_roles} professional roles across {len(companies_seen)} distinct organization(s)."
        )

        # Check for promotions
        promotions = [t for t in timeline if t.get("is_promotion")]
        for p in promotions:
            observations.append(
                f"Observed internal progression to {p.get('job_title')} at {p.get('company')}."
            )

    # Detect gaps
    gaps = calculate_career_gaps(sorted_roles)
    if gaps:
        for gap in gaps:
            observations.append(
                f"Career gap of {gap['duration_months']} months between {gap.get('preceding_company', 'previous role')} and {gap.get('succeeding_company', 'next role')}."
            )
    else:
        if total_roles > 1:
            observations.append("Continuous professional employment observed with no significant career gaps.")

    return {
        "timeline": timeline,
        "gaps": gaps,
        "observations": observations,
    }
