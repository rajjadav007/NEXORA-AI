"""
Integration Tests for Resume Improvement Tracker Endpoints
Phase 5 | Feature 30: Resume Improvement Tracker
"""

import io
import uuid
import pytest
import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.resume import Resume, ResumeVersion
from app.models.user import User
from app.models.quality_score import ResumeQualityScore
from app.models.ats_analysis import ResumeATSAnalysis
from app.models.grammar_analysis import ResumeGrammarAnalysis
from app.models.recommendations import ResumeRecommendationAnalysis
from app.models.improvement_tracker import (
    ResumeAnalysisSnapshot,
    ResumeImprovementTask,
    ResumeTimelineEvent,
)

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_pdf_bytes(title: str = "Alex Morgan", text_extra: str = "") -> bytes:
    """Generates a sample PDF resume for testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), title)
    page.insert_text((50, 70), "alex.morgan@example.com | (555) 123-4567 | San Francisco, CA")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "Software Engineer with 4 years experience in Python, FastAPI, and React.")
    page.insert_text((50, 145), "EXPERIENCE")
    page.insert_text((50, 160), "Software Developer - TechCorp (2021 - Present)")
    page.insert_text((50, 175), "- Developed cloud microservices processing 10k requests/min.")
    if text_extra:
        page.insert_text((50, 195), text_extra)
    page.insert_text((50, 225), "SKILLS")
    page.insert_text((50, 240), "Python, FastAPI, PostgreSQL, Docker, React, TypeScript")

    stream = doc.write()
    doc.close()
    return stream


def _upload_resume(filename: str = "alex_resume.pdf", text_extra: str = "") -> str:
    """Uploads and saves a resume, returning its permanent resume_id."""
    pdf_bytes = create_sample_pdf_bytes(text_extra=text_extra)
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201, save_res.text
    return save_res.json()["data"]["id"]


def test_improvement_overview_empty_resume():
    """
    Validates that a fresh resume with no analyses returns 200 OK,
    0% completion percentage, empty tasks, empty history, and base timeline.
    """
    resume_id = _upload_resume(filename="fresh_empty_tracker.pdf")

    # Test both versioned and unversioned endpoints
    res1 = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/improvements")
    assert res1.status_code == 200, res1.text
    res2 = client.get(f"/api/resumes/{resume_id}/improvements")
    assert res2.status_code == 200, res2.text

    body = res1.json()
    assert body["success"] is True
    data = body["data"]

    assert data["resume_id"] == resume_id
    assert data["filename"] == "fresh_empty_tracker.pdf"

    # Progress overview: 0% completion when no tasks
    progress = data["progress_overview"]
    assert progress["total_tasks"] == 0
    assert progress["completed_tasks"] == 0
    assert progress["completion_percentage"] == 0.0

    # Score comparison: no previous data
    comp = data["score_comparison"]
    assert comp["overall_score"]["status"] == "no_previous_data"

    # Timeline: contains base RESUME_UPLOADED event
    timeline = data["timeline"]
    assert len(timeline) >= 1
    assert any(e["event_type"] == "RESUME_UPLOADED" for e in timeline)


def test_improvement_history_and_score_comparison():
    """
    Validates historical analysis snapshots and version-over-version score comparisons.
    Ensures that historical snapshots are NOT overwritten.
    """
    resume_id = _upload_resume(filename="score_compare_resume.pdf")

    # Add historical snapshots directly to DB to simulate version 1 and version 2
    db = SessionLocal()
    try:
        resume_uuid = uuid.UUID(resume_id)
        # Snapshot 1 (v1)
        snap1 = ResumeAnalysisSnapshot(
            resume_id=resume_uuid,
            version_number=1,
            overall_score=72.0,
            ats_score=68.0,
            readability_score=75.0,
            category_scores={"technical_skills": {"score": 70.0}},
            strengths_count=3,
            weaknesses_count=4,
        )
        # Snapshot 2 (v2) - improved
        snap2 = ResumeAnalysisSnapshot(
            resume_id=resume_uuid,
            version_number=2,
            overall_score=85.0,
            ats_score=82.0,
            readability_score=75.0,
            category_scores={"technical_skills": {"score": 85.0}},
            strengths_count=5,
            weaknesses_count=2,
        )
        db.add_all([snap1, snap2])
        db.commit()
    finally:
        db.close()

    # Query history endpoint
    res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/improvements/history")
    assert res.status_code == 200, res.text
    history = res.json()["data"]
    assert len(history) == 2
    assert history[0]["version_number"] == 1
    assert history[0]["overall_score"] == 72.0
    assert history[1]["version_number"] == 2
    assert history[1]["overall_score"] == 85.0

    # Query overview endpoint for score comparisons
    res_ov = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/improvements")
    assert res_ov.status_code == 200
    ov_data = res_ov.json()["data"]
    comp = ov_data["score_comparison"]

    # Overall score: 72 -> 85 (improved +13.0)
    assert comp["overall_score"]["previous_score"] == 72.0
    assert comp["overall_score"]["latest_score"] == 85.0
    assert comp["overall_score"]["delta"] == 13.0
    assert comp["overall_score"]["status"] == "improved"

    # ATS score: 68 -> 82 (improved +14.0)
    assert comp["ats_compatibility"]["previous_score"] == 68.0
    assert comp["ats_compatibility"]["latest_score"] == 82.0
    assert comp["ats_compatibility"]["delta"] == 14.0
    assert comp["ats_compatibility"]["status"] == "improved"

    # Readability: 75 -> 75 (unchanged 0.0)
    assert comp["readability"]["previous_score"] == 75.0
    assert comp["readability"]["latest_score"] == 75.0
    assert comp["readability"]["delta"] == 0.0
    assert comp["readability"]["status"] == "unchanged"


def test_improvement_tasks_creation_and_status_tracking():
    """
    Tests task creation from recommendations, status transition (Pending -> In Progress -> Completed -> Reopened),
    priority and status filtering, and task completion percentage formula.
    """
    resume_id = _upload_resume(filename="task_tracking_resume.pdf")

    # Add recommendations to DB for this resume
    db = SessionLocal()
    try:
        resume_uuid = uuid.UUID(resume_id)
        rec_analysis = ResumeRecommendationAnalysis(
            resume_id=resume_uuid,
            total_recommendations_count=2,
            completed_count=0,
            pending_count=2,
            completion_percentage=0.0,
            recommendations=[
                {
                    "id": "rec-101",
                    "title": "Add Quantifiable Metrics to Experience",
                    "category": "experience_impact",
                    "category_name": "Work Experience",
                    "explanation": "Include percentages and revenue metrics in bullet points.",
                    "suggested_action": "Add specific KPIs and numbers to recent role.",
                    "priority": "High",
                    "is_completed": False,
                },
                {
                    "id": "rec-102",
                    "title": "Include AWS Certifications",
                    "category": "certifications",
                    "category_name": "Certifications",
                    "explanation": "Mention completed cloud certificates.",
                    "suggested_action": "Add AWS Solutions Architect certificate.",
                    "priority": "Medium",
                    "is_completed": False,
                },
            ],
        )
        db.add(rec_analysis)
        db.commit()
    finally:
        db.close()

    # 1. Fetch tasks
    res_tasks = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/improvements/tasks")
    assert res_tasks.status_code == 200, res_tasks.text
    tasks_data = res_tasks.json()["data"]
    tasks = tasks_data["tasks"]
    assert len(tasks) == 2
    assert tasks_data["progress"]["total_tasks"] == 2
    assert tasks_data["progress"]["completed_tasks"] == 0
    assert tasks_data["progress"]["completion_percentage"] == 0.0

    task1 = next(t for t in tasks if "Metrics" in t["title"])
    task2 = next(t for t in tasks if "AWS" in t["title"])
    task1_id = task1["id"]

    # 2. Update task1 to "In Progress"
    patch_res = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/improvements/tasks/{task1_id}",
        json={"status": "In Progress"},
    )
    assert patch_res.status_code == 200, patch_res.text
    assert patch_res.json()["data"]["status"] == "In Progress"
    assert patch_res.json()["data"]["completed_at"] is None

    # 3. Mark task1 as "Completed"
    patch_res2 = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/improvements/tasks/{task1_id}",
        json={"status": "Completed"},
    )
    assert patch_res2.status_code == 200, patch_res2.text
    assert patch_res2.json()["data"]["status"] == "Completed"
    assert patch_res2.json()["data"]["completed_at"] is not None

    # Verify completion percentage: (1 / 2) * 100 = 50.0%
    res_tasks2 = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/improvements/tasks")
    prog = res_tasks2.json()["data"]["progress"]
    assert prog["completed_tasks"] == 1
    assert prog["pending_tasks"] == 1
    assert prog["completion_percentage"] == 50.0

    # 4. Filter by status: status=Completed
    res_filtered = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/improvements/tasks?status=Completed")
    assert res_filtered.status_code == 200
    filtered_tasks = res_filtered.json()["data"]["tasks"]
    assert len(filtered_tasks) == 1
    assert filtered_tasks[0]["id"] == task1_id

    # 5. Filter by priority: priority=Medium
    res_prio = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/improvements/tasks?priority=Medium")
    assert res_prio.status_code == 200
    prio_tasks = res_prio.json()["data"]["tasks"]
    assert len(prio_tasks) == 1
    assert prio_tasks[0]["id"] == task2["id"]

    # 6. Reopen completed task: Completed -> Pending
    patch_reopen = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/improvements/tasks/{task1_id}",
        json={"status": "Pending"},
    )
    assert patch_reopen.status_code == 200
    assert patch_reopen.json()["data"]["status"] == "Pending"
    assert patch_reopen.json()["data"]["completed_at"] is None

    # Completion percentage is back to 0.0%
    res_tasks3 = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/improvements/tasks")
    assert res_tasks3.json()["data"]["progress"]["completion_percentage"] == 0.0


def test_resume_version_comparison():
    """
    Tests version comparison endpoint between two resume versions.
    Verifies metadata, word/character changes, skill changes, and score diffs.
    """
    resume_id = _upload_resume(filename="version_test_v1.pdf")

    # Add a second version to this resume
    db = SessionLocal()
    try:
        resume_uuid = uuid.UUID(resume_id)
        v2 = ResumeVersion(
            resume_id=resume_uuid,
            version_number=2,
            storage_key="storage/resumes/v2_version_test.pdf",
            extracted_text="Alex Morgan\nSenior Software Architect\nSkills: Python, FastAPI, Docker, Kubernetes, Rust, GraphQL",
            cleaned_text="Alex Morgan\nSenior Software Architect\nSkills: Python, FastAPI, Docker, Kubernetes, Rust, GraphQL",
        )
        snap1 = ResumeAnalysisSnapshot(
            resume_id=resume_uuid,
            version_number=1,
            overall_score=70.0,
            ats_score=65.0,
            readability_score=72.0,
        )
        snap2 = ResumeAnalysisSnapshot(
            resume_id=resume_uuid,
            version_number=2,
            overall_score=88.0,
            ats_score=85.0,
            readability_score=80.0,
        )
        db.add_all([v2, snap1, snap2])
        db.commit()
    finally:
        db.close()

    # Call compare endpoint
    res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/improvements/compare?v1=1&v2=2")
    assert res.status_code == 200, res.text
    comp = res.json()["data"]

    assert comp["version_1"]["version_number"] == 1
    assert comp["version_2"]["version_number"] == 2

    # Scores
    score_comp = comp["score_comparison"]
    assert score_comp["overall_score"]["delta"] == 18.0
    assert score_comp["overall_score"]["status"] == "improved"
    assert score_comp["ats_compatibility"]["delta"] == 20.0
    assert score_comp["ats_compatibility"]["status"] == "improved"

    # Content stats
    content = comp["content_changes"]
    assert "word_count_diff" in content
    assert "line_count_diff" in content
    assert "summary" in content


def test_unauthorized_cross_user_access_prevention():
    """
    Verifies that a user cannot access another user's improvement tracker.
    Returns 403 Forbidden.
    """
    db = SessionLocal()
    owner_id = str(uuid.uuid4())
    attacker_id = str(uuid.uuid4())
    try:
        # Create user
        owner_user = User(
            id=uuid.UUID(owner_id),
            email=f"owner_{uuid.uuid4().hex[:6]}@example.com",
        )
        resume_record = Resume(
            id=uuid.uuid4(),
            user_id=uuid.UUID(owner_id),
            original_filename="private_owner_resume.pdf",
            storage_key="storage/resumes/private.pdf",
            file_type="pdf",
            file_size=1024,
            processing_status="COMPLETED",
        )
        db.add_all([owner_user, resume_record])
        db.commit()
        res_id = str(resume_record.id)
    finally:
        db.close()

    # Attacker tries to access owner's improvement data
    res_forbidden = client.get(
        f"{RESUMES_ENDPOINT}/{res_id}/improvements",
        headers={"X-User-Id": attacker_id},
    )
    assert res_forbidden.status_code == 403, res_forbidden.text

    # Owner accesses successfully
    res_allowed = client.get(
        f"{RESUMES_ENDPOINT}/{res_id}/improvements",
        headers={"X-User-Id": owner_id},
    )
    assert res_allowed.status_code == 200, res_allowed.text
