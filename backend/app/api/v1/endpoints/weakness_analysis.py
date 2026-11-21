"""
Resume Weakness Analysis API Endpoints
Phase 4 | Feature 23: Resume Weakness Analysis
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.weakness_analysis import WeaknessAnalysisResponse
from app.services.weakness_analysis.service import weakness_analysis_service
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{resume_id}/weaknesses/analyze",
    response_model=WeaknessAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze and identify candidate weaknesses and missing information from resume",
    description="Identifies weak descriptions, statements lacking measurable impact, missing information, and prioritized improvements.",
)
async def analyze_resume_weaknesses(
    resume_id: str,
    force_recalculate: bool = Query(False, description="Whether to bypass cached weakness analysis and re-evaluate with LLM"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> WeaknessAnalysisResponse:
    """
    Evaluates candidate weaknesses across 7 categories:
    - Technical skills presentation
    - Project descriptions
    - Work and internship experience
    - Education details
    - Achievements and certifications
    - Professional summary
    - Content clarity and relevance
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await weakness_analysis_service.calculate_weakness_analysis(
            resume_id=resume_id,
            force_recalculate=force_recalculate,
            db=db,
        )
        return WeaknessAnalysisResponse(
            success=True,
            message="Resume weakness analysis completed successfully",
            data=data,
        )

    except OllamaUnavailableError as oue:
        logger.warning("Ollama unavailable for weakness analysis on resume %s: %s", resume_id, oue)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(oue),
        )

    except AIOutputValidationError as aie:
        logger.error("Weakness analysis structured validation failed for resume %s: %s", resume_id, aie)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(aie),
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Unexpected error analyzing weaknesses for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume weaknesses: {str(exc)}",
        )


@router.get(
    "/{resume_id}/weaknesses",
    response_model=WeaknessAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get previously generated resume weakness analysis",
    description="Retrieves persisted candidate weaknesses, missing information, priority breakdown, and category summaries.",
)
def get_resume_weaknesses(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> WeaknessAnalysisResponse:
    """Retrieves cached resume weakness analysis if present, or raises 404."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    data = weakness_analysis_service.get_weakness_analysis(resume_id=resume_id, db=db)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No weakness analysis found for resume ID {resume_id}. Please call the /analyze endpoint first.",
        )

    return WeaknessAnalysisResponse(
        success=True,
        message="Resume weakness analysis retrieved successfully",
        data=data,
    )
