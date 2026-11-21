"""
Resume API Endpoints
Phase 2 | Feature 6: Resume Storage
"""

import uuid
import logging
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends, Query, Header
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.security import verify_resume_access, validate_resume_id
from app.database.session import get_db
from app.models.resume import Resume, ResumeVersion
from app.models.user import User
from app.schemas.resume import ResumeUploadResponse, ResumeUploadData
from app.schemas.extraction import ExtractionResponse, ExtractionStatus
from app.schemas.cleaning import CleaningResponse, CleaningStatus, CleanRequest
from app.schemas.preview import ResumePreviewResponse, ResumePreviewData, PreviewStatus
from app.schemas.storage import (
    SaveResumeRequest,
    SaveResumeResponse,
    StoredResumeDetailResponse,
    ResumeListResponse,
    StoredResumeData,
    ResumeVersionData,
)
from app.services.storage import (
    staging_service,
    StorageError,
)
from app.services.permanent_storage import permanent_storage
from app.services.validation import (
    validation_manager,
    FileValidationError,
    ValidationErrorCode,
)
from app.services.extraction import extraction_service
from app.services.cleaning import cleaning_service
from app.services.preview_service import preview_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload, validate, and persist a resume document",
    description="Accepts PDF or DOCX resume documents, validates structure & integrity, stages them, and persists canonical resume record.",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume document (PDF or DOCX, max 10MB)"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """
    Accepts multipart/form-data upload with a 'file' parameter.
    Validates file extension, size, MIME type, signatures, and document integrity.
    Stages the file securely, creates persistent canonical resume record, and returns upload metadata.
    Automatically removes incomplete or invalid files.
    """
    if not file or not file.filename or not file.filename.strip():
        logger.warning("Rejected upload with empty or missing filename")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": {
                    "code": ValidationErrorCode.EMPTY_FILE,
                    "message": "No file provided or filename is empty.",
                    "category": "file_type",
                    "details": {},
                },
                "detail": "No file provided or filename is empty.",
            },
        )

    upload_id = None
    try:
        # 1. Stage the file stream safely in private temporary storage
        metadata = await staging_service.stage_upload(file)
        upload_id = metadata.upload_id

        staged_path = staging_service.get_staged_path(upload_id)
        if not staged_path or not staged_path.exists():
            raise StorageError("Staged file could not be retrieved from temporary storage.")

        # 2. Run comprehensive 6-stage validation pipeline
        val_result = validation_manager.validate_file(
            file_path=staged_path,
            original_filename=file.filename,
            client_content_type=file.content_type,
        )

        # 3. Persist valid resume record to permanent storage & database
        storage_key, _ = permanent_storage.persist_staged_file(
            staged_path, upload_id, version=1
        )

        owner_uuid = None
        effective_user_id = x_user_id or user_id
        if effective_user_id:
            try:
                owner_uuid = uuid.UUID(str(effective_user_id).strip())
            except ValueError:
                pass

        # Pre-extract and clean text for initial version record
        raw_text = ""
        cleaned_text = ""
        try:
            preview_data = preview_service.get_preview(upload_id)
            raw_text = preview_data.raw_text or ""
            cleaned_text = preview_data.cleaned_text or ""
        except Exception:
            pass

        parsed_uuid = uuid.UUID(upload_id)
        new_resume = Resume(
            id=parsed_uuid,
            user_id=owner_uuid,
            original_filename=metadata.original_filename,
            storage_key=storage_key,
            file_type=val_result.file_type or Path(metadata.original_filename).suffix.lstrip(".").lower() or "pdf",
            file_size=metadata.file_size,
            processing_status="COMPLETED",
        )
        db.add(new_resume)
        db.flush()

        version_record = ResumeVersion(
            resume_id=new_resume.id,
            version_number=1,
            storage_key=storage_key,
            extracted_text=raw_text,
            cleaned_text=cleaned_text,
        )
        db.add(version_record)
        db.commit()
        db.refresh(new_resume)

        return ResumeUploadResponse(
            success=True,
            message="Resume uploaded successfully",
            data=ResumeUploadData(
                upload_id=str(new_resume.id),
                original_filename=metadata.original_filename,
                file_size=metadata.file_size,
                content_type=metadata.content_type,
                status=metadata.status,
                file_type=val_result.file_type,
                is_valid=True,
            ),
        )

    except FileValidationError as val_exc:
        logger.warning(
            "File validation rejected upload (code=%s): %s",
            val_exc.code,
            val_exc.message,
        )
        if upload_id:
            staging_service.cleanup_file(upload_id)

        return JSONResponse(
            status_code=val_exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": val_exc.code,
                    "message": val_exc.message,
                    "category": val_exc.category,
                    "details": val_exc.details,
                },
                "detail": val_exc.message,
            },
        )

    except StorageError as exc:
        logger.error("Storage error processing upload: %s", exc)
        if upload_id:
            staging_service.cleanup_file(upload_id)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": ValidationErrorCode.FILE_VALIDATION_FAILED,
                    "message": "Failed to store uploaded file. Please try again.",
                    "category": "storage",
                    "details": {},
                },
                "detail": "Failed to store uploaded file. Please try again.",
            },
        )

    except Exception as exc:
        logger.error("Unexpected error during resume upload & validation: %s", exc)
        if upload_id:
            staging_service.cleanup_file(upload_id)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": ValidationErrorCode.FILE_VALIDATION_FAILED,
                    "message": "An unexpected error occurred while processing the upload.",
                    "category": "system",
                    "details": {},
                },
                "detail": "An unexpected error occurred while processing the upload.",
            },
        )


@router.post(
    "/{resume_id}/extract",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text from a validated staged resume",
    description="Extracts raw text, pages, and structured content blocks from a validated PDF or DOCX resume.",
)
async def extract_resume(resume_id: str) -> ExtractionResponse:
    """
    Retrieves the validated staged document by resume_id/upload_id,
    executes format-specific text extraction, and returns structured metadata.
    """
    staged_path = staging_service.get_staged_path(resume_id)
    if not staged_path or not staged_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume file not found or staging expired for ID: {resume_id}",
        )

    # Reconstruct original filename from staged naming convention ({upload_id}_{original_filename})
    filename = staged_path.name
    if "_" in filename:
        original_filename = filename.split("_", 1)[1]
    else:
        original_filename = filename

    try:
        extraction_data = extraction_service.extract_from_file(
            file_path=staged_path,
            original_filename=original_filename,
            resume_id=resume_id,
        )

        # Cache extraction result for preview to prevent redundant extraction
        preview_service.cache_extraction(resume_id, extraction_data)

        msg = (
            "Resume text extracted successfully"
            if extraction_data.extraction_status == ExtractionStatus.SUCCESS
            else f"Extraction completed with status: {extraction_data.extraction_status.value}"
        )

        return ExtractionResponse(
            success=True,
            message=msg,
            data=extraction_data,
        )

    except Exception as exc:
        logger.error("Failed to extract text from resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract resume text: {str(exc)}",
        )


@router.post(
    "/{resume_id}/clean",
    response_model=CleaningResponse,
    status_code=status.HTTP_200_OK,
    summary="Clean and normalize extracted resume text",
    description="Transforms extracted resume text into a normalized representation while preserving technical terms, symbols, and dates.",
)
async def clean_resume(
    resume_id: str,
    body: CleanRequest = None,
) -> CleaningResponse:
    """
    Cleans raw text for a resume. If body.raw_text is not provided, extracts
    the text from the staged resume file first, then applies the cleaning pipeline.
    """
    raw_text = body.raw_text if body else None
    extraction_id = body.extraction_id if body else None

    # If raw_text wasn't directly supplied in the request body, extract from staged file
    if raw_text is None:
        staged_path = staging_service.get_staged_path(resume_id)
        if not staged_path or not staged_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume file not found or staging expired for ID: {resume_id}",
            )

        filename = staged_path.name
        original_filename = filename.split("_", 1)[1] if "_" in filename else filename

        try:
            extraction_data = extraction_service.extract_from_file(
                file_path=staged_path,
                original_filename=original_filename,
                resume_id=resume_id,
            )
            raw_text = extraction_data.raw_text
            extraction_id = extraction_data.extraction_id
        except Exception as exc:
            logger.error("Failed to extract text prior to cleaning for %s: %s", resume_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract text from resume: {str(exc)}",
            )

    try:
        cleaning_data = cleaning_service.clean_text(
            raw_text=raw_text,
            resume_id=resume_id,
            extraction_id=extraction_id,
        )

        # Cache cleaning result for preview to prevent redundant processing
        preview_service.cache_cleaning(resume_id, cleaning_data)

        msg = (
            "Resume text cleaned successfully"
            if cleaning_data.cleaning_status != CleaningStatus.EMPTY_INPUT
            else "Cleaning completed: empty input"
        )

        return CleaningResponse(
            success=True,
            message=msg,
            data=cleaning_data,
        )
    except Exception as exc:
        logger.error("Failed to clean resume text for %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clean resume text: {str(exc)}",
        )


@router.get(
    "/{resume_id}/preview",
    response_model=ResumePreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get resume preview data",
    description="Returns cleaned resume text, structured blocks, file metadata, and preview status.",
)
async def get_resume_preview(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ResumePreviewResponse:
    """
    Retrieves or compiles preview data for a staged or permanently stored resume document.
    Reuses existing Feature 3 extraction and Feature 4 cleaning outputs,
    preventing unnecessary duplicate extraction or cleaning operations.
    """
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id, allow_non_uuid=True)

    try:
        preview_data = preview_service.get_preview(resume_id, db=db)
        return ResumePreviewResponse(
            success=True,
            message="Resume preview loaded successfully",
            data=preview_data,
        )
    except FileNotFoundError as fnf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(fnf),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to load resume preview for %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate resume preview.",
        )


def _to_stored_resume_data(resume: Resume) -> StoredResumeData:
    versions_data = [
        ResumeVersionData(
            id=str(v.id),
            resume_id=str(v.resume_id),
            version_number=v.version_number,
            storage_key=v.storage_key,
            extracted_text=v.extracted_text,
            cleaned_text=v.cleaned_text,
            created_at=v.created_at.isoformat() if v.created_at else "",
        )
        for v in (resume.versions or [])
    ]
    current_ver = resume.versions[0].version_number if resume.versions else 1
    return StoredResumeData(
        id=str(resume.id),
        user_id=str(resume.user_id) if resume.user_id else None,
        original_filename=resume.original_filename,
        storage_key=resume.storage_key,
        file_type=resume.file_type,
        file_size=resume.file_size,
        processing_status=resume.processing_status,
        current_version=current_ver,
        created_at=resume.created_at.isoformat() if resume.created_at else "",
        updated_at=resume.updated_at.isoformat() if resume.updated_at else "",
        versions=versions_data,
    )


@router.get(
    "",
    response_model=ResumeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List stored resumes",
    description="Retrieves all permanently stored resumes for a user or system.",
)
def list_resumes(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> ResumeListResponse:
    query = select(Resume).order_by(Resume.created_at.desc())
    if user_id:
        try:
            uid = uuid.UUID(user_id)
            query = query.where(Resume.user_id == uid)
        except ValueError:
            pass

    records = db.execute(query).scalars().all()
    items = [_to_stored_resume_data(r) for r in records]
    return ResumeListResponse(
        success=True,
        message="Resumes retrieved successfully",
        data=items,
        total=len(items),
    )


@router.post(
    "/{resume_id}/save",
    response_model=SaveResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a staged resume to permanent storage and database",
    description="Transitions a validated staged resume to permanent storage, associates user ownership, and records version metadata.",
)
def save_resume(
    resume_id: str,
    payload: Optional[SaveResumeRequest] = None,
    db: Session = Depends(get_db),
) -> SaveResumeResponse:
    if not resume_id or ".." in resume_id or "/" in resume_id or "\\" in resume_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume identifier.",
        )

    staged_path = staging_service.get_staged_path(resume_id)
    if not staged_path or not staged_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staged resume not found or expired for ID: {resume_id}",
        )

    # 1. Resolve preview / extracted & cleaned text
    preview_data = preview_service.get_preview(resume_id)
    extracted_text = preview_data.raw_text
    cleaned_text = preview_data.cleaned_text

    # 2. Resolve user association if user_id or user_email provided
    user_record = None
    if payload and payload.user_id:
        try:
            uid = uuid.UUID(payload.user_id)
            user_record = db.execute(select(User).where(User.id == uid)).scalar_one_or_none()
            if not user_record:
                email = payload.user_email.strip().lower() if payload.user_email else f"user_{str(uid)[:8]}@example.com"
                user_record = User(id=uid, email=email)
                db.add(user_record)
                db.flush()
        except ValueError:
            pass
    elif payload and payload.user_email:
        user_record = db.execute(
            select(User).where(User.email == payload.user_email.strip().lower())
        ).scalar_one_or_none()
        if not user_record:
            # Auto-provision user if needed
            user_record = User(email=payload.user_email.strip().lower())
            db.add(user_record)
            db.flush()

    # 3. Check if resume already exists (to bump version)
    parsed_uuid = None
    try:
        parsed_uuid = uuid.UUID(resume_id)
    except ValueError:
        parsed_uuid = uuid.uuid4()

    existing_resume = db.execute(
        select(Resume).where(Resume.id == parsed_uuid)
    ).scalar_one_or_none()

    if existing_resume:
        # If user record was resolved, update ownership
        if user_record:
            existing_resume.user_id = user_record.id

        # If freshly auto-persisted at upload and has 1 version, update user association and return version 1
        if len(existing_resume.versions) == 1 and existing_resume.storage_key:
            db.commit()
            db.refresh(existing_resume)
            return SaveResumeResponse(
                success=True,
                message="Resume saved successfully",
                data=_to_stored_resume_data(existing_resume),
            )

        version_num = (
            max([v.version_number for v in existing_resume.versions], default=0) + 1
        )
        storage_key, _ = permanent_storage.persist_staged_file(
            staged_path, str(existing_resume.id), version=version_num
        )
        existing_resume.storage_key = storage_key
        existing_resume.file_size = staged_path.stat().st_size
        existing_resume.updated_at = func.now()

        version_record = ResumeVersion(
            resume_id=existing_resume.id,
            version_number=version_num,
            storage_key=storage_key,
            extracted_text=extracted_text,
            cleaned_text=cleaned_text,
        )
        db.add(version_record)
        db.commit()
        db.refresh(existing_resume)
        return SaveResumeResponse(
            success=True,
            message=f"Resume updated to version {version_num}",
            data=_to_stored_resume_data(existing_resume),
        )

    # 4. Create new Resume and initial Version
    storage_key, _ = permanent_storage.persist_staged_file(
        staged_path, str(parsed_uuid), version=1
    )

    new_resume = Resume(
        id=parsed_uuid,
        user_id=user_record.id if user_record else None,
        original_filename=preview_data.original_filename,
        storage_key=storage_key,
        file_type=preview_data.file_type,
        file_size=preview_data.file_size,
        processing_status="COMPLETED",
    )
    db.add(new_resume)
    db.flush()

    version_record = ResumeVersion(
        resume_id=new_resume.id,
        version_number=1,
        storage_key=storage_key,
        extracted_text=extracted_text,
        cleaned_text=cleaned_text,
    )
    db.add(version_record)
    db.commit()
    db.refresh(new_resume)

    return SaveResumeResponse(
        success=True,
        message="Resume saved successfully",
        data=_to_stored_resume_data(new_resume),
    )


@router.get(
    "/{resume_id}",
    response_model=StoredResumeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get stored resume details and versions",
)
def get_stored_resume(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> StoredResumeDetailResponse:
    resume = verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id, allow_staging=False)

    return StoredResumeDetailResponse(
        success=True,
        message="Resume retrieved successfully",
        data=_to_stored_resume_data(resume),
    )


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a stored resume and its associated files",
)
def delete_stored_resume(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    resume = verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id, allow_staging=False)
    uid = resume.id

    # Delete DB records
    db.delete(resume)
    db.commit()

    # Delete permanent storage files
    permanent_storage.delete_resume_files(str(uid))

    # Delete lingering staging file if any
    staging_service.cleanup_file(str(uid))

    return {
        "success": True,
        "message": f"Resume {resume_id} and associated versions deleted successfully",
    }


@router.get(
    "/{resume_id}/file",
    summary="Access original uploaded resume document securely",
    description="Streams the original resume document (from permanent storage or staging) with appropriate disposition.",
)
async def get_resume_file(
    resume_id: str,
    download: bool = False,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """
    Provides secure access to the original uploaded document (PDF or DOCX).
    Checks permanent storage first; falls back to staging if un-saved.
    Never exposes internal server filesystem paths to the client.
    """
    verify_resume_access(
        resume_id,
        db,
        user_id=user_id,
        x_user_id=x_user_id,
        allow_staging=True,
        allow_non_uuid=True,
    )

    file_path = None
    original_filename = "resume"

    # 1. Check permanent database record
    try:
        uid = uuid.UUID(resume_id)
        stored_resume = db.execute(select(Resume).where(Resume.id == uid)).scalar_one_or_none()
        if stored_resume:
            perm_path = permanent_storage.get_storage_path(stored_resume.storage_key)
            if perm_path and perm_path.exists() and perm_path.is_file():
                file_path = perm_path
                original_filename = stored_resume.original_filename
    except ValueError:
        pass

    # 2. Fall back to staging if not in permanent storage
    if not file_path:
        staged_path = staging_service.get_staged_path(resume_id)
        if staged_path and staged_path.exists() and staged_path.is_file():
            file_path = staged_path
            filename = staged_path.name
            original_filename = filename.split("_", 1)[1] if "_" in filename else filename

    if not file_path or not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume file not found or staging expired for ID: {resume_id}",
        )

    safe_download_name = original_filename.replace('"', '').replace(';', '').strip()
    if not safe_download_name:
        safe_download_name = f"resume_{resume_id}{file_path.suffix}"

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        media_type = "application/pdf"
        disposition = "attachment" if download else "inline"
    elif suffix == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        disposition = "attachment"
    else:
        media_type = "application/octet-stream"
        disposition = "attachment"

    headers = {
        "Content-Disposition": f'{disposition}; filename="{safe_download_name}"',
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, max-age=300",
    }

    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers=headers,
    )



