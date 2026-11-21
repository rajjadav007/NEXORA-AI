"""
Resume Improvement Recommendations Service Package
Phase 4 | Feature 27: Resume Improvement Recommendations
"""

from app.services.recommendations.service import recommendation_service, RecommendationService
from app.services.recommendations.workflow import recommendation_graph
from app.services.recommendations.categories import (
    RECOMMENDATION_CATEGORIES,
    normalize_category_key,
    get_category_display_name,
)

__all__ = [
    "recommendation_service",
    "RecommendationService",
    "recommendation_graph",
    "RECOMMENDATION_CATEGORIES",
    "normalize_category_key",
    "get_category_display_name",
]
