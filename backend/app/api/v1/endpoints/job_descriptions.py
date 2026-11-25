"""
Job Description API Endpoints
Phase 6 | Feature 33: Job Description Input
"""

import hashlib
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.job_description import JobDescription
from app.models.user import User
from app.schemas.job_description import (
    JobDescriptionCreateRequest,
    JobDescriptionCreateResponse,
    JobDescriptionData,
    JobDescriptionDetailResponse,
    JobDescriptionListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _require_user_uuid(
    user_id: Optional[str] = None,
    x_user_id: Optional[str] = None,
) -> uuid.UUID:
    """Resolve and validate authenticated user UUID from X-User-Id header or user_id query."""
    effective_user_id = (x_user_id or user_id or "").strip()
    if not effective_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: provide X-User-Id header or user_id.",
        )
    try:
        return uuid.UUID(effective_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user identifier format.",
        )


def _ensure_user_exists(db: Session, user_uuid: uuid.UUID) -> User:
    """Return existing User or provision a placeholder User record for FK integrity."""
    user_record = db.execute(select(User).where(User.id == user_uuid)).scalar_one_or_none()
    if not user_record:
        user_record = User(
            id=user_uuid,
            email=f"user_{str(user_uuid)[:8]}@nexora.local",
        )
        db.add(user_record)
        db.flush()
    return user_record


def _parse_job_description_id(job_description_id: str) -> uuid.UUID:
    """Validate job_description_id UUID format."""
    if not job_description_id or ".." in job_description_id or "/" in job_description_id or "\\" in job_description_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job description identifier.",
        )
    try:
        return uuid.UUID(str(job_description_id).strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job description identifier format.",
        )


def _get_owned_job_description(
    db: Session,
    job_description_id: str,
    user_uuid: uuid.UUID,
) -> JobDescription:
    """Fetch a job description and verify ownership."""
    jd_uuid = _parse_job_description_id(job_description_id)
    record = db.execute(
        select(JobDescription).where(JobDescription.id == jd_uuid)
    ).scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description not found: {job_description_id}",
        )

    if record.user_id != user_uuid:
        logger.warning(
            "Unauthorized access attempt to job description %s by user %s (owner: %s)",
            job_description_id,
            user_uuid,
            record.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this job description.",
        )

    return record


def _compute_content_hash(
    user_uuid: uuid.UUID,
    job_title: str,
    company_name: str,
    description: str,
) -> str:
    normalized = f"{user_uuid}|{job_title.strip().lower()}|{company_name.strip().lower()}|{description.strip()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _to_data(record: JobDescription) -> JobDescriptionData:
    return JobDescriptionData(
        id=str(record.id),
        user_id=str(record.user_id),
        job_title=record.job_title,
        company_name=record.company_name,
        description=record.raw_description,
        character_count=len(record.raw_description),
        location=record.location,
        employment_type=record.employment_type,
        source_url=record.source_url,
        source_type=record.source_type,
        analysis_status=record.analysis_status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "",
    response_model=JobDescriptionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and save a job description",
    description="Validates and persists a manually entered job description for the authenticated user.",
)
def create_job_description(
    payload: JobDescriptionCreateRequest,
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
) -> JobDescriptionCreateResponse:
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)
    _ensure_user_exists(db, user_uuid)

    content_hash = _compute_content_hash(
        user_uuid=user_uuid,
        job_title=payload.job_title,
        company_name=payload.company_name,
        description=payload.description,
    )

    duplicate = db.execute(
        select(JobDescription).where(
            JobDescription.user_id == user_uuid,
            JobDescription.content_hash == content_hash,
        )
    ).scalar_one_or_none()

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate submission: this job description has already been saved.",
        )

    record = JobDescription(
        user_id=user_uuid,
        job_title=payload.job_title,
        company_name=payload.company_name,
        raw_description=payload.description,
        location=payload.location,
        employment_type=payload.employment_type,
        source_type="manual",
        analysis_status="PENDING",
        content_hash=content_hash,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return JobDescriptionCreateResponse(
        success=True,
        message="Job description saved successfully.",
        data=_to_data(record),
    )


@router.get(
    "",
    response_model=JobDescriptionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List saved job descriptions",
    description="Lists job descriptions belonging to the authenticated user.",
)
def list_job_descriptions(
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
) -> JobDescriptionListResponse:
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)

    records = db.execute(
        select(JobDescription)
        .where(JobDescription.user_id == user_uuid)
        .order_by(JobDescription.created_at.desc())
    ).scalars().all()

    return JobDescriptionListResponse(
        success=True,
        message="Job descriptions retrieved successfully.",
        total=len(records),
        data=[_to_data(r) for r in records],
    )


@router.get(
    "/{job_description_id}",
    response_model=JobDescriptionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job description details",
)
def get_job_description(
    job_description_id: str,
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
) -> JobDescriptionDetailResponse:
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)
    record = _get_owned_job_description(db, job_description_id, user_uuid)

    return JobDescriptionDetailResponse(
        success=True,
        message="Job description retrieved successfully.",
        data=_to_data(record),
    )


@router.delete(
    "/{job_description_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a saved job description",
)
def delete_job_description(
    job_description_id: str,
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
):
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)
    record = _get_owned_job_description(db, job_description_id, user_uuid)

    db.delete(record)
    db.commit()

    return {
        "success": True,
        "message": "Job description deleted successfully.",
    }
