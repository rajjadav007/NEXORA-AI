"""
Service layer for Resume Improvement Recommendations
Phase 4 | Feature 27: Resume Improvement Recommendations
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.resume import Resume
from app.models.recommendations import ResumeRecommendationAnalysis
from app.services.recommendations.workflow import recommendation_graph
from app.services.recommendations.categories import normalize_category_key

logger = logging.getLogger(__name__)


class RecommendationService:
    """Manages generation, retrieval, filtering, and completion state of resume recommendations."""

    async def calculate_recommendations(
        self,
        resume_id: str,
        force_recalculate: bool = False,
        user_id: Optional[str] = None,
        db: Session = None,
    ) -> Dict[str, Any]:
        """
        Runs the 7-stage LangGraph recommendation workflow.
        Returns cached analysis if present and force_recalculate=False.
        """
        try:
            resume_uuid = uuid.UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume ID format: {resume_id}",
            )

        resume = db.execute(select(Resume).where(Resume.id == resume_uuid)).scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found.",
            )

        # Return cached if already exists and not forcing recalculation
        if not force_recalculate:
            existing = db.execute(
                select(ResumeRecommendationAnalysis).where(ResumeRecommendationAnalysis.resume_id == resume_uuid)
            ).scalar_one_or_none()
            if existing:
                logger.info("Returning cached recommendations for resume %s", resume_id)
                return self._format_record(existing)

        # Invoke LangGraph Workflow
        logger.info("Executing LangGraph recommendation workflow for resume %s (force=%s)", resume_id, force_recalculate)
        initial_state = {
            "resume_id": resume_id,
            "user_id": user_id,
            "db": db,
            "force_recalculate": force_recalculate,
        }

        final_state = await recommendation_graph.ainvoke(initial_state)

        if final_state.get("error"):
            logger.error("LangGraph recommendation workflow failed: %s", final_state["error"])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate recommendations: {final_state['error']}",
            )

        result = final_state.get("final_result")
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Workflow completed without producing valid recommendations output.",
            )

        return result

    def get_recommendations(
        self,
        resume_id: str,
        db: Session,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        is_completed: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieves persisted recommendations with optional category, priority, and completion filters."""
        try:
            resume_uuid = uuid.UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume ID format: {resume_id}",
            )

        record = db.execute(
            select(ResumeRecommendationAnalysis).where(ResumeRecommendationAnalysis.resume_id == resume_uuid)
        ).scalar_one_or_none()

        if not record:
            return None

        formatted = self._format_record(record)

        # Apply filters in memory without mutating database
        recs = formatted["recommendations"]
        if category:
            norm_cat = normalize_category_key(category)
            recs = [r for r in recs if r.get("category") == norm_cat]

        if priority:
            prio_clean = priority.strip().capitalize()
            recs = [r for r in recs if r.get("priority") == prio_clean]

        if is_completed is not None:
            recs = [r for r in recs if bool(r.get("is_completed")) == bool(is_completed)]

        formatted["recommendations"] = recs
        return formatted

    def update_recommendation_status(
        self,
        resume_id: str,
        recommendation_id: str,
        is_completed: bool,
        db: Session,
    ) -> Dict[str, Any]:
        """Marks a recommendation item as completed or reopened, recalculating progress aggregates."""
        try:
            resume_uuid = uuid.UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume ID format: {resume_id}",
            )

        record = db.execute(
            select(ResumeRecommendationAnalysis).where(ResumeRecommendationAnalysis.resume_id == resume_uuid)
        ).scalar_one_or_none()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No recommendations found for resume ID {resume_id}. Please generate recommendations first.",
            )

        import copy
        recs = copy.deepcopy(record.recommendations or [])
        target_item = None

        for item in recs:
            if item.get("id") == recommendation_id or item.get("recommendation_id") == recommendation_id:
                target_item = item
                item["is_completed"] = bool(is_completed)
                item["completion_status"] = "Completed" if is_completed else "Pending"
                item["completed_at"] = datetime.utcnow().isoformat() if is_completed else None
                break

        if not target_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation with ID '{recommendation_id}' not found for resume {resume_id}.",
            )

        # Recalculate aggregates
        total = len(recs)
        completed = sum(1 for r in recs if r.get("is_completed", False))
        pending = total - completed
        pct = round((completed / total * 100.0), 1) if total > 0 else 0.0

        # Update category breakdown counts
        cat_breakdown = copy.deepcopy(record.category_breakdown or {})
        for ckey, cat_data in cat_breakdown.items():
            cat_items = [r for r in recs if r.get("category") == ckey]
            c_comp = sum(1 for r in cat_items if r.get("is_completed", False))
            cat_data["completed_count"] = c_comp
            cat_data["pending_count"] = len(cat_items) - c_comp

        record.recommendations = recs
        record.completed_count = completed
        record.pending_count = pending
        record.completion_percentage = pct
        record.category_breakdown = cat_breakdown

        flag_modified(record, "recommendations")
        flag_modified(record, "category_breakdown")

        db.commit()
        db.refresh(record)

        return {
            "updated_item": target_item,
            "total_count": total,
            "completed_count": completed,
            "pending_count": pending,
            "completion_percentage": pct,
        }

    def _format_record(self, record: ResumeRecommendationAnalysis) -> Dict[str, Any]:
        """Formats SQLAlchemy model instance into standard response dict."""
        return {
            "id": str(record.id),
            "resume_id": str(record.resume_id),
            "user_id": str(record.user_id) if record.user_id else None,
            "overall_summary": record.overall_summary,
            "total_recommendations_count": record.total_recommendations_count,
            "completed_count": record.completed_count,
            "pending_count": record.pending_count,
            "completion_percentage": record.completion_percentage,
            "priority_breakdown": record.priority_breakdown or {},
            "category_breakdown": record.category_breakdown or {},
            "coverage_summary": record.coverage_summary or {},
            "recommendations": record.recommendations or [],
            "analysis_metadata": record.analysis_metadata or {},
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }


# Singleton service instance
recommendation_service = RecommendationService()
