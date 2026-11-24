"""
Resume Improvement Tracker Aggregation & Orchestration Service
Phase 5 | Feature 30: Resume Improvement Tracker
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.models.resume import Resume, ResumeVersion
from app.models.quality_score import ResumeQualityScore
from app.models.ats_analysis import ResumeATSAnalysis
from app.models.grammar_analysis import ResumeGrammarAnalysis
from app.models.strength_analysis import ResumeStrengthAnalysis
from app.models.weakness_analysis import ResumeWeaknessAnalysis
from app.models.recommendations import ResumeRecommendationAnalysis
from app.models.skills import ResumeSkill
from app.models.improvement_tracker import (
    ResumeAnalysisSnapshot,
    ResumeImprovementTask,
    ResumeTimelineEvent,
)

logger = logging.getLogger(__name__)

VALID_STATUSES = ["Pending", "In Progress", "Completed"]
VALID_PRIORITIES = ["High", "Medium", "Low"]


class ResumeImprovementService:
    """
    Coordinates historical analysis snapshots, score comparisons,
    actionable improvement task tracking, and resume version comparisons.
    """

    def record_snapshot_if_needed(
        self,
        resume: Resume,
        db: Session,
        force_snapshot: bool = False,
    ) -> Optional[ResumeAnalysisSnapshot]:
        """
        Records a snapshot of current analysis results for the active version.
        Never overwrites prior historical snapshots.
        """
        # Determine active version number
        version_num = 1
        version_id = None
        if resume.versions:
            # resume.versions is ordered by version_number desc
            active_version = max(resume.versions, key=lambda v: v.version_number)
            version_num = active_version.version_number
            version_id = active_version.id

        quality: Optional[ResumeQualityScore] = resume.quality_score
        if not quality and not force_snapshot:
            return None

        # Check existing snapshot for this version
        existing_snapshot = db.execute(
            select(ResumeAnalysisSnapshot)
            .where(
                and_(
                    ResumeAnalysisSnapshot.resume_id == resume.id,
                    ResumeAnalysisSnapshot.version_number == version_num,
                )
            )
            .order_by(ResumeAnalysisSnapshot.created_at.desc())
        ).scalars().first()

        overall_score = quality.overall_score if quality else None
        ats_score = resume.ats_analysis.overall_score if resume.ats_analysis else None
        readability_score = (
            resume.grammar_analysis.overall_readability_score
            if resume.grammar_analysis
            else None
        )
        cat_scores = quality.category_scores if (quality and quality.category_scores) else {}
        strengths_count = (
            len(resume.strength_analysis.strengths)
            if (resume.strength_analysis and resume.strength_analysis.strengths)
            else (len(quality.strengths) if quality and quality.strengths else 0)
        )
        weaknesses_count = (
            len(resume.weakness_analysis.weaknesses)
            if (resume.weakness_analysis and resume.weakness_analysis.weaknesses)
            else (len(quality.missing_information) if quality and quality.missing_information else 0)
        )

        if existing_snapshot:
            # If snapshot exists but had no score and now score is computed, update it
            if existing_snapshot.overall_score is None and overall_score is not None:
                existing_snapshot.overall_score = overall_score
                existing_snapshot.ats_score = ats_score
                existing_snapshot.readability_score = readability_score
                existing_snapshot.category_scores = cat_scores
                existing_snapshot.strengths_count = strengths_count
                existing_snapshot.weaknesses_count = weaknesses_count
                db.commit()
                db.refresh(existing_snapshot)
            return existing_snapshot

        # Create new snapshot
        snapshot = ResumeAnalysisSnapshot(
            resume_id=resume.id,
            resume_version_id=version_id,
            version_number=version_num,
            overall_score=overall_score,
            ats_score=ats_score,
            readability_score=readability_score,
            category_scores=cat_scores,
            strengths_count=strengths_count,
            weaknesses_count=weaknesses_count,
            snapshot_metadata={
                "version_number": version_num,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            },
            created_at=quality.created_at if quality else datetime.now(timezone.utc),
        )
        db.add(snapshot)

        # Log timeline event
        event_type = "VERSION_ANALYZED" if version_num > 1 else "RESUME_ANALYZED"
        title = (
            f"Version {version_num} Analyzed"
            if version_num > 1
            else "Resume Quality Evaluated"
        )
        desc = (
            f"Quality score: {overall_score or 0:.1f}/100"
            + (f", ATS: {ats_score:.1f}/100" if ats_score is not None else "")
        )
        evt = ResumeTimelineEvent(
            resume_id=resume.id,
            user_id=resume.user_id,
            event_type=event_type,
            title=title,
            description=desc,
            event_metadata={
                "version_number": version_num,
                "overall_score": overall_score,
                "ats_score": ats_score,
            },
            created_at=snapshot.created_at,
        )
        db.add(evt)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    def ensure_base_timeline_events(self, resume: Resume, db: Session) -> None:
        """
        Guarantees that foundational milestones exist in timeline:
        - RESUME_UPLOADED
        - VERSION_UPLOADED (for versions > 1)
        """
        # 1. Check RESUME_UPLOADED
        has_uploaded = db.execute(
            select(ResumeTimelineEvent)
            .where(
                and_(
                    ResumeTimelineEvent.resume_id == resume.id,
                    ResumeTimelineEvent.event_type == "RESUME_UPLOADED",
                )
            )
        ).scalars().first()

        if not has_uploaded:
            evt = ResumeTimelineEvent(
                resume_id=resume.id,
                user_id=resume.user_id,
                event_type="RESUME_UPLOADED",
                title="Resume Uploaded",
                description=f"File '{resume.original_filename}' uploaded to permanent storage.",
                event_metadata={"filename": resume.original_filename, "file_size": resume.file_size},
                created_at=resume.created_at,
            )
            db.add(evt)
            db.commit()

        # 2. Check higher versions
        if resume.versions and len(resume.versions) > 1:
            for v in resume.versions:
                if v.version_number > 1:
                    has_v_evt = db.execute(
                        select(ResumeTimelineEvent)
                        .where(
                            and_(
                                ResumeTimelineEvent.resume_id == resume.id,
                                ResumeTimelineEvent.event_type == "VERSION_UPLOADED",
                                ResumeTimelineEvent.event_metadata["version_number"].astext == str(v.version_number),
                            )
                        )
                    ).scalars().first()
                    if not has_v_evt:
                        v_evt = ResumeTimelineEvent(
                            resume_id=resume.id,
                            user_id=resume.user_id,
                            event_type="VERSION_UPLOADED",
                            title=f"Resume Version {v.version_number} Uploaded",
                            description=f"New version {v.version_number} saved for comparison and analysis.",
                            event_metadata={"version_number": v.version_number},
                            created_at=v.created_at,
                        )
                        db.add(v_evt)
                        db.commit()

    def sync_tasks_from_recommendations(
        self,
        resume: Resume,
        db: Session,
        user_id: Optional[str] = None,
    ) -> List[ResumeImprovementTask]:
        """
        Extracts actionable tasks from Phase 4 recommendations or weaknesses.
        Avoids creating duplicate tasks.
        """
        created_any = False

        # Source 1: Recommendation Analysis (Feature #27)
        if resume.recommendation_analysis and resume.recommendation_analysis.recommendations:
            for rec in resume.recommendation_analysis.recommendations:
                rec_id = str(rec.get("id") or "")
                if not rec_id:
                    continue

                existing = db.execute(
                    select(ResumeImprovementTask)
                    .where(
                        and_(
                            ResumeImprovementTask.resume_id == resume.id,
                            ResumeImprovementTask.source_recommendation_id == rec_id,
                        )
                    )
                ).scalars().first()

                if not existing:
                    raw_p = (rec.get("priority") or "Medium").capitalize()
                    priority = "High" if raw_p in ["Critical", "Urgent", "High"] else ("Low" if raw_p == "Low" else "Medium")
                    section = rec.get("category_name") or rec.get("category") or "General"
                    title = rec.get("title") or (rec.get("suggested_action", "")[:60] if rec.get("suggested_action") else "Improve Resume Section")
                    description = rec.get("suggested_action") or rec.get("explanation") or ""
                    is_completed = bool(rec.get("is_completed"))

                    task = ResumeImprovementTask(
                        resume_id=resume.id,
                        user_id=resume.user_id,
                        title=title[:255],
                        description=description,
                        section=section[:100],
                        priority=priority,
                        status="Completed" if is_completed else "Pending",
                        source_recommendation_id=rec_id,
                        completed_at=datetime.now(timezone.utc) if is_completed else None,
                    )
                    db.add(task)
                    db.flush()

                    evt = ResumeTimelineEvent(
                        resume_id=resume.id,
                        user_id=resume.user_id,
                        event_type="TASK_CREATED",
                        title=f"Task Created: {title[:40]}",
                        description=f"Improvement task for '{section}' ({priority} priority).",
                        event_metadata={"task_id": str(task.id), "priority": priority, "section": section},
                        created_at=task.created_at,
                    )
                    db.add(evt)
                    created_any = True

        # Source 2: Weakness Analysis fallback if no recommendations yet
        elif resume.weakness_analysis and resume.weakness_analysis.weaknesses:
            for idx, w in enumerate(resume.weakness_analysis.weaknesses):
                w_id = f"weakness-{idx}"
                existing = db.execute(
                    select(ResumeImprovementTask)
                    .where(
                        and_(
                            ResumeImprovementTask.resume_id == resume.id,
                            ResumeImprovementTask.source_recommendation_id == w_id,
                        )
                    )
                ).scalars().first()

                if not existing:
                    raw_sev = (w.get("severity") or "Medium").capitalize()
                    priority = "High" if raw_sev in ["Critical", "High"] else ("Low" if raw_sev == "Low" else "Medium")
                    section = w.get("section") or "General"
                    title = f"Address {section} issue: {w.get('issue', '')[:50]}"
                    description = w.get("recommendation") or w.get("issue") or ""

                    task = ResumeImprovementTask(
                        resume_id=resume.id,
                        user_id=resume.user_id,
                        title=title[:255],
                        description=description,
                        section=section[:100],
                        priority=priority,
                        status="Pending",
                        source_recommendation_id=w_id,
                    )
                    db.add(task)
                    db.flush()

                    evt = ResumeTimelineEvent(
                        resume_id=resume.id,
                        user_id=resume.user_id,
                        event_type="TASK_CREATED",
                        title=f"Task Created: {title[:40]}",
                        description=f"Improvement task for '{section}' ({priority} priority).",
                        event_metadata={"task_id": str(task.id), "priority": priority, "section": section},
                        created_at=task.created_at,
                    )
                    db.add(evt)
                    created_any = True

        # Source 3: Quality score improvement suggestions if available and still 0 tasks
        elif resume.quality_score and resume.quality_score.improvement_suggestions:
            for idx, sug in enumerate(resume.quality_score.improvement_suggestions):
                sug_id = f"quality-sug-{idx}"
                existing = db.execute(
                    select(ResumeImprovementTask)
                    .where(
                        and_(
                            ResumeImprovementTask.resume_id == resume.id,
                            ResumeImprovementTask.source_recommendation_id == sug_id,
                        )
                    )
                ).scalars().first()

                if not existing:
                    title = f"Quality Improvement: {sug[:50]}"
                    task = ResumeImprovementTask(
                        resume_id=resume.id,
                        user_id=resume.user_id,
                        title=title[:255],
                        description=sug,
                        section="Quality",
                        priority="Medium",
                        status="Pending",
                        source_recommendation_id=sug_id,
                    )
                    db.add(task)
                    db.flush()
                    created_any = True

        if created_any:
            db.commit()

        # Query all tasks for this resume
        return db.execute(
            select(ResumeImprovementTask)
            .where(ResumeImprovementTask.resume_id == resume.id)
            .order_by(
                ResumeImprovementTask.status.asc(),
                ResumeImprovementTask.priority.asc(),
                ResumeImprovementTask.created_at.asc(),
            )
        ).scalars().all()

    def get_tasks(
        self,
        resume_id: str,
        db: Session,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves improvement tasks with optional status and priority filtering.
        Calculates task progress overview.
        """
        resume = self._get_resume_with_relations(resume_id, db)
        self.sync_tasks_from_recommendations(resume, db, user_id=user_id)

        query = select(ResumeImprovementTask).where(ResumeImprovementTask.resume_id == resume.id)

        if status_filter:
            # Normalize title case (e.g. 'pending' -> 'Pending')
            norm_status = status_filter.title() if status_filter.lower() in ["pending", "completed"] else (
                "In Progress" if status_filter.lower() in ["in progress", "in_progress", "inprogress"] else status_filter
            )
            query = query.where(ResumeImprovementTask.status == norm_status)

        if priority_filter:
            norm_priority = priority_filter.capitalize()
            query = query.where(ResumeImprovementTask.priority == norm_priority)

        tasks = db.execute(
            query.order_by(
                ResumeImprovementTask.status.asc(),
                ResumeImprovementTask.created_at.asc(),
            )
        ).scalars().all()

        progress = self.get_progress_overview(resume, db)

        tasks_data = [
            {
                "id": str(t.id),
                "resume_id": str(t.resume_id),
                "title": t.title,
                "description": t.description,
                "section": t.section,
                "priority": t.priority,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else "",
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else "",
            }
            for t in tasks
        ]

        return {
            "tasks": tasks_data,
            "progress": progress,
        }

    def update_task_status(
        self,
        resume_id: str,
        task_id: str,
        status_val: str,
        priority_val: Optional[str],
        db: Session,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates task status (Pending, In Progress, Completed), updates completion date,
        logs timeline event, and persists in PostgreSQL.
        """
        resume = self._get_resume_with_relations(resume_id, db)

        try:
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid task ID format: {task_id}",
            )

        task = db.execute(
            select(ResumeImprovementTask).where(
                and_(
                    ResumeImprovementTask.id == task_uuid,
                    ResumeImprovementTask.resume_id == resume.id,
                )
            )
        ).scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Improvement task with ID {task_id} not found.",
            )

        # Normalize and validate status
        norm_status = status_val.title() if status_val.lower() in ["pending", "completed"] else (
            "In Progress" if status_val.lower() in ["in progress", "in_progress", "inprogress"] else status_val
        )
        if norm_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{status_val}'. Must be one of {VALID_STATUSES}.",
            )

        if priority_val:
            norm_priority = priority_val.capitalize()
            if norm_priority not in VALID_PRIORITIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority '{priority_val}'. Must be one of {VALID_PRIORITIES}.",
                )
            task.priority = norm_priority

        prev_status = task.status
        task.status = norm_status
        now = datetime.now(timezone.utc)

        if norm_status == "Completed":
            task.completed_at = now
            evt = ResumeTimelineEvent(
                resume_id=resume.id,
                user_id=resume.user_id,
                event_type="TASK_COMPLETED",
                title=f"Task Completed: {task.title[:40]}",
                description=f"Improvement task '{task.title}' marked as completed.",
                event_metadata={"task_id": str(task.id), "section": task.section},
                created_at=now,
            )
            db.add(evt)
        else:
            task.completed_at = None
            if prev_status == "Completed":
                evt = ResumeTimelineEvent(
                    resume_id=resume.id,
                    user_id=resume.user_id,
                    event_type="TASK_REOPENED",
                    title=f"Task Reopened: {task.title[:40]}",
                    description=f"Improvement task reopened (now {norm_status}).",
                    event_metadata={"task_id": str(task.id), "status": norm_status},
                    created_at=now,
                )
                db.add(evt)
            else:
                evt = ResumeTimelineEvent(
                    resume_id=resume.id,
                    user_id=resume.user_id,
                    event_type="TASK_STATUS_UPDATED",
                    title=f"Task Status Changed: {norm_status}",
                    description=f"Task '{task.title[:40]}' moved to {norm_status}.",
                    event_metadata={"task_id": str(task.id), "status": norm_status},
                    created_at=now,
                )
                db.add(evt)

        db.commit()
        db.refresh(task)

        return {
            "id": str(task.id),
            "resume_id": str(task.resume_id),
            "title": task.title,
            "description": task.description,
            "section": task.section,
            "priority": task.priority,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else "",
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else "",
        }

    def get_score_comparison(
        self,
        resume: Resume,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Compares latest stored scores with previous historical scores.
        Only uses actual stored analysis results.
        Clearly indicates improved, declined, or unchanged.
        """
        self.record_snapshot_if_needed(resume, db)

        snapshots = db.execute(
            select(ResumeAnalysisSnapshot)
            .where(ResumeAnalysisSnapshot.resume_id == resume.id)
            .order_by(
                ResumeAnalysisSnapshot.created_at.asc(),
                ResumeAnalysisSnapshot.version_number.asc(),
            )
        ).scalars().all()

        latest = snapshots[-1] if snapshots else None
        prev = snapshots[-2] if len(snapshots) >= 2 else None

        def _calc_comparison(
            prev_val: Optional[float],
            curr_val: Optional[float],
        ) -> Dict[str, Any]:
            if curr_val is None or prev_val is None:
                return {
                    "previous_score": prev_val,
                    "latest_score": curr_val,
                    "delta": None,
                    "status": "no_previous_data",
                }
            delta = round(curr_val - prev_val, 1)
            if delta > 0:
                status_str = "improved"
            elif delta < 0:
                status_str = "declined"
            else:
                status_str = "unchanged"
            return {
                "previous_score": prev_val,
                "latest_score": curr_val,
                "delta": delta,
                "status": status_str,
            }

        overall_prev = prev.overall_score if prev else None
        overall_curr = latest.overall_score if latest else (
            resume.quality_score.overall_score if resume.quality_score else None
        )

        ats_prev = prev.ats_score if prev else None
        ats_curr = latest.ats_score if latest else (
            resume.ats_analysis.overall_score if resume.ats_analysis else None
        )

        read_prev = prev.readability_score if prev else None
        read_curr = latest.readability_score if latest else (
            resume.grammar_analysis.overall_readability_score if resume.grammar_analysis else None
        )

        # Category comparisons
        cat_comparisons: Dict[str, Any] = {}
        curr_cats = (latest.category_scores if latest else (
            resume.quality_score.category_scores if resume.quality_score else {}
        )) or {}
        prev_cats = (prev.category_scores if prev else {}) or {}

        for k, v in curr_cats.items():
            curr_val = v.get("score") if isinstance(v, dict) else v
            prev_val = prev_cats.get(k, {}).get("score") if isinstance(prev_cats.get(k), dict) else prev_cats.get(k)
            try:
                curr_f = float(curr_val) if curr_val is not None else None
            except (ValueError, TypeError):
                curr_f = None
            try:
                prev_f = float(prev_val) if prev_val is not None else None
            except (ValueError, TypeError):
                prev_f = None

            cat_comparisons[k] = _calc_comparison(prev_f, curr_f)

        return {
            "overall_score": _calc_comparison(overall_prev, overall_curr),
            "ats_compatibility": _calc_comparison(ats_prev, ats_curr),
            "readability": _calc_comparison(read_prev, read_curr),
            "category_comparisons": cat_comparisons,
        }

    def get_progress_overview(self, resume: Resume, db: Session) -> Dict[str, Any]:
        """
        Calculates task completion percentage:
        Completion Percentage = (Completed Tasks / Total Tasks) × 100
        Clearly distinguishes task progress from actual score improvement.
        """
        tasks = db.execute(
            select(ResumeImprovementTask).where(ResumeImprovementTask.resume_id == resume.id)
        ).scalars().all()

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "Completed")
        in_progress = sum(1 for t in tasks if t.status == "In Progress")
        pending = sum(1 for t in tasks if t.status == "Pending")

        completion_pct = round((completed / total) * 100, 1) if total > 0 else 0.0

        # Calculate score delta if history exists
        snapshots = db.execute(
            select(ResumeAnalysisSnapshot)
            .where(ResumeAnalysisSnapshot.resume_id == resume.id)
            .order_by(ResumeAnalysisSnapshot.created_at.asc())
        ).scalars().all()

        score_delta = None
        if len(snapshots) >= 2:
            s_prev = snapshots[-2].overall_score
            s_curr = snapshots[-1].overall_score
            if s_prev is not None and s_curr is not None:
                score_delta = round(s_curr - s_prev, 1)

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "pending_tasks": pending,
            "completion_percentage": completion_pct,
            "score_improvement_delta": score_delta,
        }

    def get_history(self, resume_id: str, db: Session) -> List[Dict[str, Any]]:
        """
        Retrieves chronological history of resume analysis snapshots.
        """
        resume = self._get_resume_with_relations(resume_id, db)
        self.record_snapshot_if_needed(resume, db)

        snapshots = db.execute(
            select(ResumeAnalysisSnapshot)
            .where(ResumeAnalysisSnapshot.resume_id == resume.id)
            .order_by(
                ResumeAnalysisSnapshot.created_at.asc(),
                ResumeAnalysisSnapshot.version_number.asc(),
            )
        ).scalars().all()

        return [
            {
                "id": str(s.id),
                "resume_id": str(s.resume_id),
                "version_number": s.version_number,
                "version_name": f"Version {s.version_number}",
                "overall_score": s.overall_score,
                "ats_score": s.ats_score,
                "readability_score": s.readability_score,
                "category_scores": s.category_scores or {},
                "strengths_count": s.strengths_count,
                "weaknesses_count": s.weaknesses_count,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            }
            for s in snapshots
        ]

    def get_timeline(self, resume_id: str, db: Session) -> List[Dict[str, Any]]:
        """
        Retrieves chronological timeline displaying:
        - Resume uploaded
        - Resume analyzed
        - Improvement task created
        - Improvement task completed
        - New resume version analyzed
        Using real event timestamps.
        """
        resume = self._get_resume_with_relations(resume_id, db)
        self.ensure_base_timeline_events(resume, db)

        events = db.execute(
            select(ResumeTimelineEvent)
            .where(ResumeTimelineEvent.resume_id == resume.id)
            .order_by(ResumeTimelineEvent.created_at.desc())
        ).scalars().all()

        return [
            {
                "id": str(e.id),
                "resume_id": str(e.resume_id),
                "event_type": e.event_type,
                "title": e.title,
                "description": e.description,
                "event_metadata": e.event_metadata or {},
                "created_at": e.created_at.isoformat() if e.created_at else "",
            }
            for e in events
        ]

    def compare_versions(
        self,
        resume_id: str,
        v1_num: Optional[int],
        v2_num: Optional[int],
        db: Session,
    ) -> Dict[str, Any]:
        """
        Compares two resume versions:
        - Version names, upload dates, analysis dates
        - Available score comparisons
        - Added or removed skills (objective string matching against canonical skills)
        - Important content changes (word count diff, line diff)
        Never claims content improvements based only on score differences.
        """
        resume = self._get_resume_with_relations(resume_id, db)
        self.record_snapshot_if_needed(resume, db)

        all_versions = sorted(resume.versions or [], key=lambda v: v.version_number)
        if not all_versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume versions found for comparison.",
            )

        # Select target versions
        if v1_num is not None and v2_num is not None:
            v1 = next((v for v in all_versions if v.version_number == v1_num), None)
            v2 = next((v for v in all_versions if v.version_number == v2_num), None)
            if not v1 or not v2:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Requested versions ({v1_num}, {v2_num}) not found.",
                )
        elif len(all_versions) >= 2:
            v1 = all_versions[-2]
            v2 = all_versions[-1]
        else:
            # Single version available
            v1 = all_versions[0]
            v2 = all_versions[0]

        # Extract text stats
        t1 = v1.cleaned_text or v1.extracted_text or ""
        t2 = v2.cleaned_text or v2.extracted_text or ""
        w1_words = len(t1.split())
        w2_words = len(t2.split())
        l1_lines = len(t1.splitlines())
        l2_lines = len(t2.splitlines())

        # Skill comparison based on canonical resume skills in database
        skills_db = db.execute(
            select(ResumeSkill).where(ResumeSkill.resume_id == resume.id)
        ).scalars().all()
        canonical_skills = [s.canonical_name for s in skills_db] if skills_db else []

        # If no skills in DB, extract basic capitalized words from text
        if not canonical_skills:
            t1_lower = set(t1.lower().split())
            t2_lower = set(t2.lower().split())
        else:
            t1_lower = {s.lower() for s in canonical_skills if s.lower() in t1.lower()}
            t2_lower = {s.lower() for s in canonical_skills if s.lower() in t2.lower()}

        added_skills = sorted(list(t2_lower - t1_lower))
        removed_skills = sorted(list(t1_lower - t2_lower))
        retained_skills = sorted(list(t1_lower & t2_lower))

        # Query snapshots for these versions
        snap1 = db.execute(
            select(ResumeAnalysisSnapshot).where(
                and_(
                    ResumeAnalysisSnapshot.resume_id == resume.id,
                    ResumeAnalysisSnapshot.version_number == v1.version_number,
                )
            )
        ).scalars().first()

        snap2 = db.execute(
            select(ResumeAnalysisSnapshot).where(
                and_(
                    ResumeAnalysisSnapshot.resume_id == resume.id,
                    ResumeAnalysisSnapshot.version_number == v2.version_number,
                )
            )
        ).scalars().first()

        def _diff_metric(s1_val, s2_val):
            if s1_val is None or s2_val is None:
                return {"previous_score": s1_val, "latest_score": s2_val, "delta": None, "status": "no_previous_data"}
            d = round(s2_val - s1_val, 1)
            status_str = "improved" if d > 0 else ("declined" if d < 0 else "unchanged")
            return {"previous_score": s1_val, "latest_score": s2_val, "delta": d, "status": status_str}

        score_comp = {
            "overall_score": _diff_metric(
                snap1.overall_score if snap1 else None,
                snap2.overall_score if snap2 else None,
            ),
            "ats_compatibility": _diff_metric(
                snap1.ats_score if snap1 else None,
                snap2.ats_score if snap2 else None,
            ),
            "readability": _diff_metric(
                snap1.readability_score if snap1 else None,
                snap2.readability_score if snap2 else None,
            ),
        }

        notes = []
        if v1.version_number == v2.version_number:
            notes.append("Comparing version against itself. Upload a new resume version to view version-over-version diffs.")
        else:
            notes.append("Score deltas reflect evaluation model ratings. Text statistics reflect raw extracted content.")

        return {
            "resume_id": str(resume.id),
            "version_1": {
                "version_number": v1.version_number,
                "version_name": f"Version {v1.version_number}",
                "upload_date": v1.created_at.isoformat() if v1.created_at else "",
                "analysis_date": snap1.created_at.isoformat() if snap1 and snap1.created_at else None,
                "word_count": w1_words,
                "line_count": l1_lines,
                "char_count": len(t1),
            },
            "version_2": {
                "version_number": v2.version_number,
                "version_name": f"Version {v2.version_number}",
                "upload_date": v2.created_at.isoformat() if v2.created_at else "",
                "analysis_date": snap2.created_at.isoformat() if snap2 and snap2.created_at else None,
                "word_count": w2_words,
                "line_count": l2_lines,
                "char_count": len(t2),
            },
            "score_comparison": score_comp,
            "skills_comparison": {
                "added_skills": added_skills,
                "removed_skills": removed_skills,
                "retained_skills": retained_skills,
                "total_retained": len(retained_skills),
                "total_added": len(added_skills),
                "total_removed": len(removed_skills),
            },
            "content_changes": {
                "word_count_diff": w2_words - w1_words,
                "line_count_diff": l2_lines - l1_lines,
                "char_count_diff": len(t2) - len(t1),
                "summary": (
                    f"Word count changed by {w2_words - w1_words:+d} words "
                    f"({w1_words} -> {w2_words}). "
                    f"Identified {len(added_skills)} added skills and {len(removed_skills)} removed skills."
                ),
            },
            "notes": notes,
        }

    def get_improvements_overview(
        self,
        resume_id: str,
        db: Session,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Aggregates complete data payload for Resume Improvement Tracker.
        """
        resume = self._get_resume_with_relations(resume_id, db)
        self.record_snapshot_if_needed(resume, db)
        self.ensure_base_timeline_events(resume, db)
        self.sync_tasks_from_recommendations(resume, db, user_id=user_id)

        score_comp = self.get_score_comparison(resume, db)
        progress = self.get_progress_overview(resume, db)
        history = self.get_history(resume_id, db)
        timeline = self.get_timeline(resume_id, db)

        tasks_res = self.get_tasks(resume_id, db, user_id=user_id)

        available_versions = [
            {
                "version_number": v.version_number,
                "version_name": f"Version {v.version_number}",
                "created_at": v.created_at.isoformat() if v.created_at else "",
            }
            for v in sorted(resume.versions or [], key=lambda x: x.version_number, reverse=True)
        ]

        return {
            "resume_id": str(resume.id),
            "filename": resume.original_filename,
            "score_comparison": score_comp,
            "progress_overview": progress,
            "tasks": tasks_res["tasks"],
            "timeline": timeline,
            "history": history,
            "available_versions": available_versions,
        }

    def _get_resume_with_relations(self, resume_id: str, db: Session) -> Resume:
        """Fetches resume with required joined relations."""
        try:
            resume_uuid = uuid.UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume ID format: {resume_id}",
            )

        resume = db.execute(
            select(Resume)
            .options(
                joinedload(Resume.quality_score),
                joinedload(Resume.ats_analysis),
                joinedload(Resume.grammar_analysis),
                joinedload(Resume.strength_analysis),
                joinedload(Resume.weakness_analysis),
                joinedload(Resume.recommendation_analysis),
                joinedload(Resume.versions),
            )
            .where(Resume.id == resume_uuid)
        ).unique().scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found.",
            )

        return resume


improvement_service = ResumeImprovementService()
