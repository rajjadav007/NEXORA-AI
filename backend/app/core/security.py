"""
Security and Access Control Utilities
Phase 3 | Resume Ownership & Identification Verification
"""

import uuid
import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.services.storage import staging_service

logger = logging.getLogger(__name__)


def validate_resume_id(resume_id: str, allow_non_uuid: bool = False) -> Optional[uuid.UUID]:
    """
    Validates resume identifier format and protects against directory traversal.
    Raises HTTPException 400 on directory traversal.
    Returns UUID if valid, or None if not a UUID (when allow_non_uuid=True).
    """
    if not resume_id or ".." in resume_id or "/" in resume_id or "\\" in resume_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume identifier.",
        )
    try:
        return uuid.UUID(str(resume_id).strip())
    except ValueError:
        if allow_non_uuid:
            return None
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume identifier format.",
        )


def verify_resume_access(
    resume_id: str,
    db: Session,
    user_id: Optional[str] = None,
    x_user_id: Optional[str] = None,
    allow_staging: bool = True,
    allow_non_uuid: bool = False,
) -> Resume:
    """
    Verifies that a resume exists (in database or temporary staging) and enforces user ownership checks.

    - Raises 400 if resume_id format is invalid (or directory traversal).
    - Raises 404 if resume record is not found in database (and not present in staging).
    - Raises 403 if resume has an assigned owner and requested user_id does not match.
    - Returns Resume database model.
    """
    parsed_uuid = validate_resume_id(resume_id, allow_non_uuid=allow_non_uuid)
    if not parsed_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )

    # 1. Check database for persisted record
    resume = db.execute(select(Resume).where(Resume.id == parsed_uuid)).scalar_one_or_none()

    if not resume:
        # Check if staged file exists on disk
        if allow_staging:
            staged_path = staging_service.get_staged_path(str(parsed_uuid))
            if staged_path and staged_path.exists():
                try:
                    # Auto-persist staged resume to database to ensure relational integrity
                    from app.services.permanent_storage import permanent_storage
                    from app.services.preview_service import preview_service
                    from app.models.resume import ResumeVersion

                    preview_data = preview_service.get_preview(str(parsed_uuid))
                    storage_key, _ = permanent_storage.persist_staged_file(
                        staged_path, str(parsed_uuid), version=1
                    )
                    effective_user_id = x_user_id or user_id
                    owner_uuid = None
                    if effective_user_id:
                        try:
                            owner_uuid = uuid.UUID(str(effective_user_id).strip())
                        except ValueError:
                            pass

                    resume = Resume(
                        id=parsed_uuid,
                        user_id=owner_uuid,
                        original_filename=preview_data.original_filename,
                        storage_key=storage_key,
                        file_type=preview_data.file_type or "pdf",
                        file_size=preview_data.file_size,
                        processing_status="COMPLETED",
                    )
                    db.add(resume)
                    db.flush()

                    version_record = ResumeVersion(
                        resume_id=resume.id,
                        version_number=1,
                        storage_key=storage_key,
                        extracted_text=preview_data.raw_text,
                        cleaned_text=preview_data.cleaned_text,
                    )
                    db.add(version_record)
                    db.commit()
                    db.refresh(resume)
                    return resume
                except Exception as exc:
                    logger.warning("Could not auto-persist staged resume %s: %s", resume_id, exc)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )

    # 2. Enforce user ownership if resume belongs to a user
    effective_user_id = x_user_id or user_id
    if effective_user_id and resume.user_id:
        try:
            req_user_uuid = uuid.UUID(str(effective_user_id).strip())
            if resume.user_id != req_user_uuid:
                logger.warning(
                    "Unauthorized access attempt to resume %s by user %s (owner: %s)",
                    resume_id,
                    effective_user_id,
                    resume.user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: You do not own resume {resume_id}.",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You do not own resume {resume_id}.",
            )

    return resume
