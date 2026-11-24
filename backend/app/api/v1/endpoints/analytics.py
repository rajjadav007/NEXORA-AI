"""
Resume Analytics Dashboard & Skill Distribution API Endpoints
Phase 5 | Feature 28: Resume Analytics Dashboard
Phase 5 | Feature 29: Skill Distribution
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.analytics import ResumeAnalyticsDashboardResponse
from app.schemas.skill_distribution import SkillDistributionResponse
from app.services.analytics.service import analytics_service
from app.services.analytics.skill_distribution import skill_distribution_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{resume_id}/analytics/dashboard",
    response_model=ResumeAnalyticsDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Resume Analytics Dashboard",
    description="Aggregates and returns multi-feature resume analytics, score cards, visualizations, and insights from existing Phase 4 analyses.",
)
@router.get(
    "/{resume_id}/analytics",
    response_model=ResumeAnalyticsDashboardResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_resume_analytics_dashboard(
    resume_id: str,
    user_id: Optional[str] = Query(None, description="Optional authenticated user ID query param"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Optional authenticated user ID header"),
    db: Session = Depends(get_db),
) -> ResumeAnalyticsDashboardResponse:
    """
    Retrieves aggregated visual insights and analytics for an uploaded resume.
    Enforces authorization and returns genuine metrics without fake data.
    """
    # 1. Enforce ownership and existence check
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        # 2. Retrieve aggregated analytics
        data = analytics_service.get_dashboard_analytics(
            resume_id=resume_id,
            db=db,
            user_id=user_id or x_user_id,
        )

        return ResumeAnalyticsDashboardResponse(
            success=True,
            message="Resume analytics dashboard retrieved successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Error retrieving analytics dashboard for resume %s: %s", resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resume analytics: {str(exc)}",
        )


@router.get(
    "/{resume_id}/analytics/skills",
    response_model=SkillDistributionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Resume Skill Distribution Analytics",
    description="Extracts, groups, and returns candidate skill distribution across 8 canonical categories for Feature #29.",
)
async def get_resume_skill_distribution(
    resume_id: str,
    user_id: Optional[str] = Query(None, description="Optional authenticated user ID query param"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Optional authenticated user ID header"),
    db: Session = Depends(get_db),
) -> SkillDistributionResponse:
    """
    Retrieves categorized skill distribution metrics for an uploaded resume.
    Enforces authorization, groups into 8 canonical categories, and prevents duplicates.
    """
    # 1. Enforce ownership and existence check
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await skill_distribution_service.get_resume_skill_distribution(
            resume_id=resume_id,
            db=db,
            user_id=user_id or x_user_id,
        )

        return SkillDistributionResponse(
            success=True,
            message="Resume skill distribution retrieved successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Error retrieving skill distribution for resume %s: %s", resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resume skill distribution: {str(exc)}",
        )
