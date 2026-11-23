"""
Integration Tests for Resume Analytics Dashboard Endpoints
Phase 5 | Feature 28: Resume Analytics Dashboard
"""

import io
import uuid
import pytest
import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.resume import Resume
from app.models.user import User

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_analytics_pdf_bytes() -> bytes:
    """Generates a sample PDF resume for testing analytics dashboard."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Maya Patel")
    page.insert_text((50, 70), "maya.patel@example.com | (555) 890-1234 | Austin, TX")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "Senior Cloud Architect with 6 years experience in distributed microservices and AWS.")
    page.insert_text((50, 145), "EXPERIENCE")
    page.insert_text((50, 160), "Lead Cloud Engineer - Apex Cloud (2020 - Present)")
    page.insert_text((50, 175), "- Architected multi-region Kubernetes clusters handling 50k RPS with 99.99% uptime.")
    page.insert_text((50, 190), "- Cut annual AWS compute costs by 32% through spot instances and container rightsizing.")
    page.insert_text((50, 215), "PROJECTS")
    page.insert_text((50, 230), "Distributed Task Queue: High-throughput async scheduler in Python and Redis.")
    page.insert_text((50, 255), "SKILLS")
    page.insert_text((50, 270), "Python, Go, AWS, Docker, Kubernetes, Terraform, PostgreSQL, Redis")
    page.insert_text((50, 295), "EDUCATION")
    page.insert_text((50, 310), "B.S. in Computer Engineering - University of Texas at Austin (2018)")

    stream = doc.write()
    doc.close()
    return stream


def _upload_resume(filename: str = "maya_patel_resume.pdf") -> str:
    """Uploads and saves a resume, returning its permanent resume_id."""
    pdf_bytes = create_sample_analytics_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201, save_res.text
    return save_res.json()["data"]["id"]


def test_analytics_dashboard_empty_resume():
    """
    Validates that a freshly uploaded resume with no Phase 4 analyses
    loads cleanly with 200 OK, empty/un-analyzed status, and zero fake scores.
    """
    resume_id = _upload_resume(filename="fresh_un_analyzed.pdf")

    res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/analytics/dashboard")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # 1. Header assertions
    header = data["resume_header"]
    assert header["resume_id"] == resume_id
    assert header["filename"] == "fresh_un_analyzed.pdf"
    assert header["analysis_status"] == "NOT_ANALYZED"
    assert header["coverage_count"] == 0
    assert header["total_features"] == 6
    assert len(header["available_features"]) == 0
    assert len(header["missing_features"]) == 6

    # 2. Summary cards: all scores null, available=False (NO fake data!)
    cards = data["summary_cards"]
    for card_key in ["quality_score", "ats_compatibility", "readability", "content_completeness"]:
        card = cards[card_key]
        assert card["available"] is False
        assert card["score"] is None
        assert card["grade_or_rating"] == "Not Evaluated"

    # 3. Visual analytics: gracefully empty
    visual = data["visual_analytics"]
    assert len(visual["quality_category_breakdown"]) == 0
    dist = visual["score_distribution"]
    assert len(dist) == 5
    for item in dist:
        assert item["available"] is False
        assert item["score"] is None

    # 4. Insights
    insights = data["resume_insights"]
    assert len(insights["key_strengths"]) == 0
    assert len(insights["important_weaknesses"]) == 0

    assert data["has_any_analysis"] is False


def test_analytics_dashboard_with_analyses():
    """
    Validates full aggregation when Phase 4 analyses are generated.
    """
    resume_id = _upload_resume(filename="analyzed_maya_patel.pdf")

    # Run ATS Compatibility analysis (Feature #24)
    ats_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/ats/analyze")
    assert ats_res.status_code == 200, ats_res.text

    # Run Achievement analysis (Feature #26)
    ach_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/achievements/analyze")
    assert ach_res.status_code == 200, ach_res.text

    # Run Grammar analysis (Feature #25)
    gram_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/grammar/analyze")
    assert gram_res.status_code == 200, gram_res.text

    # Run Recommendations (Feature #27)
    rec_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/recommendations/generate")
    assert rec_res.status_code == 200, rec_res.text

    # Query Dashboard via versioned API
    res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/analytics/dashboard")
    assert res.status_code == 200, res.text
    data = res.json()["data"]

    # Header check
    header = data["resume_header"]
    assert header["coverage_count"] >= 3
    assert header["analysis_status"] in ["PARTIAL", "COMPLETE"]
    assert any("ATS" in f for f in header["available_features"])
    assert any("Achievement" in f for f in header["available_features"])

    # ATS summary card must have genuine score
    ats_card = data["summary_cards"]["ats_compatibility"]
    assert ats_card["available"] is True
    assert ats_card["score"] is not None
    assert ats_card["score"] > 0
    assert ats_card["grade_or_rating"] != "Not Evaluated"

    # Grammar / Readability card must have genuine score
    read_card = data["summary_cards"]["readability"]
    assert read_card["available"] is True
    assert read_card["score"] is not None

    # Visual distribution items
    dist = data["visual_analytics"]["score_distribution"]
    ats_dist = next(d for d in dist if d["metric"] == "ATS Compatibility")
    assert ats_dist["available"] is True
    assert ats_dist["score"] == ats_card["score"]

    # Feature summaries
    feat_summaries = data["resume_insights"]["feature_summaries"]
    assert "ats" in feat_summaries
    assert "achievement" in feat_summaries
    assert "grammar" in feat_summaries
    assert "recommendations" in feat_summaries

    assert data["has_any_analysis"] is True

    # Test unversioned alias endpoint: GET /api/resumes/{resume_id}/analytics/dashboard
    alias_res = client.get(f"/api/resumes/{resume_id}/analytics/dashboard")
    assert alias_res.status_code == 200
    assert alias_res.json()["data"]["resume_id"] == resume_id

    # Test short alias endpoint: GET /api/v1/resumes/{resume_id}/analytics
    short_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/analytics")
    assert short_res.status_code == 200
    assert short_res.json()["data"]["resume_id"] == resume_id


def test_analytics_dashboard_nonexistent_resume():
    """Validates 404 response for nonexistent resume ID."""
    fake_id = str(uuid.uuid4())
    res = client.get(f"{RESUMES_ENDPOINT}/{fake_id}/analytics/dashboard")
    assert res.status_code == 404


def test_analytics_dashboard_invalid_uuid():
    """Validates 400 response for malformed resume ID."""
    res = client.get(f"{RESUMES_ENDPOINT}/not-a-valid-uuid/analytics/dashboard")
    assert res.status_code == 400


def test_analytics_dashboard_unauthorized_access():
    """Validates 403 response when requesting a resume owned by another user."""
    # Create resume with owner user A
    owner_user_id = uuid.uuid4()
    pdf_bytes = create_sample_analytics_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("protected_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201
    resume_id = save_res.json()["data"]["id"]

    # Assign user_id to resume in database
    db = SessionLocal()
    try:
        user_a = User(id=owner_user_id, email=f"user_{uuid.uuid4().hex[:6]}@example.com")
        db.add(user_a)
        resume_record = db.query(Resume).filter(Resume.id == uuid.UUID(resume_id)).first()
        resume_record.user_id = owner_user_id
        db.commit()
    finally:
        db.close()

    # Request with different user B should be rejected with 403 Forbidden
    other_user_id = str(uuid.uuid4())
    forbidden_res = client.get(
        f"{RESUMES_ENDPOINT}/{resume_id}/analytics/dashboard",
        headers={"X-User-Id": other_user_id},
    )
    assert forbidden_res.status_code == 403

    # Request with correct owner user A should succeed with 200 OK
    allowed_res = client.get(
        f"{RESUMES_ENDPOINT}/{resume_id}/analytics/dashboard",
        headers={"X-User-Id": str(owner_user_id)},
    )
    assert allowed_res.status_code == 200


def test_analytics_dashboard_multi_resume_options():
    """Validates that available_resumes dropdown list returns all user's resumes."""
    user_id = uuid.uuid4()

    db = SessionLocal()
    try:
        user = User(id=user_id, email=f"multi_{uuid.uuid4().hex[:6]}@example.com")
        db.add(user)
        db.commit()
    finally:
        db.close()

    # Upload two resumes for this user
    res1_id = _upload_resume(filename="resume_1_backend.pdf")
    res2_id = _upload_resume(filename="resume_2_frontend.pdf")

    db = SessionLocal()
    try:
        r1 = db.query(Resume).filter(Resume.id == uuid.UUID(res1_id)).first()
        r2 = db.query(Resume).filter(Resume.id == uuid.UUID(res2_id)).first()
        r1.user_id = user_id
        r2.user_id = user_id
        db.commit()
    finally:
        db.close()

    res = client.get(
        f"{RESUMES_ENDPOINT}/{res1_id}/analytics/dashboard",
        headers={"X-User-Id": str(user_id)},
    )
    assert res.status_code == 200
    avail = res.json()["data"]["resume_header"]["available_resumes"]
    assert len(avail) >= 2
    ids = [r["id"] for r in avail]
    assert res1_id in ids
    assert res2_id in ids
    active_item = next(r for r in avail if r["id"] == res1_id)
    assert active_item["is_active"] is True
