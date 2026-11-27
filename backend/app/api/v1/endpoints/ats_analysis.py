"""
Resume ATS Compatibility Analysis API Endpoints
Phase 4 | Feature 24: ATS Compatibility Analysis
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.ats_analysis import ATSAnalysisResponse
from app.services.ats_analysis.service import ats_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{resume_id}/ats/analyze",
    response_model=ATSAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze resume ATS compatibility",
    description="Evaluates resume layout, sections, contact info, formatting risks, and keywords using a deterministic scoring engine with AI explanations.",
)
async def analyze_resume_ats(
    resume_id: str,
    force_recalculate: bool = Query(False, description="Whether to bypass cached ATS evaluation and re-analyze"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ATSAnalysisResponse:
    """
    Evaluates:
    - Standard section detection & heading consistency
    - Contact info completeness
    - Professional summary presence
    - Work experience & education formatting
    - Technical skills presentation
    - Projects & certifications
    - Formatting risks (tables, multiple columns, textboxes, unreadable text)
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await ats_analysis_service.calculate_ats_analysis(
            resume_id=resume_id,
            force_recalculate=force_recalculate,
            db=db,
        )
        return ATSAnalysisResponse(
            success=True,
            message="Resume ATS compatibility analysis completed successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Unexpected error analyzing ATS compatibility for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume ATS compatibility: {str(exc)}",
        )


@router.get(
    "/{resume_id}/ats",
    response_model=ATSAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get previously generated ATS compatibility analysis",
    description="Retrieves persisted deterministic ATS score, category breakdown, verified issues, and formatting risks.",
)
def get_resume_ats(
    resume_id: str,
    optional: bool = Query(False, description="Return 200 with data=null instead of 404 when not analyzed"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ATSAnalysisResponse:
    """Retrieves cached resume ATS compatibility analysis if present, or raises 404."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    data = ats_analysis_service.get_ats_analysis(resume_id=resume_id, db=db)
    if not data:
        if optional:
            return JSONResponse(content={"success": True, "message": "No ATS analysis found", "data": None})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No ATS analysis found for resume ID {resume_id}. Please call the /analyze endpoint first.",
        )

    return ATSAnalysisResponse(
        success=True,
        message="Resume ATS compatibility analysis retrieved successfully",
        data=data,
    )
