"""
Education Analysis API Endpoints
Phase 3 | Feature 14: Education Analysis
"""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.resume import Resume
from app.schemas.education import (
    EducationListResponse,
    EducationSingleResponse,
    EducationCreateRequest,
    EducationUpdateRequest,
)
from app.services.education.service import education_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_resume_id(resume_id: str) -> uuid.UUID:
    """Security verification on resume identifier format."""
    if not resume_id or ".." in resume_id or "/" in resume_id or "\\" in resume_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume identifier.",
        )
    try:
        return uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume identifier format.",
        )


def _validate_education_id(education_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(education_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid education identifier format.",
        )


@router.post(
    "/{resume_id}/education/extract",
    response_model=EducationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract education records from resume",
    description="Extracts, normalizes, validates, and orders candidate education records into a structured chronological timeline.",
)
async def extract_education(
    resume_id: str,
    reprocess: bool = Query(False, description="Whether to re-run extraction"),
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits on reprocess"),
    db: Session = Depends(get_db),
) -> EducationListResponse:
    parsed_uuid = _validate_resume_id(resume_id)

    resume = db.execute(select(Resume).where(Resume.id == parsed_uuid)).scalar_one_or_none()
    if not resume and resume_id not in education_service._staging_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )

    try:
        entries = await education_service.extract_education(
            resume_id=resume_id,
            reprocess=reprocess,
            force_overwrite=force_overwrite,
            db=db,
        )

        return EducationListResponse(
            success=True,
            message="Education extracted successfully",
            data=entries,
            total=len(entries),
            extraction_status="completed",
        )
    except Exception as exc:
        logger.error("Failed to extract education for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract education: {str(exc)}",
        )


@router.get(
    "/{resume_id}/education",
    response_model=EducationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get education records for a resume",
    description="Retrieves candidate education records ordered chronologically.",
)
def get_education(
    resume_id: str,
    db: Session = Depends(get_db),
) -> EducationListResponse:
    parsed_uuid = _validate_resume_id(resume_id)

    resume = db.execute(select(Resume).where(Resume.id == parsed_uuid)).scalar_one_or_none()
    if not resume and resume_id not in education_service._staging_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )

    entries = education_service.get_education(resume_id, db)
    return EducationListResponse(
        success=True,
        message="Education records retrieved successfully",
        data=entries,
        total=len(entries),
        extraction_status="completed",
    )


@router.post(
    "/{resume_id}/education/reprocess",
    response_model=EducationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocess education extraction",
    description="Re-extracts education records while protecting user manual edits.",
)
async def reprocess_education(
    resume_id: str,
    payload: Optional[dict] = None,
    force_overwrite: bool = Query(False, description="Whether to discard manual user edits"),
    db: Session = Depends(get_db),
) -> EducationListResponse:
    parsed_uuid = _validate_resume_id(resume_id)

    resume = db.execute(select(Resume).where(Resume.id == parsed_uuid)).scalar_one_or_none()
    if not resume and resume_id not in education_service._staging_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )

    # Support force_overwrite from json body or query param
    overwrite = force_overwrite
    if payload and isinstance(payload, dict):
        overwrite = payload.get("force_overwrite", overwrite)

    try:
        entries = await education_service.extract_education(
            resume_id=resume_id,
            reprocess=True,
            force_overwrite=overwrite,
            db=db,
        )

        return EducationListResponse(
            success=True,
            message="Education reprocessed successfully",
            data=entries,
            total=len(entries),
            extraction_status="completed",
        )
    except Exception as exc:
        logger.error("Failed to reprocess education for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess education: {str(exc)}",
        )


@router.post(
    "/{resume_id}/education",
    response_model=EducationSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an education record manually",
    description="Manually adds an academic qualification to a resume.",
)
def add_education(
    resume_id: str,
    payload: EducationCreateRequest,
    db: Session = Depends(get_db),
) -> EducationSingleResponse:
    _validate_resume_id(resume_id)

    created = education_service.add_education_entry(resume_id, payload, db)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found for ID: {resume_id}",
        )

    return EducationSingleResponse(
        success=True,
        message="Education record added successfully",
        data=created,
    )


@router.patch(
    "/{resume_id}/education/{education_id}",
    response_model=EducationSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an education record",
    description="Updates an existing education record. Marks the entry as user-edited.",
)
def update_education(
    resume_id: str,
    education_id: str,
    payload: EducationUpdateRequest,
    db: Session = Depends(get_db),
) -> EducationSingleResponse:
    _validate_resume_id(resume_id)
    _validate_education_id(education_id)

    updated = education_service.update_education_entry(resume_id, education_id, payload, db)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Education entry not found for ID: {education_id}",
        )

    return EducationSingleResponse(
        success=True,
        message="Education record updated successfully",
        data=updated,
    )


@router.delete(
    "/{resume_id}/education/{education_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an education record",
    description="Deletes an education record from a resume.",
)
def delete_education(
    resume_id: str,
    education_id: str,
    db: Session = Depends(get_db),
):
    _validate_resume_id(resume_id)
    _validate_education_id(education_id)

    success = education_service.delete_education_entry(resume_id, education_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Education entry not found for ID: {education_id}",
        )

    return {
        "success": True,
        "message": f"Education record {education_id} deleted successfully",
    }
