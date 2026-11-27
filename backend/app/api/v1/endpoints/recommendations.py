"""
Resume Improvement Recommendations API Endpoints
Phase 4 | Feature 27: Resume Improvement Recommendations
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.recommendations import (
    RecommendationResponse,
    UpdateRecommendationStatusRequest,
    SingleRecommendationResponse,
)
from app.services.recommendations.service import recommendation_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{resume_id}/recommendations/generate",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate personalized resume improvement recommendations",
    description="Synthesizes findings across Features #21 to #26 into prioritized, actionable recommendations across 8 categories via a 7-stage LangGraph workflow.",
)
async def generate_resume_recommendations(
    resume_id: str,
    force_recalculate: bool = Query(False, description="Whether to bypass cached recommendations and re-evaluate via LangGraph"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    """
    Coordinates multi-step recommendation workflow:
    1. Loads prior analysis results (Quality, Strengths, Weaknesses, ATS, Grammar, Achievements)
    2. Validates data coverage gracefully
    3. Combines findings into 8 target categories
    4. Generates intelligent recommendations with Ollama / Gemma (with robust fallback)
    5. Deduplicates and prioritizes (Critical, High, Medium, Low)
    6. Validates output with Pydantic
    7. Persists records in PostgreSQL
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await recommendation_service.calculate_recommendations(
            resume_id=resume_id,
            force_recalculate=force_recalculate,
            user_id=user_id or x_user_id,
            db=db,
        )
        return RecommendationResponse(
            success=True,
            message="Resume improvement recommendations generated successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Unexpected error generating recommendations for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(exc)}",
        )


@router.get(
    "/{resume_id}/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get resume improvement recommendations with filtering",
    description="Retrieves persisted recommendations with optional filters by category, priority, and completion status.",
)
def get_resume_recommendations(
    resume_id: str,
    category: Optional[str] = Query(None, description="Filter by category (e.g., technical_skills, ats_compatibility, etc.)"),
    priority: Optional[str] = Query(None, description="Filter by priority (Critical, High, Medium, Low)"),
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    optional: bool = Query(False, description="Return 200 with data=null instead of 404 when not generated"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    """Retrieves recommendations for a resume, or raises 404 if not yet generated."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    data = recommendation_service.get_recommendations(
        resume_id=resume_id,
        db=db,
        category=category,
        priority=priority,
        is_completed=is_completed,
    )

    if not data:
        if optional:
            return JSONResponse(content={"success": True, "message": "No recommendations found", "data": None})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No recommendations found for resume ID {resume_id}. Please call the /generate endpoint first.",
        )

    return RecommendationResponse(
        success=True,
        message="Resume improvement recommendations retrieved successfully",
        data=data,
    )


@router.patch(
    "/{resume_id}/recommendations/{recommendation_id}/status",
    response_model=SingleRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update completion status of a recommendation",
    description="Allows users to mark a recommendation as completed or reopen it, tracking progress in real time.",
)
def update_recommendation_status(
    resume_id: str,
    recommendation_id: str,
    payload: UpdateRecommendationStatusRequest,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SingleRecommendationResponse:
    """Updates completion status for an individual recommendation and recalculates completion percentage."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    result = recommendation_service.update_recommendation_status(
        resume_id=resume_id,
        recommendation_id=recommendation_id,
        is_completed=payload.is_completed,
        db=db,
    )

    status_str = "completed" if payload.is_completed else "reopened"
    return SingleRecommendationResponse(
        success=True,
        message=f"Recommendation '{recommendation_id}' marked as {status_str}.",
        data=result,
    )
