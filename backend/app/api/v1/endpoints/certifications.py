"""
Certifications and Achievements API Endpoints
Phase 3 | Feature 19: Certifications & Achievements Intelligence
"""

import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.resume import Resume
from app.schemas.certifications import (
    CertificationListResponse,
    CertificationSingleResponse,
    CertificationCreateRequest,
    CertificationUpdateRequest,
    CertificationConfirmRequest,
    CertificationSummaryData,
    CertificationSkillLinkData,
    AchievementListResponse,
    AchievementSingleResponse,
    AchievementCreateRequest,
    AchievementUpdateRequest,
    AchievementConfirmRequest,
    AchievementSummaryData,
    CertificationsAchievementsCombinedSummary,
)
from app.services.certifications.service import certifications_achievements_service

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


def _check_resume_exists(resume_id: str, db: Session) -> uuid.UUID:
    parsed = _validate_resume_id(resume_id)
    resume = db.execute(select(Resume).where(Resume.id == parsed)).scalar_one_or_none()
    in_staging = (
        resume_id in certifications_achievements_service._staging_certifications
        or resume_id in certifications_achievements_service._staging_achievements
    )
    if not resume and not in_staging:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )
    return parsed


# =========================================================================
# CERTIFICATIONS ENDPOINTS
# =========================================================================

@router.post(
    "/{resume_id}/certifications/extract",
    response_model=CertificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract candidate certifications from resume",
)
async def extract_certifications(
    resume_id: str,
    reprocess: bool = Query(False, description="Whether to re-run extraction"),
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits on reprocess"),
    db: Session = Depends(get_db),
) -> CertificationListResponse:
    _check_resume_exists(resume_id, db)
    try:
        certs = await certifications_achievements_service.extract_and_structure_certifications(
            resume_id=resume_id,
            reprocess=reprocess,
            force_overwrite=force_overwrite,
            db=db,
        )
        summary = certifications_achievements_service.get_certification_summary(resume_id, db)
        return CertificationListResponse(
            success=True,
            message="Certifications extracted and structured successfully",
            data=certs,
            summary=summary,
            total=len(certs),
            extraction_status="completed",
        )
    except Exception as exc:
        logger.error("Failed to extract certifications for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract certifications: {str(exc)}",
        )


@router.get(
    "/{resume_id}/certifications",
    response_model=CertificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all certifications for a resume",
)
def get_certifications(
    resume_id: str,
    db: Session = Depends(get_db),
) -> CertificationListResponse:
    _check_resume_exists(resume_id, db)
    certs = certifications_achievements_service.get_certifications(resume_id, db)
    summary = certifications_achievements_service.get_certification_summary(resume_id, db)
    return CertificationListResponse(
        success=True,
        message="Certifications retrieved successfully",
        data=certs,
        summary=summary,
        total=len(certs),
        extraction_status="completed",
    )


@router.get(
    "/{resume_id}/certifications/summary",
    response_model=CertificationSummaryData,
    status_code=status.HTTP_200_OK,
    summary="Get certification analytics summary",
)
def get_certification_summary(
    resume_id: str,
    db: Session = Depends(get_db),
) -> CertificationSummaryData:
    _check_resume_exists(resume_id, db)
    return certifications_achievements_service.get_certification_summary(resume_id, db)


@router.get(
    "/{resume_id}/certifications/pending-reviews",
    response_model=CertificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get certifications requiring review",
)
def get_pending_certification_reviews(
    resume_id: str,
    db: Session = Depends(get_db),
) -> CertificationListResponse:
    _check_resume_exists(resume_id, db)
    certs = certifications_achievements_service.get_certifications(resume_id, db)
    pending = [c for c in certs if c.review_status in ("pending", "needs_review")]
    return CertificationListResponse(
        success=True,
        message="Pending review certifications retrieved",
        data=pending,
        total=len(pending),
        extraction_status="completed",
    )


@router.get(
    "/{resume_id}/certifications/{certification_id}",
    response_model=CertificationSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single certification details",
)
def get_certification_by_id(
    resume_id: str,
    certification_id: str,
    db: Session = Depends(get_db),
) -> CertificationSingleResponse:
    _check_resume_exists(resume_id, db)
    cert = certifications_achievements_service.get_certification_by_id(resume_id, certification_id, db)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification '{certification_id}' not found.",
        )
    return CertificationSingleResponse(success=True, message="Certification retrieved", data=cert)


@router.get(
    "/{resume_id}/certifications/{certification_id}/skills",
    response_model=List[CertificationSkillLinkData],
    status_code=status.HTTP_200_OK,
    summary="Get linked canonical skills for a certification",
)
def get_certification_skills(
    resume_id: str,
    certification_id: str,
    db: Session = Depends(get_db),
) -> List[CertificationSkillLinkData]:
    _check_resume_exists(resume_id, db)
    cert = certifications_achievements_service.get_certification_by_id(resume_id, certification_id, db)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification '{certification_id}' not found.",
        )
    return cert.related_skills


