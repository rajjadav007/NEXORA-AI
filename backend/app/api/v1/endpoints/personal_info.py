"""
Personal Information API Endpoints
Phase 3 | Feature 13: Personal Information Extraction
"""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access, validate_resume_id
from app.database.session import get_db
from app.schemas.personal_information import (
    PersonalInformationResponse,
    PersonalInformationData,
    PersonalInformationUpdateRequest,
)
from app.services.personal_info.service import personal_info_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_resume_id(resume_id: str) -> uuid.UUID:
    return validate_resume_id(resume_id)


@router.post(
    "/{resume_id}/personal-info/extract",
    response_model=PersonalInformationResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract personal information from resume",
    description="Extracts candidate name, contact details, location, and professional links from cleaned resume text.",
)
async def extract_personal_info(
    resume_id: str,
    reprocess: bool = Query(False, description="Whether to re-run extraction"),
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits on reprocess"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> PersonalInformationResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await personal_info_service.extract_personal_information(
            resume_id=resume_id,
            reprocess=reprocess,
            force_overwrite=force_overwrite,
            db=db,
        )

        return PersonalInformationResponse(
            success=True,
            message="Personal information extracted successfully",
            data=data,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to extract personal information for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract personal information: {str(exc)}",
        )


@router.get(
    "/{resume_id}/personal-info",
    response_model=PersonalInformationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get extracted personal information",
    description="Retrieves candidate personal information extracted for a resume.",
)
def get_personal_info(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> PersonalInformationResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    data = personal_info_service.get_personal_information(resume_id, db)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Personal information not found for resume: {resume_id}",
        )

    return PersonalInformationResponse(
        success=True,
        message="Personal information retrieved successfully",
        data=data,
    )


@router.patch(
    "/{resume_id}/personal-info",
    response_model=PersonalInformationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update personal information manually",
    description="Allows users to correct extracted details. Manually edited fields are protected against overwrite during reprocessing.",
)
def update_personal_info(
    resume_id: str,
    payload: PersonalInformationUpdateRequest,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> PersonalInformationResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    updated_data = personal_info_service.update_personal_information(
        resume_id=resume_id,
        update_data=payload,
        db=db,
    )

    if not updated_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume personal information not found for ID: {resume_id}",
        )

    return PersonalInformationResponse(
        success=True,
        message="Personal information updated successfully",
        data=updated_data,
    )


@router.post(
    "/{resume_id}/personal-info/reprocess",
    response_model=PersonalInformationResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocess personal information extraction",
    description="Re-runs personal information extraction on the resume while preserving manual corrections.",
)
async def reprocess_personal_info(
    resume_id: str,
    force_overwrite: bool = Query(False, description="Whether to discard manual user edits"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> PersonalInformationResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = await personal_info_service.extract_personal_information(
            resume_id=resume_id,
            reprocess=True,
            force_overwrite=force_overwrite,
            db=db,
        )

        return PersonalInformationResponse(
            success=True,
            message="Personal information reprocessed successfully",
            data=data,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to reprocess personal info for %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess personal information: {str(exc)}",
        )
