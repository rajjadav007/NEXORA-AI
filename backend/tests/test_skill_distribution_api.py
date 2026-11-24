"""
Integration Tests for Resume Skill Distribution API Endpoints
Phase 5 | Feature 29: Skill Distribution
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
from app.models.skills import ResumeSkill

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_tech_pdf_bytes() -> bytes:
    """Generates a sample PDF resume with rich technical skills."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Alex Rivera")
    page.insert_text((50, 70), "alex.rivera@example.com | (555) 321-7654 | San Francisco, CA")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "Lead Machine Learning & Full Stack Engineer with 7 years experience.")
    page.insert_text((50, 145), "EXPERIENCE")
    page.insert_text((50, 160), "Principal AI Engineer - NextGen Systems (2021 - Present)")
    page.insert_text((50, 175), "- Deployed deep learning models in PyTorch with LangChain and FastAPI.")
    page.insert_text((50, 190), "- Built data processing pipelines with Pandas, NumPy, and Apache Spark.")
    page.insert_text((50, 215), "SKILLS")
    page.insert_text(
        (50, 230),
        "Python, TypeScript, SQL, React, FastAPI, PyTorch, Pandas, PostgreSQL, Docker, AWS, Git",
    )
    page.insert_text((50, 255), "EDUCATION")
    page.insert_text((50, 270), "M.S. in Computer Science - Stanford University (2019)")

    stream = doc.write()
    doc.close()
    return stream