@router.post(
    "/{resume_id}/certifications",
    response_model=CertificationSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a certification entry manually",
)
def add_certification(
    resume_id: str,
    payload: CertificationCreateRequest,
    db: Session = Depends(get_db),
) -> CertificationSingleResponse:
    _check_resume_exists(resume_id, db)
    entry = certifications_achievements_service.add_certification_manually(resume_id, payload, db)
    return CertificationSingleResponse(success=True, message="Certification created successfully", data=entry)


@router.patch(
    "/{resume_id}/certifications/{certification_id}",
    response_model=CertificationSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update certification information",
)
def update_certification(
    resume_id: str,
    certification_id: str,
    payload: CertificationUpdateRequest,
    db: Session = Depends(get_db),
) -> CertificationSingleResponse:
    _check_resume_exists(resume_id, db)
    updated = certifications_achievements_service.update_certification_manually(
        resume_id, certification_id, payload, db
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification '{certification_id}' not found.",
        )
    return CertificationSingleResponse(success=True, message="Certification updated successfully", data=updated)


@router.post(
    "/{resume_id}/certifications/{certification_id}/confirm",
    response_model=CertificationSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm certification verification status",
)
def confirm_certification(
    resume_id: str,
    certification_id: str,
    payload: Optional[CertificationConfirmRequest] = None,
    db: Session = Depends(get_db),
) -> CertificationSingleResponse:
    _check_resume_exists(resume_id, db)
    confirmed = certifications_achievements_service.confirm_certification(resume_id, certification_id, db)
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification '{certification_id}' not found.",
        )
    return CertificationSingleResponse(success=True, message="Certification confirmed", data=confirmed)


@router.delete(
    "/{resume_id}/certifications/{certification_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete certification",
)
def delete_certification(
    resume_id: str,
    certification_id: str,
    db: Session = Depends(get_db),
):
    _check_resume_exists(resume_id, db)
    deleted = certifications_achievements_service.delete_certification(resume_id, certification_id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification '{certification_id}' not found.",
        )
    return {"success": True, "message": "Certification deleted successfully"}


@router.post(
    "/{resume_id}/certifications/reprocess",
    response_model=CertificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocess certification extraction",
)
async def reprocess_certifications(
    resume_id: str,
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits"),
    db: Session = Depends(get_db),
) -> CertificationListResponse:
    return await extract_certifications(
        resume_id=resume_id,
        reprocess=True,
        force_overwrite=force_overwrite,
        db=db,
    )


# =========================================================================
# ACHIEVEMENTS ENDPOINTS
# =========================================================================

@router.post(
    "/{resume_id}/achievements/extract",
    response_model=AchievementListResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract candidate accomplishments and achievements",
)
async def extract_achievements(
    resume_id: str,
    reprocess: bool = Query(False, description="Whether to re-run extraction"),
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits on reprocess"),
    db: Session = Depends(get_db),
) -> AchievementListResponse:
    _check_resume_exists(resume_id, db)
    try:
        achieves = await certifications_achievements_service.extract_and_structure_achievements(
            resume_id=resume_id,
            reprocess=reprocess,
            force_overwrite=force_overwrite,
            db=db,
        )
        summary = certifications_achievements_service.get_achievement_summary(resume_id, db)
        return AchievementListResponse(
            success=True,
            message="Achievements extracted and structured successfully",
            data=achieves,
            summary=summary,
            total=len(achieves),
            extraction_status="completed",
        )
    except Exception as exc:
        logger.error("Failed to extract achievements for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract achievements: {str(exc)}",
        )


@router.get(
    "/{resume_id}/achievements",
    response_model=AchievementListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all achievements for a resume",
)
def get_achievements(
    resume_id: str,
    db: Session = Depends(get_db),
) -> AchievementListResponse:
    _check_resume_exists(resume_id, db)
    achieves = certifications_achievements_service.get_achievements(resume_id, db)
    summary = certifications_achievements_service.get_achievement_summary(resume_id, db)
    return AchievementListResponse(
        success=True,
        message="Achievements retrieved successfully",
        data=achieves,
        summary=summary,
        total=len(achieves),
        extraction_status="completed",
    )


@router.get(
    "/{resume_id}/achievements/summary",
    response_model=AchievementSummaryData,
    status_code=status.HTTP_200_OK,
    summary="Get achievement analytics summary",
)
def get_achievement_summary(
    resume_id: str,
    db: Session = Depends(get_db),
) -> AchievementSummaryData:
    _check_resume_exists(resume_id, db)
    return certifications_achievements_service.get_achievement_summary(resume_id, db)


