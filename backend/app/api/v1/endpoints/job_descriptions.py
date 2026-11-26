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
    JobDescriptionImportPreviewData,
    JobDescriptionImportRequest,
    JobDescriptionImportResponse,
    JobDescriptionListResponse,
)
from app.schemas.job_role_analysis import JobRoleAnalysisResponse
from app.services.job_import import (
    JobImportError,
    extract_job_description_from_html,
    fetch_job_page,
    normalize_and_validate_url,
)
from app.services.job_role_extraction import job_role_extraction_service
from app.services.quality_score.ai_evaluator import (
    AIOutputValidationError,
    OllamaUnavailableError,
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
        experience_required=record.experience_required,
        salary_info=record.salary_info,
        mandatory_skills=record.mandatory_skills or [],
        preferred_skills=record.preferred_skills or [],
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "/import",
    response_model=JobDescriptionImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import and preview a job description from a public URL",
    description="Validates URL against SSRF, fetches public HTML safely, and extracts structured job details for preview.",
)
async def import_job_description_from_url(
    payload: JobDescriptionImportRequest,
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
) -> JobDescriptionImportResponse:
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)

    try:
        normalized_url, _ = normalize_and_validate_url(payload.url)
    except JobImportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    existing_url = db.execute(
        select(JobDescription).where(
            JobDescription.user_id == user_uuid,
            JobDescription.source_url == normalized_url,
        )
    ).scalar_one_or_none()
    if existing_url:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate URL: this job posting has already been saved.",
        )

    try:
        page = await fetch_job_page(normalized_url)
        if page.final_url != normalized_url:
            existing_final = db.execute(
                select(JobDescription).where(
                    JobDescription.user_id == user_uuid,
                    JobDescription.source_url == page.final_url,
                )
            ).scalar_one_or_none()
            if existing_final:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Duplicate URL: this job posting has already been saved.",
                )

        extracted = extract_job_description_from_html(page.html)
    except JobImportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    return JobDescriptionImportResponse(
        success=True,
        message="Job description extracted successfully. Review and edit before saving.",
        data=JobDescriptionImportPreviewData(
            source_url=page.final_url,
            source_platform=page.source_platform,
            extraction_method=extracted.extraction_method,
            job_title=extracted.job_title,
            company_name=extracted.company_name,
            location=extracted.location,
            employment_type=extracted.employment_type,
            experience_required=extracted.experience_required,
            salary_info=extracted.salary_info,
            description=extracted.description,
            character_count=len(extracted.description),
            required_skills=extracted.required_skills,
            preferred_skills=extracted.preferred_skills,
        ),
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

    normalized_source_url = None
    if payload.source_url:
        try:
            normalized_source_url, _ = normalize_and_validate_url(payload.source_url)
        except JobImportError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message)

        duplicate_url = db.execute(
            select(JobDescription).where(
                JobDescription.user_id == user_uuid,
                JobDescription.source_url == normalized_source_url,
            )
        ).scalar_one_or_none()
        if duplicate_url:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate URL: this job posting has already been saved.",
            )

    record = JobDescription(
        user_id=user_uuid,
        job_title=payload.job_title,
        company_name=payload.company_name,
        raw_description=payload.description,
        location=payload.location,
        employment_type=payload.employment_type,
        source_url=normalized_source_url,
        source_type=payload.source_type,
        analysis_status="PENDING",
        content_hash=content_hash,
        experience_required=payload.experience_required,
        salary_info=payload.salary_info,
        mandatory_skills=payload.mandatory_skills,
        preferred_skills=payload.preferred_skills,
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


@router.post(
    "/{job_description_id}/role-analysis",
    response_model=JobRoleAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured job role metadata using Ollama",
    description="Analyzes a saved job description to extract role, department, seniority, experience, employment type, and responsibilities.",
)
async def extract_job_role_analysis(
    job_description_id: str,
    force_recalculate: bool = Query(False, description="Bypass cached extraction and re-run Ollama"),
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
) -> JobRoleAnalysisResponse:
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)
    record = _get_owned_job_description(db, job_description_id, user_uuid)

    try:
        data = await job_role_extraction_service.extract_and_save(
            db=db,
            record=record,
            force_recalculate=force_recalculate,
        )
        return JobRoleAnalysisResponse(
            success=True,
            message="Job role extraction completed successfully."
            if not data.cached
            else "Job role extraction retrieved from cache.",
            data=data,
        )
    except OllamaUnavailableError as oue:
        logger.warning("Ollama unavailable for job role extraction %s: %s", job_description_id, oue)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(oue),
        )
    except AIOutputValidationError as aie:
        logger.error("Job role extraction validation failed for %s: %s", job_description_id, aie)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(aie),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error extracting job role for %s: %s", job_description_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract job role metadata.",
        )


@router.get(
    "/{job_description_id}/role-analysis",
    response_model=JobRoleAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get saved job role extraction results",
)
def get_job_role_analysis(
    job_description_id: str,
    user_id: Optional[str] = Query(None, description="Authenticated user UUID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Authenticated user UUID"),
    db: Session = Depends(get_db),
) -> JobRoleAnalysisResponse:
    user_uuid = _require_user_uuid(user_id=user_id, x_user_id=x_user_id)
    record = _get_owned_job_description(db, job_description_id, user_uuid)

    data = job_role_extraction_service.get_saved_analysis(db=db, record=record)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job role analysis has not been run for this job description.",
        )
    return JobRoleAnalysisResponse(
        success=True,
        message="Job role analysis retrieved successfully.",
        data=data,
    )
