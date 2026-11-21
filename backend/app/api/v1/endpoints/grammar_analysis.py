"""
Resume Grammar & Clarity Analysis API Endpoints
Phase 4 | Feature 25: Grammar & Clarity Analysis
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.grammar_analysis import GrammarAnalysisResponse
from app.services.grammar_analysis.service import grammar_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{resume_id}/grammar/analyze",
    response_model=GrammarAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze resume grammar, spelling, clarity, and professional tone",
    description="Identifies grammar errors, awkward phrasing, wordiness, tone inconsistencies, and generates before-and-after sentence comparisons without overwriting the original resume.",
)
async def analyze_resume_grammar(
    resume_id: str,
    force_recalculate: bool = Query(False, description="Whether to bypass cached grammar analysis and re-evaluate with AI"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> GrammarAnalysisResponse:
    """
    Evaluates:
    - Grammar mistakes and spelling errors
    - Sentence clarity and structure
    - Professional tone and active voice
    - Repeated words, phrases, and wordiness
    - Readability metrics and before-and-after sentence improvements
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await grammar_analysis_service.calculate_grammar_analysis(
            resume_id=resume_id,
            force_recalculate=force_recalculate,
            db=db,
        )
        return GrammarAnalysisResponse(
            success=True,
            message="Resume grammar and clarity analysis completed successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Unexpected error analyzing grammar for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume grammar and clarity: {str(exc)}",
        )


@router.get(
    "/{resume_id}/grammar",
    response_model=GrammarAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get previously generated grammar and clarity analysis",
    description="Retrieves persisted writing score, detected issues, readability measurements, and before-and-after sentence comparisons.",
)
def get_resume_grammar(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> GrammarAnalysisResponse:
    """Retrieves cached resume grammar analysis if present, or raises 404."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    data = grammar_analysis_service.get_grammar_analysis(resume_id=resume_id, db=db)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No grammar analysis found for resume ID {resume_id}. Please call the /analyze endpoint first.",
        )

    return GrammarAnalysisResponse(
        success=True,
        message="Resume grammar and clarity analysis retrieved successfully",
        data=data,
    )
