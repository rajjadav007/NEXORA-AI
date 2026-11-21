"""
Skill Normalization API Endpoints
Phase 3 | Feature 17: Skill Normalization
"""

import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access, validate_resume_id
from app.database.session import get_db
from app.models.resume import Resume
from app.schemas.skills import (
    SkillListResponse,
    SkillSingleResponse,
    SkillNormalizeRequest,
    SkillManualUpdateRequest,
    SkillConfirmRequest,
    SkillRejectRequest,
    SkillAliasCreateRequest,
    SkillSummaryData,
    DictionaryResponse,
    CanonicalSkillData,
)
from app.services.skills.service import skill_normalization_service
from app.services.skills.dictionary import skill_dictionary

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_resume_id(resume_id: str) -> uuid.UUID:
    return validate_resume_id(resume_id)


# --- Resume-Scoped Skill Endpoints ---

@router.post(
    "/{resume_id}/skills/extract",
    response_model=SkillListResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract and normalize skills from resume",
    description="Parses skills from resume text, applies multi-layer normalization, consolidates duplicates, and returns profile.",
)
async def extract_and_normalize_skills(
    resume_id: str,
    reprocess: bool = Query(False, description="Whether to re-run extraction"),
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits on reprocess"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SkillListResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        skills = await skill_normalization_service.extract_and_normalize_skills(
            resume_id=resume_id,
            reprocess=reprocess,
            force_overwrite=force_overwrite,
            db=db,
        )
        summary = skill_normalization_service.get_normalization_summary(resume_id, db)
        return SkillListResponse(
            success=True,
            message="Skills extracted and normalized successfully",
            data=skills,
            summary=summary,
            total=len(skills),
            extraction_status="completed",
        )
    except Exception as exc:
        logger.error("Failed to extract skills for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to normalize skills: {str(exc)}",
        )


