"""
AI Resume Report API Endpoints
Phase 5 | Feature 31: AI Resume Report
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header, Response
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.report import (
    GenerateReportResponse,
    GetReportResponse,
    ReportHistoryResponse,
)
from app.services.report.service import resume_report_service
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{resume_id}/reports/generate",
    response_model=GenerateReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Resume Report",
    description="Generates or retrieves a comprehensive, 11-section AI Resume Report using local Ollama model.",
)
async def generate_resume_report(
    resume_id: str,
    force_recalculate: bool = Query(False, description="Whether to bypass cached report and re-generate with Ollama"),
    fallback_to_deterministic: bool = Query(False, description="Whether to fallback to deterministic analysis if Ollama is unreachable"),
    user_id: Optional[str] = Query(None, description="Optional authenticated user ID query param"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Optional authenticated user ID header"),
    db: Session = Depends(get_db),
) -> GenerateReportResponse:
    """
    Coordinates AI Resume Report generation:
    1. Verifies authenticated user & resume access
    2. Loads Phase 3, Phase 4, and Phase 5 structured findings
    3. Invokes local Ollama model (with timeout & connection protection)
    4. Validates structured output schema with Pydantic
    5. Persists report in PostgreSQL resume_reports table
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        report_data = await resume_report_service.generate_report(
            resume_id=resume_id,
            force_recalculate=force_recalculate,
            fallback_to_deterministic=fallback_to_deterministic,
            user_id=user_id or x_user_id,
            db=db,
        )
        return GenerateReportResponse(
            success=True,
            message="AI Resume Report generated successfully",
            data=report_data,
        )

    except OllamaUnavailableError as oue:
        logger.warning("Ollama unavailable for report generation on resume %s: %s", resume_id, oue)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(oue),
        )

    except AIOutputValidationError as aoe:
        logger.error("AI report output validation failed for resume %s: %s", resume_id, aoe)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI model generated invalid report structure: {str(aoe)}",
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Unexpected error generating report for resume %s: %s", resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI resume report: {str(exc)}",
        )


@router.get(
    "/{resume_id}/reports",
    response_model=ReportHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Resume Report History",
    description="Retrieves a list of all previously generated AI reports for a resume.",
)
def get_resume_report_history(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ReportHistoryResponse:
    """Retrieves chronological report history for a resume."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        history = resume_report_service.get_report_history(resume_id=resume_id, db=db)
        return ReportHistoryResponse(
            success=True,
            message="Resume report history retrieved successfully",
            data=history,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving report history for resume %s: %s", resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report history: {str(exc)}",
        )


@router.get(
    "/{resume_id}/reports/latest",
    response_model=GetReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Latest AI Resume Report",
    description="Retrieves the most recent AI Resume Report for a resume, or 404 if not yet generated.",
)
def get_latest_resume_report(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> GetReportResponse:
    """Retrieves the latest generated report."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    report_data = resume_report_service.get_latest_report(resume_id=resume_id, db=db)
    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AI resume report found for resume ID {resume_id}. Please generate a report first.",
        )

    return GetReportResponse(
        success=True,
        message="Latest AI resume report retrieved successfully",
        data=report_data,
    )


@router.get(
    "/{resume_id}/reports/{report_id}",
    response_model=GetReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Specific AI Resume Report",
    description="Retrieves a specific report by its report ID.",
)
def get_resume_report_by_id(
    resume_id: str,
    report_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> GetReportResponse:
    """Retrieves an individual report by report ID."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        report_data = resume_report_service.get_report_by_id(
            resume_id=resume_id,
            report_id=report_id,
            db=db,
        )
        return GetReportResponse(
            success=True,
            message="AI resume report retrieved successfully",
            data=report_data,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving report %s for resume %s: %s", report_id, resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report: {str(exc)}",
        )


@router.get(
    "/{resume_id}/reports/{report_id}/pdf",
    summary="Export AI Resume Report as PDF",
    description="Generates and downloads a publication-grade, multi-page PDF document for a saved AI Resume Report.",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the generated PDF binary stream.",
        },
        404: {"description": "Resume or report not found."},
        400: {"description": "Invalid UUID format."},
    },
)
def export_resume_report_pdf(
    resume_id: str,
    report_id: str,
    user_id: Optional[str] = Query(None, description="Optional authenticated user ID query param"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Optional authenticated user ID header"),
    db: Session = Depends(get_db),
):
    """
    Phase 5 | Feature 32: PDF Report Export
    Exports saved AI Resume Report as professional PDF.
    Does not regenerate AI report.
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    export_result = resume_report_service.export_report_pdf(
        resume_id=resume_id,
        report_id=report_id,
        db=db,
        user_id=user_id or x_user_id,
    )

    pdf_bytes = export_result["pdf_bytes"]
    filename = export_result["filename"]

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )

