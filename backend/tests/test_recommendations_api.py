"""
Integration Tests for Resume Improvement Recommendations Endpoints
Phase 4 | Feature 27: Resume Improvement Recommendations
"""

import io
import uuid
import pytest
import fitz
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_recommendation_pdf_bytes() -> bytes:
    """Generates a sample PDF resume for testing recommendations."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "David Chen")
    page.insert_text((50, 70), "david.chen@example.com | (555) 345-6789 | San Francisco, CA")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "Software Engineer with 4 years experience building scalable backend microservices and REST APIs.")
    page.insert_text((50, 145), "WORK EXPERIENCE")
    page.insert_text((50, 160), "Backend Developer - DataPulse Labs (2021 - Present)")
    page.insert_text((50, 175), "- Built REST API endpoints using Python, FastAPI, and PostgreSQL for customer data ingestion.")
    page.insert_text((50, 190), "- Optimized database queries to improve performance.")
    page.insert_text((50, 205), "- Helped team maintain Kubernetes deployment manifests.")
    page.insert_text((50, 235), "PROJECTS")
    page.insert_text((50, 250), "Micro-Cache Redis Wrapper")
    page.insert_text((50, 265), "- Open source caching library for distributed Python applications.")
    page.insert_text((50, 295), "SKILLS")
    page.insert_text((50, 310), "Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, Git, Linux")
    page.insert_text((50, 340), "EDUCATION")
    page.insert_text((50, 355), "B.S. in Computer Science - San Jose State University (2020)")

    stream = doc.write()
    doc.close()
    return stream


def _upload_resume(filename: str = "david_chen_recommendations.pdf") -> str:
    """Uploads resume and returns its permanent resume_id."""
    pdf_bytes = create_sample_recommendation_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201, save_res.text
    return save_res.json()["data"]["id"]


def test_recommendations_api_lifecycle():
    """Validates full lifecycle: generation, retrieval, filtering, and completion tracking."""
    resume_id = _upload_resume()

    # 1. Trigger recommendation generation
    gen_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/recommendations/generate")
    assert gen_res.status_code == 200, gen_res.text
    data = gen_res.json()["data"]

    assert data["resume_id"] == resume_id
    assert "total_recommendations_count" in data
    assert data["total_recommendations_count"] > 0
    assert data["completed_count"] == 0
    assert data["pending_count"] == data["total_recommendations_count"]
    assert data["completion_percentage"] == 0.0

    # Verify coverage summary
    coverage = data["coverage_summary"]
    assert "coverage_percentage" in coverage
    assert "total_features" in coverage
    assert coverage["total_features"] == 6

    # Verify recommendations list structure
    recs = data["recommendations"]
    assert len(recs) == data["total_recommendations_count"]

    first_rec = recs[0]
    required_keys = [
        "id", "recommendation_id", "title", "category", "category_name",
        "description", "explanation", "reason", "evidence", "suggested_action",
        "priority", "estimated_effort", "related_feature", "is_completed",
        "completion_status", "completed_at"
    ]
    for key in required_keys:
        assert key in first_rec, f"Missing key {key} in recommendation item"

    assert first_rec["is_completed"] is False
    assert first_rec["completion_status"] == "Pending"
    assert first_rec["completed_at"] is None
    assert first_rec["priority"] in ["Critical", "High", "Medium", "Low"]
    assert first_rec["estimated_effort"] in ["Easy", "Medium", "Hard"]

    # 2. Get recommendations (cached retrieval)
    get_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/recommendations")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["total_recommendations_count"] == data["total_recommendations_count"]

    # 3. Filter by category
    tech_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/recommendations?category=technical_skills")
    assert tech_res.status_code == 200
    tech_recs = tech_res.json()["data"]["recommendations"]
    for r in tech_recs:
        assert r["category"] == "technical_skills"

    # 4. Mark first recommendation completed
    first_id = first_rec["id"]
    patch_res = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/recommendations/{first_id}/status",
        json={"is_completed": True},
    )
    assert patch_res.status_code == 200, patch_res.text
    patch_data = patch_res.json()["data"]
    assert patch_data["completed_count"] == 1
    assert patch_data["pending_count"] == data["total_recommendations_count"] - 1
    assert patch_data["completion_percentage"] > 0
    assert patch_data["updated_item"]["is_completed"] is True
    assert patch_data["updated_item"]["completed_at"] is not None

    # 5. Filter by is_completed=true
    comp_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/recommendations?is_completed=true")
    assert comp_res.status_code == 200
    assert len(comp_res.json()["data"]["recommendations"]) == 1
    assert comp_res.json()["data"]["recommendations"][0]["id"] == first_id

    # 6. Reopen recommendation
    reopen_res = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/recommendations/{first_id}/status",
        json={"is_completed": False},
    )
    assert reopen_res.status_code == 200
    reopen_data = reopen_res.json()["data"]
    assert reopen_data["completed_count"] == 0
    assert reopen_data["completion_percentage"] == 0.0
    assert reopen_data["updated_item"]["is_completed"] is False
    assert reopen_data["updated_item"]["completed_at"] is None


def test_recommendations_nonexistent_resume():
    """Validates 404 when resume ID does not exist."""
    fake_id = str(uuid.uuid4())
    res = client.get(f"{RESUMES_ENDPOINT}/{fake_id}/recommendations")
    assert res.status_code == 404


def test_recommendations_graceful_missing_analyses():
    """Validates that recommendations are generated cleanly even if some or all prior analyses are missing."""
    resume_id = _upload_resume(filename="partial_analyses_resume.pdf")

    # Generate recommendations without running any other analysis first
    res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/recommendations/generate")
    assert res.status_code == 200, res.text
    data = res.json()["data"]

    # Coverage should accurately reflect 0/6 prior analyses
    cov = data["coverage_summary"]
    assert cov["is_full_coverage"] is False
    assert len(cov["missing_features"]) == 6
    assert cov["coverage_percentage"] == 0.0

    # But recommendations are still generated gracefully across target categories!
    recs = data["recommendations"]
    assert len(recs) >= 5
    categories = {r["category"] for r in recs}
    assert "technical_skills" in categories
    assert "work_experience" in categories


def test_recommendations_priority_ordering():
    """Validates that recommendations are sorted with highest priority first."""
    resume_id = _upload_resume(filename="priority_test_resume.pdf")

    res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/recommendations/generate")
    assert res.status_code == 200
    recs = res.json()["data"]["recommendations"]

    priority_weight = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    weights = [priority_weight.get(r["priority"], 99) for r in recs]
    # Check that weights are monotonically non-decreasing
    assert weights == sorted(weights), "Recommendations are not sorted in Critical -> High -> Medium -> Low priority order"


def test_recommendations_integration_with_prior_analyses():
    """Validates that running prior analysis (e.g., ATS analysis) updates coverage and findings."""
    resume_id = _upload_resume(filename="integrated_analyses_resume.pdf")

    # Run ATS analysis first (Feature #24)
    ats_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/ats/analyze")
    assert ats_res.status_code == 200, ats_res.text

    # Run Achievement analysis (Feature #26)
    ach_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/achievements/analyze")
    assert ach_res.status_code == 200, ach_res.text

    # Now generate recommendations (Feature #27)
    rec_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/recommendations/generate")
    assert rec_res.status_code == 200, rec_res.text
    data = rec_res.json()["data"]

    # Coverage should show at least 2 available features
    cov = data["coverage_summary"]
    assert cov["coverage_percentage"] >= 33.0
    assert any("ATS" in f for f in cov["available_features"])
    assert any("Achievement" in f for f in cov["available_features"])

    # Recommendations should contain related feature tags referencing Feature #24 or #26
    features = [r["related_feature"] for r in data["recommendations"]]
    assert any("Feature #24" in f or "Feature #26" in f for f in features)


def test_recommendations_invalid_id_status_update():
    """Validates 404 when attempting to update status of nonexistent recommendation ID."""
    resume_id = _upload_resume(filename="status_err_resume.pdf")
    gen_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/recommendations/generate")
    assert gen_res.status_code == 200

    bad_id = "REC-INVALID-999"
    patch_res = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/recommendations/{bad_id}/status",
        json={"is_completed": True},
    )
    assert patch_res.status_code == 404