@router.post(
    "/{resume_id}/skills/normalize",
    response_model=SkillListResponse,
    status_code=status.HTTP_200_OK,
    summary="Normalize arbitrary list of raw skills",
    description="Accepts an explicit list of raw skill strings, maps aliases, prevents false merges, and consolidates.",
)
async def normalize_raw_skills(
    resume_id: str,
    payload: SkillNormalizeRequest,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SkillListResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    try:
        skills = await skill_normalization_service.normalize_skill_list(
            raw_skills=payload.skills,
            context_text=payload.context_text,
        )
        return SkillListResponse(
            success=True,
            message="Skills normalized successfully",
            data=skills,
            total=len(skills),
            extraction_status="completed",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed normalizing raw skill list: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed normalizing skills: {str(exc)}",
        )


@router.get(
    "/{resume_id}/skills",
    response_model=SkillListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get normalized skills for resume",
    description="Retrieves standardized skill profile and summary analytics for a candidate resume.",
)
def get_normalized_skills(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SkillListResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    skills = skill_normalization_service.get_normalized_skills(resume_id, db)
    summary = skill_normalization_service.get_normalization_summary(resume_id, db)
    return SkillListResponse(
        success=True,
        message="Skills retrieved successfully",
        data=skills,
        summary=summary,
        total=len(skills),
        extraction_status="completed",
    )


@router.post(
    "/{resume_id}/skills/reprocess",
    response_model=SkillListResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocess skill normalization",
    description="Re-runs skill normalization while preserving user-confirmed mappings unless force_overwrite=True.",
)
async def reprocess_skills(
    resume_id: str,
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SkillListResponse:
    return await extract_and_normalize_skills(
        resume_id=resume_id,
        reprocess=True,
        force_overwrite=force_overwrite,
        user_id=user_id,
        x_user_id=x_user_id,
        db=db,
    )


@router.get(
    "/{resume_id}/skills/summary",
    response_model=SkillSummaryData,
    status_code=status.HTTP_200_OK,
    summary="Get normalization summary metrics",
    description="Returns aggregate counts: total original, unique canonical, duplicates consolidated, pending reviews, etc.",
)
def get_skills_summary(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SkillSummaryData:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    return skill_normalization_service.get_normalization_summary(resume_id, db)


@router.get(
    "/{resume_id}/skills/pending-reviews",
    response_model=SkillListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get skills requiring human review",
    description="Returns ambiguous or low-confidence skill mappings awaiting user confirmation.",
)
def get_pending_reviews(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SkillListResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    pending = skill_normalization_service.get_pending_reviews(resume_id, db)
    return SkillListResponse(
        success=True,
        message="Pending review skills retrieved",
        data=pending,
        total=len(pending),
        extraction_status="completed",
    )


@router.post(
    "/{resume_id}/skills/{skill_id}/confirm",
    response_model=SkillSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm proposed skill mapping",
    description="Marks a pending review skill as confirmed, protecting it from automatic overwrite.",
)
def confirm_skill_mapping(
    resume_id: str,
    skill_id: str,
    payload: Optional[SkillConfirmRequest] = None,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SkillSingleResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    override_name = payload.canonical_name if payload else None
    res = skill_normalization_service.confirm_mapping(
        resume_id=resume_id,
        skill_id=skill_id,
        override_canonical_name=override_name,
        db=db,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found.",
        )
    return SkillSingleResponse(success=True, message="Skill mapping confirmed", data=res)


@router.post(
    "/{resume_id}/skills/{skill_id}/reject",
    response_model=SkillSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject proposed skill mapping",
    description="Rejects a suggested mapping, reverting canonical name to raw input value.",
)
def reject_skill_mapping(
    resume_id: str,
    skill_id: str,
    payload: Optional[SkillRejectRequest] = None,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SkillSingleResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    res = skill_normalization_service.reject_mapping(
        resume_id=resume_id,
        skill_id=skill_id,
        db=db,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found.",
        )
    return SkillSingleResponse(success=True, message="Skill mapping rejected", data=res)


@router.patch(
    "/{resume_id}/skills/{skill_id}",
    response_model=SkillSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Manually update skill record",
    description="Updates canonical name, category, or status of a normalized skill.",
)
def update_skill_entry(
    resume_id: str,
    skill_id: str,
    payload: SkillManualUpdateRequest,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SkillSingleResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    res = skill_normalization_service.update_skill_manually(
        resume_id=resume_id,
        skill_id=skill_id,
        payload=payload,
        db=db,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found.",
        )
    return SkillSingleResponse(success=True, message="Skill updated successfully", data=res)


@router.delete(
    "/{resume_id}/skills/{skill_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete normalized skill record",
    description="Removes a skill record from candidate profile.",
)
def delete_skill_entry(
    resume_id: str,
    skill_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    deleted = skill_normalization_service.delete_skill(resume_id, skill_id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found.",
        )
    return {"success": True, "message": "Skill deleted successfully"}


# --- Global Canonical Dictionary Endpoints ---

dict_router = APIRouter()

@dict_router.get(
    "/dictionary",
    response_model=DictionaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get canonical skill dictionary",
    description="Lists all standardized skills, their categories, and known aliases with dictionary version.",
)
def get_canonical_dictionary(
    db: Session = Depends(get_db),
) -> DictionaryResponse:
    skill_dictionary.sync_from_db(db)
    items = skill_dictionary.list_canonical_skills()
    parsed_items = [
        CanonicalSkillData(
            id=item.get("id"),
            name=item["name"],
            category=item["category"],
            skill_type=item.get("skill_type", "technical"),
            aliases=item.get("aliases", []),
            description=item.get("description"),
            version=item.get("version", skill_dictionary.version),
            is_active=item.get("is_active", True),
        )
        for item in items
    ]
    return DictionaryResponse(
        success=True,
        message="Dictionary retrieved successfully",
        version=skill_dictionary.version,
        total=len(parsed_items),
        data=parsed_items,
    )


@dict_router.post(
    "/dictionary/alias",
    status_code=status.HTTP_201_CREATED,
    summary="Add new alias to canonical skill",
    description="Associates a new alias or abbreviation with an existing canonical skill. Rejects conflicting mappings.",
)
def add_skill_alias(
    payload: SkillAliasCreateRequest,
    db: Session = Depends(get_db),
):
    success, msg = skill_dictionary.add_alias(
        canonical_name=payload.canonical_name,
        new_alias=payload.alias,
        category=payload.category,
        skill_type=payload.skill_type or "technical",
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )
    return {"success": True, "message": msg}
