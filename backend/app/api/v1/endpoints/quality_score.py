"""
Resume Quality Score API Endpoints
Phase 4 | Feature 21: Resume Quality Score Engine
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.quality_score import (
    QualityScoreResponse,
    QualityScoreAnalyzeRequest,
)
from app.services.quality_score.service import quality_score_service
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{resume_id}/quality-score/analyze",
    response_model=QualityScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze and calculate resume quality score",
    description="Evaluates 8 structured resume quality dimensions using LangChain ChatOllama and deterministic metrics.",
)
async def analyze_quality_score(
    resume_id: str,
    force_recalculate: bool = Query(False, description="Whether to recalculate score even if cached record exists"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> QualityScoreResponse:
    """
    Triggers the Quality Score Engine for the designated resume.
    Evaluates:
    1. Resume completeness
    2. Professional summary
    3. Technical skills
    4. Work experience
    5. Project descriptions
    6. Education
    7. Achievements & Certifications
    8. Content clarity
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await quality_score_service.calculate_quality_score(
            resume_id=resume_id,
            force_recalculate=force_recalculate,
            db=db,
        )
        return QualityScoreResponse(
            success=True,
            message="Resume quality score calculated successfully",
            data=data,
        )

    except OllamaUnavailableError as oue:
        logger.warning("Ollama unavailable for quality scoring on resume %s: %s", resume_id, oue)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(oue),
        )

    except AIOutputValidationError as aie:
        logger.error("AI output validation failed for resume %s: %s", resume_id, aie)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(aie),
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Unexpected error analyzing quality score for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate resume quality score: {str(exc)}",
        )


@router.get(
    "/{resume_id}/quality-score",
    response_model=QualityScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get previously calculated resume quality score",
    description="Retrieves the saved quality score evaluation, category breakdown, and suggestions.",
)
def get_quality_score(
    resume_id: str,
    optional: bool = Query(False, description="Return 200 with data=null instead of 404 when not analyzed"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> QualityScoreResponse:
    """
    Retrieves the persisted quality score for the specified resume.
    Returns 404 if not yet analyzed (unless optional=true).
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    data = quality_score_service.get_quality_score(resume_id, db)
    if not data:
        if optional:
            return JSONResponse(content={"success": True, "message": "No quality score evaluation found", "data": None})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No quality score evaluation found for resume ID: {resume_id}",
        )

    return QualityScoreResponse(
        success=True,
        message="Resume quality score retrieved successfully",
        data=data,
    )
