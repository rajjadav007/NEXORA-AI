"""
Resume Achievement Analysis API Endpoints
Phase 4 | Feature 26: Achievement Analysis
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.achievement_analysis import AchievementAnalysisResponse
from app.services.achievement_analysis.service import achievement_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{resume_id}/achievements/analyze",
    response_model=AchievementAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze resume accomplishments and measurable impact",
    description="Identifies accomplishments across experience, projects, hackathons, awards, and certifications; measures metric quantification rate and produces Google X-Y-Z improved statements.",
)
async def analyze_resume_achievements(
    resume_id: str,
    force_recalculate: bool = Query(False, description="Whether to bypass cached achievement analysis and re-evaluate with AI"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> AchievementAnalysisResponse:
    """
    Evaluates:
    - Achievements across 7 categories
    - Detection of percentages, numbers, time saved, and scale
    - Quantification rate and transparent rubric score (0-100)
    - Google X-Y-Z improved statements preserving factual accomplishments
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await achievement_analysis_service.calculate_achievement_analysis(
            resume_id=resume_id,
            force_recalculate=force_recalculate,
            db=db,
        )
        return AchievementAnalysisResponse(
            success=True,
            message="Resume achievement analysis completed successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Unexpected error analyzing achievements for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume achievements: {str(exc)}",
        )


@router.get(
    "/{resume_id}/achievements/analysis",
    response_model=AchievementAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get previously generated achievement analysis",
    description="Retrieves persisted achievement quality score, quantified vs non-quantified breakdowns, evidence, and Google X-Y-Z statements.",
)
def get_resume_achievement_analysis(
    resume_id: str,
    optional: bool = Query(False, description="Return 200 with data=null instead of 404 when not analyzed"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> AchievementAnalysisResponse:
    """Retrieves cached resume achievement analysis if present, or raises 404."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    data = achievement_analysis_service.get_achievement_analysis(resume_id=resume_id, db=db)
    if not data:
        if optional:
            return JSONResponse(content={"success": True, "message": "No achievement analysis found", "data": None})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No achievement analysis found for resume ID {resume_id}. Please call the /analyze endpoint first.",
        )

    return AchievementAnalysisResponse(
        success=True,
        message="Resume achievement analysis retrieved successfully",
        data=data,
    )


@router.get(
    "/{resume_id}/achievement-analysis",
    response_model=AchievementAnalysisResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_resume_achievement_analysis_alias(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> AchievementAnalysisResponse:
    """Alias for /{resume_id}/achievements/analysis."""
    return get_resume_achievement_analysis(resume_id=resume_id, user_id=user_id, x_user_id=x_user_id, db=db)