def create_empty_pdf_bytes() -> bytes:
    """Generates a bare minimal PDF resume with no listed skills."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Jane Doe")
    page.insert_text((50, 70), "jane.doe@example.com")
    page.insert_text((50, 100), "No specific technical content listed here.")
    stream = doc.write()
    doc.close()
    return stream


def _upload_and_save_resume(pdf_bytes: bytes, filename: str = "alex_rivera_resume.pdf") -> str:
    """Uploads and saves a resume, returning its permanent resume_id."""
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201, save_res.text
    return save_res.json()["data"]["id"]


def test_get_skill_distribution_success():
    """Verify endpoint retrieves categorized skills and summary metrics."""
    pdf_bytes = create_sample_tech_pdf_bytes()
    resume_id = _upload_and_save_resume(pdf_bytes)

    # Populate explicit resume_skills records in the database to test all 8 categories
    db = SessionLocal()
    try:
        resume_uuid = uuid.UUID(resume_id)
        test_skills = [
            ("Python", "Programming Languages", "exact_match"),
            ("TypeScript", "Programming Languages", "exact_match"),
            ("SQL", "Programming Languages", "exact_match"),
            ("PyTorch", "Frameworks & Libraries", "exact_match"),
            ("Natural Language Processing", "Machine Learning & AI", "exact_match"),
            ("Pandas", "Frameworks & Libraries", "exact_match"),
            ("React", "Frameworks & Libraries", "exact_match"),
            ("FastAPI", "Frameworks & Libraries", "exact_match"),
            ("PostgreSQL", "Databases", "exact_match"),
            ("Docker", "Cloud & DevOps", "exact_match"),
            ("AWS", "Cloud & DevOps", "exact_match"),
            ("Git", "Tools", "exact_match"),
            ("Agile Coaching", "Other", "exact_match"),
        ]
        for name, cat, method in test_skills:
            db.add(
                ResumeSkill(
                    resume_id=resume_uuid,
                    original_name=name,
                    canonical_name=name,
                    category=cat,
                    skill_type="technical" if cat != "Other" else "soft",
                    normalization_method=method,
                    confidence_score=1.0,
                    occurrence_count=1,
                    source_sections=["skills"],
                )
            )
        db.commit()
    finally:
        db.close()

    # Query endpoint via /api/v1 prefix
    url_v1 = f"{settings.API_V1_PREFIX}/resumes/{resume_id}/analytics/skills"
    res_v1 = client.get(url_v1)
    assert res_v1.status_code == 200, res_v1.text
    body = res_v1.json()
    assert body["success"] is True
    data = body["data"]

    assert data["resume_id"] == resume_id
    assert data["total_skills"] == 13

    # Check categories
    cat_names = [c["name"] for c in data["categories"]]
    assert "Programming Languages" in cat_names
    assert "AI and Machine Learning" in cat_names
    assert "Data Science and Analytics" in cat_names
    assert "Frameworks and Libraries" in cat_names
    assert "Databases" in cat_names
    assert "Cloud and DevOps" in cat_names
    assert "Development Tools" in cat_names
    assert "Other Skills" in cat_names

    # Check summary
    summary = data["summary"]
    assert summary["total_skills"] == 13
    assert summary["total_categories"] == len(data["categories"])
    assert summary["most_populated_category"] is not None
    assert "Agile Coaching" in summary["uncategorized_skills"]

    # Also check unversioned direct alias /api/resumes/{id}/analytics/skills
    url_direct = f"/api/resumes/{resume_id}/analytics/skills"
    res_direct = client.get(url_direct)
    assert res_direct.status_code == 200
    assert res_direct.json()["data"]["total_skills"] == 13


def test_skill_distribution_duplicate_prevention():
    """Verify duplicate mentions of skills are consolidated and deduplicated."""
    pdf_bytes = create_sample_tech_pdf_bytes()
    resume_id = _upload_and_save_resume(pdf_bytes, filename="dup_test_resume.pdf")

    db = SessionLocal()
    try:
        resume_uuid = uuid.UUID(resume_id)
        # Insert duplicate Python and duplicate Docker mentions
        db.add(ResumeSkill(
            resume_id=resume_uuid,
            original_name="Python",
            canonical_name="Python",
            category="Programming Languages",
            occurrence_count=2,
            source_sections=["skills", "experience"],
        ))
        db.add(ResumeSkill(
            resume_id=resume_uuid,
            original_name="python",
            canonical_name="Python",
            category="Programming Languages",
            occurrence_count=1,
            source_sections=["projects"],
        ))
        db.add(ResumeSkill(
            resume_id=resume_uuid,
            original_name="Docker",
            canonical_name="Docker",
            category="Cloud & DevOps",
            occurrence_count=1,
            source_sections=["skills"],
        ))
        db.commit()
    finally:
        db.close()

    res = client.get(f"{settings.API_V1_PREFIX}/resumes/{resume_id}/analytics/skills")
    assert res.status_code == 200
    data = res.json()["data"]

    # Total skills must count Python once and Docker once -> total = 2
    assert data["total_skills"] == 2
    prog_cat = next(c for c in data["categories"] if c["name"] == "Programming Languages")
    assert prog_cat["count"] == 1
    assert prog_cat["skills"] == ["Python"]


def test_skill_distribution_empty_resume():
    """Verify empty resume returns 200 with 0 skills and empty categories."""
    pdf_bytes = create_empty_pdf_bytes()
    resume_id = _upload_and_save_resume(pdf_bytes, filename="empty_resume.pdf")

    res = client.get(f"{settings.API_V1_PREFIX}/resumes/{resume_id}/analytics/skills")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_skills"] == 0
    assert data["categories"] == []
    assert data["summary"]["total_skills"] == 0
    assert data["summary"]["total_categories"] == 0
    assert data["summary"]["most_populated_category"] is None
    assert data["summary"]["uncategorized_skills"] == []


def test_skill_distribution_invalid_resume_id():
    """Verify invalid UUID returns 400."""
    res = client.get(f"{settings.API_V1_PREFIX}/resumes/not-a-valid-uuid/analytics/skills")
    assert res.status_code == 400


def test_skill_distribution_not_found():
    """Verify non-existent UUID returns 404."""
    random_uuid = str(uuid.uuid4())
    res = client.get(f"{settings.API_V1_PREFIX}/resumes/{random_uuid}/analytics/skills")
    assert res.status_code == 404
