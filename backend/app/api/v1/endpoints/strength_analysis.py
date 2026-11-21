"""
Resume Strength Analysis API Endpoints
Phase 4 | Feature 22: Resume Strength Analysis
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.strength_analysis import StrengthAnalysisResponse
from app.services.strength_analysis.service import strength_analysis_service
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{resume_id}/strengths/analyze",
    response_model=StrengthAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze and identify candidate strengths from resume",
    description="Identifies top technical, project, experience, education, and soft skill strengths with supporting evidence.",
)
async def analyze_resume_strengths(
    resume_id: str,
    force_recalculate: bool = Query(False, description="Whether to bypass cached strength analysis and re-evaluate with LLM"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> StrengthAnalysisResponse:
    """
    Evaluates candidate strengths across 7 categories:
    - Technical skills
    - Projects
    - Work and internship experience
    - Education
    - Achievements and certifications
    - Leadership and teamwork (evidence-backed)
    - Communication and problem-solving (evidence-backed)
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await strength_analysis_service.calculate_strength_analysis(
            resume_id=resume_id,
            force_recalculate=force_recalculate,
            db=db,
        )
        return StrengthAnalysisResponse(
            success=True,
            message="Resume strength analysis completed successfully",
            data=data,
        )

    except OllamaUnavailableError as oue:
        logger.warning("Ollama unavailable for strength analysis on resume %s: %s", resume_id, oue)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(oue),
        )

    except AIOutputValidationError as aie:
        logger.error("Strength analysis structured validation failed for resume %s: %s", resume_id, aie)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(aie),
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Unexpected error analyzing strengths for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume strengths: {str(exc)}",
        )


@router.get(
    "/{resume_id}/strengths",
    response_model=StrengthAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get previously generated resume strength analysis",
    description="Retrieves persisted candidate strengths, evidence citations, and category takeaways.",
)
def get_resume_strengths(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> StrengthAnalysisResponse:
    """
    Retrieves the persisted strength analysis for a resume.
    Returns 404 if not yet analyzed.
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    data = strength_analysis_service.get_strength_analysis(resume_id, db)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No strength analysis found for resume ID: {resume_id}",
        )

    return StrengthAnalysisResponse(
        success=True,
        message="Resume strength analysis retrieved successfully",
        data=data,
    )
