"""
Experience Analysis API Endpoints
Phase 3 | Feature 15: Experience Analysis
"""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.resume import Resume
from app.schemas.experience import (
    ExperienceListResponse,
    ExperienceSingleResponse,
    ExperienceCreateRequest,
    ExperienceUpdateRequest,
    ExperienceSummaryData,
    CareerProgressionResponse,
)
from app.services.experience.service import experience_service

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


def _validate_experience_id(experience_id: str) -> uuid.UUID:
    """Security verification on experience identifier format."""
    try:
        return uuid.UUID(experience_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid experience identifier format.",
        )


@router.post(
    "/{resume_id}/experience/extract",
    response_model=ExperienceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract experience records from resume",
    description="Extracts, normalizes, validates, and structures candidate professional experience from resume text.",
)
async def extract_experience(
    resume_id: str,
    reprocess: bool = Query(False, description="Whether to re-run extraction"),
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits on reprocess"),
    db: Session = Depends(get_db),
) -> ExperienceListResponse:
    parsed_uuid = _validate_resume_id(resume_id)

    resume = db.execute(select(Resume).where(Resume.id == parsed_uuid)).scalar_one_or_none()
    if not resume and resume_id not in experience_service._staging_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )

    try:
        entries = await experience_service.extract_experience(
            resume_id=resume_id,
            reprocess=reprocess,
            force_overwrite=force_overwrite,
            db=db,
        )
        summary = experience_service.get_experience_summary(resume_id=resume_id, db=db)

        return ExperienceListResponse(
            success=True,
            message="Experience extracted successfully",
            data=entries,
            summary=summary,
            total=len(entries),
            extraction_status="completed",
        )
    except Exception as exc:
        logger.error("Failed to extract experience for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract experience: {str(exc)}",
        )


@router.get(
    "/{resume_id}/experience",
    response_model=ExperienceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get experience records for a resume",
    description="Retrieves professional experience records and summary for a resume.",
)
def get_experience(
    resume_id: str,
    db: Session = Depends(get_db),
) -> ExperienceListResponse:
    parsed_uuid = _validate_resume_id(resume_id)

    resume = db.execute(select(Resume).where(Resume.id == parsed_uuid)).scalar_one_or_none()
    if not resume and resume_id not in experience_service._staging_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )

    entries = experience_service.get_experience(resume_id, db)
    summary = experience_service.get_experience_summary(resume_id, db)

    return ExperienceListResponse(
        success=True,
        message="Experience records retrieved successfully",
        data=entries,
        summary=summary,
        total=len(entries),
        extraction_status="completed",
    )


@router.post(
    "/{resume_id}/experience/reprocess",
    response_model=ExperienceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocess experience extraction",
    description="Re-extracts experience records while protecting user manual edits.",
)
async def reprocess_experience(
    resume_id: str,
    payload: Optional[dict] = None,
    force_overwrite: bool = Query(False, description="Whether to discard manual user edits"),
    db: Session = Depends(get_db),
) -> ExperienceListResponse:
    parsed_uuid = _validate_resume_id(resume_id)

    resume = db.execute(select(Resume).where(Resume.id == parsed_uuid)).scalar_one_or_none()
    if not resume and resume_id not in experience_service._staging_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )

    overwrite = force_overwrite
    if payload and isinstance(payload, dict):
        overwrite = payload.get("force_overwrite", overwrite)

    try:
        entries = await experience_service.extract_experience(
            resume_id=resume_id,
            reprocess=True,
            force_overwrite=overwrite,
            db=db,
        )
        summary = experience_service.get_experience_summary(resume_id, db)

        return ExperienceListResponse(
            success=True,
            message="Experience reprocessed successfully",
            data=entries,
            summary=summary,
            total=len(entries),
            extraction_status="completed",
        )
    except Exception as exc:
        logger.error("Failed to reprocess experience for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess experience: {str(exc)}",
        )


@router.post(
    "/{resume_id}/experience",
    response_model=ExperienceSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an experience record manually",
    description="Manually adds a work experience record to a resume.",
)
def add_experience(
    resume_id: str,
    payload: ExperienceCreateRequest,
    db: Session = Depends(get_db),
) -> ExperienceSingleResponse:
    _validate_resume_id(resume_id)

    created = experience_service.add_experience_entry(resume_id, payload, db)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found for ID: {resume_id}",
        )

    return ExperienceSingleResponse(
        success=True,
        message="Experience record added successfully",
        data=created,
    )


@router.patch(
    "/{resume_id}/experience/{experience_id}",
    response_model=ExperienceSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an experience record",
    description="Updates an existing experience record and marks it as user-edited.",
)
def update_experience(
    resume_id: str,
    experience_id: str,
    payload: ExperienceUpdateRequest,
    db: Session = Depends(get_db),
) -> ExperienceSingleResponse:
    _validate_resume_id(resume_id)
    _validate_experience_id(experience_id)

    updated = experience_service.update_experience_entry(resume_id, experience_id, payload, db)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experience entry not found for ID: {experience_id}",
        )

    return ExperienceSingleResponse(
        success=True,
        message="Experience record updated successfully",
        data=updated,
    )


@router.delete(
    "/{resume_id}/experience/{experience_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an experience record",
    description="Deletes an experience record from a resume.",
)
def delete_experience(
    resume_id: str,
    experience_id: str,
    db: Session = Depends(get_db),
):
    _validate_resume_id(resume_id)
    _validate_experience_id(experience_id)

    success = experience_service.delete_experience_entry(resume_id, experience_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experience entry not found for ID: {experience_id}",
        )

    return {
        "success": True,
        "message": f"Experience record {experience_id} deleted successfully",
    }


@router.get(
    "/{resume_id}/experience/summary",
    response_model=ExperienceSummaryData,
    status_code=status.HTTP_200_OK,
    summary="Get experience summary",
    description="Retrieves aggregate experience metrics, non-overlapping total duration, and career progression observations.",
)
def get_experience_summary(
    resume_id: str,
    db: Session = Depends(get_db),
) -> ExperienceSummaryData:
    _validate_resume_id(resume_id)
    return experience_service.get_experience_summary(resume_id, db)


@router.get(
    "/{resume_id}/experience/progression",
    response_model=CareerProgressionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get career progression",
    description="Retrieves chronological career progression analysis, transitions, and employment gaps.",
)
def get_career_progression(
    resume_id: str,
    db: Session = Depends(get_db),
) -> CareerProgressionResponse:
    _validate_resume_id(resume_id)
    return experience_service.get_career_progression(resume_id, db)
