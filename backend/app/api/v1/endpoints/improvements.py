"""
Resume Improvement Tracker API Endpoints
Phase 5 | Feature 30: Resume Improvement Tracker
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.core.security import verify_resume_access
from app.database.session import get_db
from app.schemas.improvement_tracker import (
    ImprovementOverviewResponse,
    ImprovementHistoryResponse,
    ImprovementTasksResponse,
    SingleTaskResponse,
    VersionComparisonResponse,
    UpdateTaskStatusRequest,
)
from app.services.improvements.service import improvement_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{resume_id}/improvements",
    response_model=ImprovementOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Resume Improvement Tracker Overview",
    description="Returns complete aggregated tracker metrics including score comparisons, progress overview, tasks, timeline, and versions.",
)
def get_resume_improvements_overview(
    resume_id: str,
    user_id: Optional[str] = Query(None, description="Optional authenticated user ID query param"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Optional authenticated user ID header"),
    db: Session = Depends(get_db),
) -> ImprovementOverviewResponse:
    """Retrieves full improvement tracking overview for a resume."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = improvement_service.get_improvements_overview(
            resume_id=resume_id,
            db=db,
            user_id=user_id or x_user_id,
        )
        return ImprovementOverviewResponse(
            success=True,
            message="Resume improvement tracking data retrieved successfully",
            data=data,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving improvements overview for resume %s: %s", resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve improvement tracking data: {str(exc)}",
        )


@router.get(
    "/{resume_id}/improvements/history",
    response_model=ImprovementHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Resume Improvement History",
    description="Retrieves chronological analysis snapshots and scores over time.",
)
def get_resume_improvement_history(
    resume_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ImprovementHistoryResponse:
    """Retrieves historical analysis snapshots for a resume."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        history = improvement_service.get_history(resume_id=resume_id, db=db)
        return ImprovementHistoryResponse(
            success=True,
            message="Resume improvement history retrieved successfully",
            data=history,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving improvement history for resume %s: %s", resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve improvement history: {str(exc)}",
        )


@router.get(
    "/{resume_id}/improvements/tasks",
    response_model=ImprovementTasksResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Resume Improvement Tasks",
    description="Retrieves actionable improvement tasks with optional status and priority filtering.",
)
def get_resume_improvement_tasks(
    resume_id: str,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Pending, In Progress, Completed)"),
    priority_filter: Optional[str] = Query(None, alias="priority", description="Filter by priority (High, Medium, Low)"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ImprovementTasksResponse:
    """Retrieves filtered improvement tasks and current task progress metrics."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        data = improvement_service.get_tasks(
            resume_id=resume_id,
            db=db,
            status_filter=status_filter,
            priority_filter=priority_filter,
            user_id=user_id or x_user_id,
        )
        return ImprovementTasksResponse(
            success=True,
            message="Improvement tasks retrieved successfully",
            data=data,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving improvement tasks for resume %s: %s", resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve improvement tasks: {str(exc)}",
        )


@router.patch(
    "/{resume_id}/improvements/tasks/{task_id}",
    response_model=SingleTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Resume Improvement Task Status",
    description="Updates task status (Pending, In Progress, Completed), updates completion date, and records timeline event.",
)
def update_resume_improvement_task(
    resume_id: str,
    task_id: str,
    payload: UpdateTaskStatusRequest,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SingleTaskResponse:
    """Updates status or priority of an individual improvement task."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        updated_task = improvement_service.update_task_status(
            resume_id=resume_id,
            task_id=task_id,
            status_val=payload.status,
            priority_val=payload.priority,
            db=db,
            user_id=user_id or x_user_id,
        )
        return SingleTaskResponse(
            success=True,
            message=f"Improvement task updated to {payload.status}",
            data=updated_task,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error updating improvement task %s for resume %s: %s", task_id, resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update improvement task: {str(exc)}",
        )


@router.get(
    "/{resume_id}/improvements/compare",
    response_model=VersionComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Two Resume Versions",
    description="Compares two versions on metadata, text metrics, score differences, and skill changes.",
)
def compare_resume_versions(
    resume_id: str,
    v1: Optional[int] = Query(None, description="First version number (defaults to previous)"),
    v2: Optional[int] = Query(None, description="Second version number (defaults to latest)"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> VersionComparisonResponse:
    """Performs side-by-side comparison of two resume versions."""
    verify_resume_access(resume_id, db, user_id=user_id, x_user_id=x_user_id)

    try:
        comparison = improvement_service.compare_versions(
            resume_id=resume_id,
            v1_num=v1,
            v2_num=v2,
            db=db,
        )
        return VersionComparisonResponse(
            success=True,
            message="Resume versions compared successfully",
            data=comparison,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error comparing versions for resume %s: %s", resume_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare resume versions: {str(exc)}",
        )
