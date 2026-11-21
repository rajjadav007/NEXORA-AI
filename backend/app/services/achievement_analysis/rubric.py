"""
Achievement Quality Scoring Rubric Engine
Phase 4 | Feature 26: Achievement Analysis
Transparent 5-component scoring rubric summing to 100 points.
"""

from typing import List, Dict, Any, Tuple
from app.schemas.achievement_analysis import RubricBreakdown


def calculate_achievement_rubric(
    achievements: List[Any],
    category_keys: List[str],
) -> Tuple[int, str, RubricBreakdown]:
    """
    Computes transparent rubric score out of 100:
    1. Quantification Rate Score (Max 35 pts)
    2. Impact Magnitude Score (Max 25 pts)
    3. Cross-Category Diversity Score (Max 15 pts)
    4. Action Clarity Score (Max 15 pts)
    5. Metric Verification Fidelity Score (Max 10 pts)
    """
    total = len(achievements)
    if total == 0:
        breakdown = RubricBreakdown(
            quantification_rate_score=0.0,
            impact_magnitude_score=0.0,
            cross_category_diversity_score=0.0,
            action_clarity_score=0.0,
            metric_verification_fidelity_score=0.0,
            total_score=20,
        )
        return 20, "Needs Quantification", breakdown

    quantified_count = sum(1 for a in achievements if getattr(a, "is_quantified", False))
    high_impact_count = sum(1 for a in achievements if getattr(a, "impact_level", "Medium") == "High")
    med_impact_count = sum(1 for a in achievements if getattr(a, "impact_level", "Medium") == "Medium")
    strong_quality_count = sum(1 for a in achievements if getattr(a, "quality_rating", "Moderate") == "Strong")
    mod_quality_count = sum(1 for a in achievements if getattr(a, "quality_rating", "Moderate") == "Moderate")
    verified_metrics_count = sum(1 for a in achievements if getattr(a, "has_verified_metrics", True))

    # 1. Quantification Rate (35 pts max)
    quant_rate = quantified_count / total
    quant_score = round(quant_rate * 35.0, 1)

    # 2. Impact Magnitude (25 pts max)
    impact_score = min(25.0, round((high_impact_count * 8.0) + (med_impact_count * 4.0), 1))

    # 3. Category Diversity (15 pts max)
    active_categories = len(set(category_keys))
    diversity_score = min(15.0, round(active_categories * 5.0, 1))

    # 4. Action Clarity & Strength (15 pts max)
    clarity_score = min(15.0, round((strong_quality_count * 5.0) + (mod_quality_count * 2.5), 1))

    # 5. Verification Fidelity (10 pts max)
    fidelity_rate = verified_metrics_count / total
    fidelity_score = round(fidelity_rate * 10.0, 1)

    total_pts = int(round(quant_score + impact_score + diversity_score + clarity_score + fidelity_score))
    total_score = max(20, min(100, total_pts))

    if total_score >= 85:
        grade = "Exceptional"
    elif total_score >= 70:
        grade = "Strong"
    elif total_score >= 50:
        grade = "Moderate"
    else:
        grade = "Needs Quantification"

    breakdown = RubricBreakdown(
        quantification_rate_score=quant_score,
        impact_magnitude_score=impact_score,
        cross_category_diversity_score=diversity_score,
        action_clarity_score=clarity_score,
        metric_verification_fidelity_score=fidelity_score,
        total_score=total_score,
    )

    return total_score, grade, breakdown
