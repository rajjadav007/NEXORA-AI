"""
Resume-to-Job Matching Service Package
Phase 7 | Feature 39: Resume-to-Job Matching Engine
"""

from app.services.job_matching.service import (
    CALCULATION_VERSION,
    CATEGORY_WEIGHTS,
    MatchPrerequisiteError,
    job_matching_service,
)

__all__ = [
    "CALCULATION_VERSION",
    "CATEGORY_WEIGHTS",
    "MatchPrerequisiteError",
    "job_matching_service",
]
