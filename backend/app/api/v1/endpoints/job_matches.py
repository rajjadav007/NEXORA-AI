"""
Job Matches API Endpoints
Phase 7 | Feature 39: Resume-to-Job Matching Engine
"""

import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.endpoints.job_descriptions import (
    _ensure_user_exists,
    _get_owned_job_description,
    _require_user_uuid,
)
from app.core.security import verify_resume_access
from app.database.session import get_db
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.schemas.job_match import (
    JobMatchListItem,
    JobMatchListResponse,
    JobMatchRequest,
    JobMatchResponse,
)
from app.services.job_matching import MatchPrerequisiteError, job_matching_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _parse_match_id(match_id: str) -> uuid.UUID:
    if not match_id or ".." in match_id or "/" in match_id or "\\" in match_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job match identifier.",
        )
    try:
        return uuid.UUID(str(match_id).strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job match identifier format.",
        )


@router.post(
    "",
    response_model=JobMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare an analyzed resume against an analyzed job description",
    description="Computes or retrieves a weighted, evidence-backed candidate-to-job match result.",
)
def create_or_get_job_match(
    payload: JobMatchRequest,
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
) -> JobMatchResponse:
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)
    _ensure_user_exists(db, user_uuid)

    resume = verify_resume_access(
        resume_id=payload.resume_id,
        db=db,
        user_id=str(user_uuid),
        x_user_id=str(user_uuid),
        allow_staging=False,
    )
    jd = _get_owned_job_description(
        db=db,
        job_description_id=payload.job_description_id,
        user_uuid=user_uuid,
    )

    try:
        result = job_matching_service.compute_and_save(
            db=db,
            user_uuid=user_uuid,
            resume=resume,
            jd=jd,
            regenerate=payload.regenerate,
        )
    except MatchPrerequisiteError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": str(exc),
                "missing_prerequisites": exc.missing_items,
            },
        )

    return JobMatchResponse(
        success=True,
        message=(
            "Job match retrieved from cache."
            if result.cached
            else "Job match computed and saved successfully."
        ),
        data=result,
    )


@router.get(
    "",
    response_model=JobMatchListResponse,
    status_code=status.HTTP_200_OK,
    summary="List saved job matches for the authenticated user",
)
def list_job_matches(
    resume_id: Optional[str] = Query(None),
    job_description_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
) -> JobMatchListResponse:
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)

    query = select(JobMatch).where(JobMatch.user_id == user_uuid).order_by(JobMatch.updated_at.desc())
    if resume_id:
        try:
            query = query.where(JobMatch.resume_id == uuid.UUID(resume_id.strip()))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid resume_id format.")
    if job_description_id:
        try:
            query = query.where(JobMatch.job_description_id == uuid.UUID(job_description_id.strip()))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job_description_id format.",
            )

    records = db.execute(query).scalars().all()
    items: List[JobMatchListItem] = []
    for rec in records:
        resume = db.execute(select(Resume).where(Resume.id == rec.resume_id)).scalar_one_or_none()
        jd = db.execute(select(JobDescription).where(JobDescription.id == rec.job_description_id)).scalar_one_or_none()
        items.append(
            JobMatchListItem(
                id=str(rec.id),
                resume_id=str(rec.resume_id),
                job_description_id=str(rec.job_description_id),
                resume_filename=resume.original_filename if resume else None,
                job_title=jd.job_title if jd else None,
                company_name=jd.company_name if jd else None,
                overall_match_score=rec.overall_match_score,
                calculation_version=rec.calculation_version,
                version_number=rec.version_number,
                created_at=rec.created_at,
                updated_at=rec.updated_at,
            )
        )

    return JobMatchListResponse(
        success=True,
        message="Job matches retrieved successfully.",
        data=items,
        total=len(items),
    )


@router.get(
    "/{match_id}",
    response_model=JobMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a previously generated job match by ID",
)
def get_job_match(
    match_id: str,
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
) -> JobMatchResponse:
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)
    parsed_id = _parse_match_id(match_id)

    try:
        result = job_matching_service.get_saved_match(db=db, match_id=parsed_id, user_uuid=user_uuid)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job match not found: {match_id}",
        )

    return JobMatchResponse(
        success=True,
        message="Job match retrieved successfully.",
        data=result,
    )
