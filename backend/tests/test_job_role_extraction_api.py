"""
Integration & Unit Tests for Job Role Extraction
Phase 6 | Feature 35: Job Role Extraction
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.database.session import SessionLocal
from app.main import app
from app.models.job_description import JobDescription
from app.models.job_role_analysis import JobRoleAnalysis
from app.models.user import User
from app.schemas.job_role_analysis import ExperienceLevelSchema, JobRoleAIStructuredOutput
from app.services.job_role_extraction.ai_extractor import JobRoleAIExtractor
from app.services.quality_score.ai_evaluator import (
    AIOutputValidationError,
    OllamaUnavailableError,
)

client = TestClient(app)
ENDPOINT = f"{settings.API_V1_PREFIX}/job-descriptions"


def _cleanup_user(user_id: str) -> None:
    db = SessionLocal()
    try:
        uid = uuid.UUID(user_id)
        analyses = db.execute(
            select(JobRoleAnalysis).where(JobRoleAnalysis.user_id == uid)
        ).scalars().all()
        for item in analyses:
            db.delete(item)
        jds = db.execute(
            select(JobDescription).where(JobDescription.user_id == uid)
        ).scalars().all()
        for jd in jds:
            db.delete(jd)
        user = db.execute(select(User).where(User.id == uid)).scalar_one_or_none()
        if user:
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _create_jd(
    user_id: str,
    job_title: str = "AI Engineer Intern",
    company_name: str = "Nexora Labs",
    description: str = (
        "We are looking for an AI Engineer Intern to develop Python-based AI applications, "
        "build and integrate LLM solutions, and collaborate with the engineering team."
    ),
    employment_type: str | None = "Internship",
    location: str | None = None,
    experience_required: str | None = None,
) -> dict:
    payload = {
        "job_title": job_title,
        "company_name": company_name,
        "description": description,
        "employment_type": employment_type,
        "location": location,
        "experience_required": experience_required,
    }
    res = client.post(ENDPOINT, json=payload, headers={"X-User-Id": user_id})
    assert res.status_code == 201, res.text
    return res.json()["data"]


def test_extract_ai_engineer_intern_and_db_persistence():
    user_id = str(uuid.uuid4())
    mock_output = JobRoleAIStructuredOutput(
        job_title="AI Engineer Intern",
        standardized_role="AI Engineer",
        department="Artificial Intelligence",
        category="Engineering",
        seniority="Internship",
        experience_level=ExperienceLevelSchema(minimum_years=0, maximum_years=1, description="0-1 years"),
        employment_type="Internship",
        work_arrangement="Unknown",
        industry="Technology",
        responsibilities=[
            "Develop AI applications",
            "Build and integrate LLM solutions",
            "Work with Python-based AI systems",
        ],
        role_summary="Develop and integrate AI-powered applications.",
        confidence_score=0.92,
    )

    try:
        jd = _create_jd(user_id)
        with patch(
            "app.services.job_role_extraction.service.job_role_extraction_service.ai_extractor.extract_role",
            new=AsyncMock(return_value=mock_output),
        ):
            res = client.post(f"{ENDPOINT}/{jd['id']}/role-analysis", headers={"X-User-Id": user_id})
            assert res.status_code == 200, res.text
            body = res.json()
            assert body["success"] is True
            data = body["data"]
            assert data["standardized_role"] == "AI Engineer"
            assert data["seniority"] == "Internship"
            assert data["work_arrangement"] == "Unknown"
            assert data["confidence_score"] == 0.92
            assert data["cached"] is False
            assert data["analysis_status"] == "COMPLETED"
            assert len(data["responsibilities"]) == 3

        # Verify DB persistence & GET endpoint
        db = SessionLocal()
        try:
            saved = db.execute(
                select(JobRoleAnalysis).where(JobRoleAnalysis.job_description_id == uuid.UUID(jd["id"]))
            ).scalar_one_or_none()
            assert saved is not None
            assert saved.standardized_role == "AI Engineer"
            jd_row = db.execute(
                select(JobDescription).where(JobDescription.id == uuid.UUID(jd["id"]))
            ).scalar_one()
            assert jd_row.analysis_status == "COMPLETED"
        finally:
            db.close()

        get_res = client.get(f"{ENDPOINT}/{jd['id']}/role-analysis", headers={"X-User-Id": user_id})
        assert get_res.status_code == 200
        assert get_res.json()["data"]["standardized_role"] == "AI Engineer"
    finally:
        _cleanup_user(user_id)


def test_extract_ml_engineer_data_scientist_and_backend_developer():
    user_id = str(uuid.uuid4())
    cases = [
        (
            "Senior Machine Learning Engineer",
            "Build, train, and deploy production ML pipelines with PyTorch and Kubernetes. 5+ years experience required.",
            JobRoleAIStructuredOutput(
                job_title="Senior Machine Learning Engineer",
                standardized_role="Machine Learning Engineer",
                department="Machine Learning",
                category="Engineering",
                seniority="Senior",
                experience_level=ExperienceLevelSchema(minimum_years=5, maximum_years=None, description="5+ years"),
                employment_type="Full-time",
                work_arrangement="Hybrid",
                industry="Technology",
                responsibilities=["Build and deploy ML pipelines"],
                role_summary="Lead production ML pipeline engineering.",
                confidence_score=0.95,
            ),
        ),
        (
            "Data Scientist",
            "Apply statistical modeling, A/B testing, and predictive analytics to customer retention datasets.",
            JobRoleAIStructuredOutput(
                job_title="Data Scientist",
                standardized_role="Data Scientist",
                department="Data Science",
                category="Data & Analytics",
                seniority="Mid-Level",
                experience_level=ExperienceLevelSchema(minimum_years=2, maximum_years=4, description="2-4 years"),
                employment_type="Full-time",
                work_arrangement="Remote",
                industry="SaaS",
                responsibilities=["Run statistical modeling and A/B tests"],
                role_summary="Drive experimentation and predictive modeling.",
                confidence_score=0.9,
            ),
        ),
        (
            "Backend Developer",
            "Design REST APIs in Python FastAPI and PostgreSQL microservices on AWS.",
            JobRoleAIStructuredOutput(
                job_title="Backend Developer",
                standardized_role="Backend Developer",
                department="Platform Engineering",
                category="Engineering",
                seniority="Junior",
                experience_level=ExperienceLevelSchema(minimum_years=1, maximum_years=3, description="1-3 years"),
                employment_type="Full-time",
                work_arrangement="On-site",
                industry="FinTech",
                responsibilities=["Design REST APIs and microservices"],
                role_summary="Build scalable FastAPI backend services.",
                confidence_score=0.89,
            ),
        ),
    ]

    try:
        for title, desc, mock_out in cases:
            jd = _create_jd(user_id, job_title=title, description=desc, employment_type="Full-time")
            with patch(
                "app.services.job_role_extraction.service.job_role_extraction_service.ai_extractor.extract_role",
                new=AsyncMock(return_value=mock_out),
            ):
                res = client.post(f"{ENDPOINT}/{jd['id']}/role-analysis", headers={"X-User-Id": user_id})
                assert res.status_code == 200, res.text
                data = res.json()["data"]
                assert data["standardized_role"] == mock_out.standardized_role
                assert data["seniority"] == mock_out.seniority
    finally:
        _cleanup_user(user_id)


def test_missing_title_missing_experience_and_ambiguous_role():
    user_id = str(uuid.uuid4())
    try:
        # Job description without explicit title/experience & ambiguous role
        jd = _create_jd(
            user_id,
            job_title="Untitled Role",
            description=(
                "Join our fast-paced team to support cross-functional initiatives, coordinate stakeholders, "
                "and assist with special projects across operations and technology."
            ),
            employment_type=None,
        )
        mock_out = JobRoleAIStructuredOutput(
            job_title=None,
            standardized_role="Other",
            department=None,
            category=None,
            seniority="Unknown",
            experience_level=ExperienceLevelSchema(minimum_years=None, maximum_years=None, description=None),
            employment_type=None,
            work_arrangement="Unknown",
            industry=None,
            responsibilities=["Support cross-functional initiatives"],
            role_summary="General cross-functional support role.",
            confidence_score=0.42,
        )
        with patch(
            "app.services.job_role_extraction.service.job_role_extraction_service.ai_extractor.extract_role",
            new=AsyncMock(return_value=mock_out),
        ):
            res = client.post(f"{ENDPOINT}/{jd['id']}/role-analysis", headers={"X-User-Id": user_id})
            assert res.status_code == 200, res.text
            data = res.json()["data"]
            assert data["standardized_role"] == "Other"
            # Must not assume Fresher when evidence is missing
            assert data["seniority"] == "Unknown"
            assert data["experience_level"]["minimum_years"] is None
            assert data["experience_level"]["maximum_years"] is None
            assert data["confidence_score"] == 0.42
    finally:
        _cleanup_user(user_id)


def test_repeated_extraction_uses_cache_and_prevents_duplicates():
    user_id = str(uuid.uuid4())
    mock_out = JobRoleAIStructuredOutput(
        job_title="AI Engineer",
        standardized_role="AI Engineer",
        seniority="Mid-Level",
        confidence_score=0.88,
    )
    try:
        jd = _create_jd(user_id, job_title="AI Engineer")
        mock_fn = AsyncMock(return_value=mock_out)
        with patch(
            "app.services.job_role_extraction.service.job_role_extraction_service.ai_extractor.extract_role",
            new=mock_fn,
        ):
            first = client.post(f"{ENDPOINT}/{jd['id']}/role-analysis", headers={"X-User-Id": user_id})
            assert first.status_code == 200
            assert first.json()["data"]["cached"] is False
            assert mock_fn.await_count == 1

            # Second call should return cached result without invoking Ollama
            second = client.post(f"{ENDPOINT}/{jd['id']}/role-analysis", headers={"X-User-Id": user_id})
            assert second.status_code == 200
            assert second.json()["data"]["cached"] is True
            assert mock_fn.await_count == 1

            # Force recalculate updates same record without creating duplicate rows
            third = client.post(
                f"{ENDPOINT}/{jd['id']}/role-analysis?force_recalculate=true",
                headers={"X-User-Id": user_id},
            )
            assert third.status_code == 200
            assert third.json()["data"]["cached"] is False
            assert mock_fn.await_count == 2

        db = SessionLocal()
        try:
            rows = db.execute(
                select(JobRoleAnalysis).where(JobRoleAnalysis.job_description_id == uuid.UUID(jd["id"]))
            ).scalars().all()
            assert len(rows) == 1
        finally:
            db.close()
    finally:
        _cleanup_user(user_id)


def test_invalid_ai_response_ollama_unavailable_and_timeout():
    user_id = str(uuid.uuid4())
    try:
        jd = _create_jd(user_id)

        with patch(
            "app.services.job_role_extraction.service.job_role_extraction_service.ai_extractor.extract_role",
            new=AsyncMock(side_effect=AIOutputValidationError("Malformed JSON")),
        ):
            res = client.post(f"{ENDPOINT}/{jd['id']}/role-analysis", headers={"X-User-Id": user_id})
            assert res.status_code == 502

        with patch(
            "app.services.job_role_extraction.service.job_role_extraction_service.ai_extractor.extract_role",
            new=AsyncMock(side_effect=OllamaUnavailableError("Connection refused")),
        ):
            res = client.post(f"{ENDPOINT}/{jd['id']}/role-analysis", headers={"X-User-Id": user_id})
            assert res.status_code == 503

        # Direct unit test of JobRoleAIExtractor timeout & invalid response handling
        extractor = JobRoleAIExtractor(base_url="http://localhost:11434", model="qwen2.5:3b", timeout=1.0)
        fake_llm = MagicMock()
        fake_structured = MagicMock()
        fake_structured.ainvoke = AsyncMock(side_effect=httpx.ReadTimeout("Timed out"))
        fake_llm.with_structured_output.return_value = fake_structured

        with patch.object(extractor, "_get_llm", return_value=fake_llm):
            try:
                asyncio.run(extractor.extract_role(description="Test job description text for timeout check."))
                assert False, "Expected OllamaUnavailableError"
            except OllamaUnavailableError:
                pass

        fake_structured.ainvoke = AsyncMock(return_value="{not-valid-json")
        with patch.object(extractor, "_get_llm", return_value=fake_llm):
            try:
                asyncio.run(extractor.extract_role(description="Test job description text for invalid json check."))
                assert False, "Expected AIOutputValidationError"
            except AIOutputValidationError:
                pass
    finally:
        _cleanup_user(user_id)


def test_unauthorized_and_not_found_access():
    owner_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())
    try:
        jd = _create_jd(owner_id)

        # Missing auth header -> 401
        res_unauth = client.post(f"{ENDPOINT}/{jd['id']}/role-analysis")
        assert res_unauth.status_code == 401

        # Wrong user -> 403
        res_forbidden = client.post(f"{ENDPOINT}/{jd['id']}/role-analysis", headers={"X-User-Id": other_id})
        assert res_forbidden.status_code == 403

        # Nonexistent ID -> 404
        res_missing = client.post(
            f"{ENDPOINT}/{uuid.uuid4()}/role-analysis",
            headers={"X-User-Id": owner_id},
        )
        assert res_missing.status_code == 404
    finally:
        _cleanup_user(owner_id)
