"""
Project Intelligence API Endpoints
Phase 3 | Feature 18: Project Intelligence
"""

import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.resume import Resume
from app.core.security import verify_resume_access, validate_resume_id
from app.schemas.projects import (
    ProjectListResponse,
    ProjectSingleResponse,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectConfirmRequest,
    ProjectSummaryData,
    ProjectSkillLinkData,
)
from app.services.projects.service import project_intelligence_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_resume_id(resume_id: str) -> uuid.UUID:
    return validate_resume_id(resume_id)


@router.post(
    "/{resume_id}/projects/extract",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract and analyze candidate projects from resume",
    description="Parses projects, extracts technologies, links Feature #17 canonical skills, and structures narratives.",
)
async def extract_projects(
    resume_id: str,
    reprocess: bool = Query(False, description="Whether to re-run extraction"),
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits on reprocess"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        projects = await project_intelligence_service.extract_and_structure_projects(
            resume_id=resume_id,
            reprocess=reprocess,
            force_overwrite=force_overwrite,
            db=db,
        )
        summary = project_intelligence_service.get_project_summary(resume_id, db)
        return ProjectListResponse(
            success=True,
            message="Projects extracted and structured successfully",
            data=projects,
            summary=summary,
            total=len(projects),
            extraction_status="completed",
        )
    except Exception as exc:
        logger.error("Failed to extract projects for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract projects: {str(exc)}",
        )


@router.get(
    "/{resume_id}/projects",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all projects for a resume",
    description="Retrieves structured project intelligence records and summary analytics.",
)
def get_projects(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    projects = project_intelligence_service.get_projects(resume_id, db)
    summary = project_intelligence_service.get_project_summary(resume_id, db)
    return ProjectListResponse(
        success=True,
        message="Projects retrieved successfully",
        data=projects,
        summary=summary,
        total=len(projects),
        extraction_status="completed",
    )


@router.get(
    "/{resume_id}/projects/summary",
    response_model=ProjectSummaryData,
    status_code=status.HTTP_200_OK,
    summary="Get project analytics summary",
    description="Returns aggregate counts: categories, domains, unique technologies, links, etc.",
)
def get_project_summary(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ProjectSummaryData:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    return project_intelligence_service.get_project_summary(resume_id, db)


@router.get(
    "/{resume_id}/projects/pending-reviews",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get projects requiring review",
    description="Returns projects with pending review status.",
)
def get_pending_reviews(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    projects = project_intelligence_service.get_projects(resume_id, db)
    pending = [p for p in projects if p.review_status == "pending" or p.review_status == "needs_review"]
    return ProjectListResponse(
        success=True,
        message="Pending review projects retrieved",
        data=pending,
        total=len(pending),
        extraction_status="completed",
    )


@router.get(
    "/{resume_id}/projects/{project_id}",
    response_model=ProjectSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single project details",
)
def get_project_by_id(
    resume_id: str,
    project_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ProjectSingleResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    project = project_intelligence_service.get_project_by_id(resume_id, project_id, db)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return ProjectSingleResponse(success=True, message="Project retrieved", data=project)


@router.get(
    "/{resume_id}/projects/{project_id}/skills",
    response_model=List[ProjectSkillLinkData],
    status_code=status.HTTP_200_OK,
    summary="Get linked canonical skills for a project",
)
def get_project_skills(
    resume_id: str,
    project_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> List[ProjectSkillLinkData]:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    project = project_intelligence_service.get_project_by_id(resume_id, project_id, db)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return project.skills


@router.post(
    "/{resume_id}/projects",
    response_model=ProjectSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a project entry manually",
)
def add_project(
    resume_id: str,
    payload: ProjectCreateRequest,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ProjectSingleResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    entry = project_intelligence_service.add_project_manually(resume_id, payload, db)
    return ProjectSingleResponse(success=True, message="Project created successfully", data=entry)


@router.patch(
    "/{resume_id}/projects/{project_id}",
    response_model=ProjectSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update project information",
)
def update_project(
    resume_id: str,
    project_id: str,
    payload: ProjectUpdateRequest,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ProjectSingleResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    updated = project_intelligence_service.update_project_manually(resume_id, project_id, payload, db)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return ProjectSingleResponse(success=True, message="Project updated successfully", data=updated)


@router.post(
    "/{resume_id}/projects/{project_id}/confirm",
    response_model=ProjectSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm extracted project",
)
def confirm_project(
    resume_id: str,
    project_id: str,
    payload: Optional[ProjectConfirmRequest] = None,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ProjectSingleResponse:
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    confirmed = project_intelligence_service.confirm_project(resume_id, project_id, db)
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return ProjectSingleResponse(success=True, message="Project confirmed", data=confirmed)


@router.delete(
    "/{resume_id}/projects/{project_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete project",
)
def delete_project(
    resume_id: str,
    project_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)
    deleted = project_intelligence_service.delete_project(resume_id, project_id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return {"success": True, "message": "Project deleted successfully"}


@router.post(
    "/{resume_id}/projects/reprocess",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocess project extraction",
    description="Re-runs project extraction while preserving manual user edits.",
)
async def reprocess_projects(
    resume_id: str,
    force_overwrite: bool = Query(False, description="Whether to overwrite manual edits"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    return await extract_projects(
        resume_id=resume_id,
        reprocess=True,
        force_overwrite=force_overwrite,
        user_id=user_id,
        x_user_id=x_user_id,
        db=db,
    )