@router.get(
    "/{resume_id}/achievements/pending-reviews",
    response_model=AchievementListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get achievements requiring review",
)
def get_pending_achievement_reviews(
    resume_id: str,
    db: Session = Depends(get_db),
) -> AchievementListResponse:
    _check_resume_exists(resume_id, db)
    achieves = certifications_achievements_service.get_achievements(resume_id, db)
    pending = [a for a in achieves if a.review_status in ("pending", "needs_review")]
    return AchievementListResponse(
        success=True,
        message="Pending review achievements retrieved",
        data=pending,
        total=len(pending),
        extraction_status="completed",
    )


@router.get(
    "/{resume_id}/achievements/{achievement_id}",
    response_model=AchievementSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single achievement details",
)
def get_achievement_by_id(
    resume_id: str,
    achievement_id: str,
    db: Session = Depends(get_db),
) -> AchievementSingleResponse:
    _check_resume_exists(resume_id, db)
    achieve = certifications_achievements_service.get_achievement_by_id(resume_id, achievement_id, db)
    if not achieve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement '{achievement_id}' not found.",
        )
    return AchievementSingleResponse(success=True, message="Achievement retrieved", data=achieve)


@router.get(
    "/{resume_id}/achievements/{achievement_id}/skills",
    response_model=List[CertificationSkillLinkData],
    status_code=status.HTTP_200_OK,
    summary="Get linked canonical skills for an achievement",
)
def get_achievement_skills(
    resume_id: str,
    achievement_id: str,
    db: Session = Depends(get_db),
) -> List[CertificationSkillLinkData]:
    _check_resume_exists(resume_id, db)
    achieve = certifications_achievements_service.get_achievement_by_id(resume_id, achievement_id, db)
    if not achieve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement '{achievement_id}' not found.",
        )
    return achieve.related_skills


@router.post(
    "/{resume_id}/achievements",
    response_model=AchievementSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an achievement entry manually",
)
def add_achievement(
    resume_id: str,
    payload: AchievementCreateRequest,
    db: Session = Depends(get_db),
) -> AchievementSingleResponse:
    _check_resume_exists(resume_id, db)
    entry = certifications_achievements_service.add_achievement_manually(resume_id, payload, db)
    return AchievementSingleResponse(success=True, message="Achievement created successfully", data=entry)


@router.patch(
    "/{resume_id}/achievements/{achievement_id}",
    response_model=AchievementSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update achievement information",
)
def update_achievement(
    resume_id: str,
    achievement_id: str,
    payload: AchievementUpdateRequest,
    db: Session = Depends(get_db),
) -> AchievementSingleResponse:
    _check_resume_exists(resume_id, db)
    updated = certifications_achievements_service.update_achievement_manually(
        resume_id, achievement_id, payload, db
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement '{achievement_id}' not found.",
        )
    return AchievementSingleResponse(success=True, message="Achievement updated successfully", data=updated)


@router.post(
    "/{resume_id}/achievements/{achievement_id}/confirm",
    response_model=AchievementSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm achievement review status",
)
def confirm_achievement(
    resume_id: str,
    achievement_id: str,
    payload: Optional[AchievementConfirmRequest] = None,
    db: Session = Depends(get_db),
) -> AchievementSingleResponse:
    _check_resume_exists(resume_id, db)
    confirmed = certifications_achievements_service.confirm_achievement(resume_id, achievement_id, db)
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement '{achievement_id}' not found.",
        )
    return AchievementSingleResponse(success=True, message="Achievement confirmed", data=confirmed)


@router.delete(
    "/{resume_id}/achievements/{achievement_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete achievement",
)
def delete_achievement(
    resume_id: str,
    achievement_id: str,
    db: Session = Depends(get_db),
):
    _check_resume_exists(resume_id, db)
    deleted = certifications_achievements_service.delete_achievement(resume_id, achievement_id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement '{achievement_id}' not found.",
        )
    return {"success": True, "message": "Achievement deleted successfully"}


@router.post(
    "/{resume_id}/achievements/reprocess",
    response_model=AchievementListResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocess achievement extraction",
)
async def reprocess_achievements(
    resume_id: str,
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits"),
    db: Session = Depends(get_db),
) -> AchievementListResponse:
    return await extract_achievements(
        resume_id=resume_id,
        reprocess=True,
        force_overwrite=force_overwrite,
        db=db,
    )


# =========================================================================
# COMBINED SUMMARY ENDPOINT
# =========================================================================

@router.get(
    "/{resume_id}/certifications-achievements/summary",
    response_model=CertificationsAchievementsCombinedSummary,
    status_code=status.HTTP_200_OK,
    summary="Get complete certifications and achievements summary",
)
def get_certifications_achievements_summary(
    resume_id: str,
    db: Session = Depends(get_db),
) -> CertificationsAchievementsCombinedSummary:
    _check_resume_exists(resume_id, db)
    return certifications_achievements_service.get_combined_summary(resume_id, db)
