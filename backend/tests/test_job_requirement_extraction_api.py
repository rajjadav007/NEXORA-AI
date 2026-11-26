"""
Integration & Unit Tests for Job Requirement Extraction
Phase 6 | Feature 36: Job Requirement Extraction
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
from app.models.job_requirement_analysis import JobRequirementAnalysis
from app.models.user import User
from app.schemas.job_requirement_analysis import (
    EducationRequirementSchema,
    ExperienceRequirementSchema,
    ExtractedRequirementItem,
    JobRequirementAIStructuredOutput,
)
from app.services.job_requirement_extraction.ai_extractor import JobRequirementAIExtractor
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
            select(JobRequirementAnalysis).where(JobRequirementAnalysis.user_id == uid)
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
    job_title: str = "AI Engineer",
    company_name: str = "Nexora Labs",
    description: str = (
        "Strong Python programming skills required. Experience with LangChain is an advantage. "
        "Bachelor's Degree in Computer Science required. 0-1 years experience; freshers welcome."
    ),
) -> dict:
    payload = {
        "job_title": job_title,
        "company_name": company_name,
        "description": description,
    }
    res = client.post(ENDPOINT, json=payload, headers={"X-User-Id": user_id})
    assert res.status_code == 201, res.text
    return res.json()["data"]


def test_ai_engineer_requirements_and_db_persistence():
    user_id = str(uuid.uuid4())
    mock_output = JobRequirementAIStructuredOutput(
        technical_skills=[
            ExtractedRequirementItem(
                name="Python",
                category="Programming Language",
                importance="Mandatory",
                evidence="Strong Python programming skills required",
                confidence=0.98,
                source_type="explicit",
            ),
            ExtractedRequirementItem(
                name="LangChain",
                category="AI Framework",
                importance="Preferred",
                evidence="Experience with LangChain is an advantage",
                confidence=0.95,
                source_type="explicit",
            ),
        ],
        education=EducationRequirementSchema(
            minimum_level="Bachelor's Degree",
            required_degree="Bachelor's Degree",
            required_fields=["Computer Science"],
            required_certifications=[],
            preferred_certifications=[],
        ),
        experience=ExperienceRequirementSchema(
            minimum_years=0,
            maximum_years=1,
            fresher_eligible=True,
            requirements=[],
        ),
        soft_skills=[
            ExtractedRequirementItem(
                name="Communication",
                category="Soft Skill",
                importance="Mandatory",
                evidence="Collaborate with product teams",
                confidence=0.82,
                source_type="inferred",
            )
        ],
        domain_knowledge=[
            ExtractedRequirementItem(
                name="Generative AI",
                category="Domain Knowledge",
                importance="Mandatory",
                evidence="Build LLM-powered applications",
                confidence=0.9,
                source_type="explicit",
            )
        ],
        other_requirements=[],
    )

    try:
        jd = _create_jd(user_id)
        with patch(
            "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
            new=AsyncMock(return_value=mock_output),
        ):
            res = client.post(
                f"{ENDPOINT}/{jd['id']}/requirements-analysis",
                headers={"X-User-Id": user_id},
            )
            assert res.status_code == 200, res.text
            data = res.json()["data"]
            assert data["job_id"] == jd["id"]
            assert data["technical_skills"][0]["name"] == "Python"
            assert data["technical_skills"][0]["importance"] == "Mandatory"
            assert data["technical_skills"][1]["category"] == "Framework & Library"
            assert data["technical_skills"][1]["importance"] == "Preferred"
            assert data["education"]["minimum_level"] == "Bachelor's Degree"
            assert data["experience"]["fresher_eligible"] is True
            assert data["summary_counts"]["mandatory_count"] == 3
            assert data["summary_counts"]["preferred_count"] == 1
            assert data["cached"] is False

        # Verify DB persistence & JobDescription sync
        db = SessionLocal()
        try:
            saved = db.execute(
                select(JobRequirementAnalysis).where(
                    JobRequirementAnalysis.job_description_id == uuid.UUID(jd["id"])
                )
            ).scalar_one_or_none()
            assert saved is not None
            jd_row = db.execute(
                select(JobDescription).where(JobDescription.id == uuid.UUID(jd["id"]))
            ).scalar_one()
            assert jd_row.analysis_status == "COMPLETED"
            assert "Python" in jd_row.mandatory_skills
            assert "LangChain" in jd_row.preferred_skills
        finally:
            db.close()

        get_res = client.get(
            f"{ENDPOINT}/{jd['id']}/requirements-analysis",
            headers={"X-User-Id": user_id},
        )
        assert get_res.status_code == 200
        assert get_res.json()["data"]["technical_skills"][0]["name"] == "Python"
    finally:
        _cleanup_user(user_id)


def test_data_scientist_data_analyst_and_backend_developer():
    user_id = str(uuid.uuid4())
    cases = [
        (
            "Data Scientist",
            "Must know Python, Scikit-learn, and Machine Learning. TensorFlow is a plus.",
            JobRequirementAIStructuredOutput(
                technical_skills=[
                    ExtractedRequirementItem(name="Python", category="Programming Language", importance="Mandatory"),
                    ExtractedRequirementItem(name="Scikit-learn", category="Framework & Library", importance="Mandatory"),
                    ExtractedRequirementItem(name="Machine Learning", category="AI & Machine Learning", importance="Mandatory"),
                    ExtractedRequirementItem(name="TensorFlow", category="Framework & Library", importance="Preferred"),
                ],
                domain_knowledge=[
                    ExtractedRequirementItem(name="Data Science", category="Domain Knowledge", importance="Mandatory"),
                ],
            ),
        ),
        (
            "Data Analyst",
            "SQL required for querying MySQL databases. Analytical thinking and Tableau preferred.",
            JobRequirementAIStructuredOutput(
                technical_skills=[
                    ExtractedRequirementItem(name="SQL", category="Programming Language", importance="Mandatory"),
                    ExtractedRequirementItem(name="MySQL", category="Database", importance="Mandatory"),
                    ExtractedRequirementItem(name="Tableau", category="Tool & Platform", importance="Preferred"),
                ],
                soft_skills=[
                    ExtractedRequirementItem(name="Analytical thinking", category="Soft Skill", importance="Mandatory"),
                ],
                domain_knowledge=[
                    ExtractedRequirementItem(name="Data Analytics", category="Domain Knowledge", importance="Mandatory"),
                ],
            ),
        ),
        (
            "Backend Developer",
            "FastAPI, PostgreSQL, Docker, and Git required. Kubernetes and AWS nice to have.",
            JobRequirementAIStructuredOutput(
                technical_skills=[
                    ExtractedRequirementItem(name="FastAPI", category="Framework & Library", importance="Mandatory"),
                    ExtractedRequirementItem(name="PostgreSQL", category="Database", importance="Mandatory"),
                    ExtractedRequirementItem(name="Docker", category="Tool & Platform", importance="Mandatory"),
                    ExtractedRequirementItem(name="Git", category="Tool & Platform", importance="Mandatory"),
                    ExtractedRequirementItem(name="Kubernetes", category="Tool & Platform", importance="Preferred"),
                    ExtractedRequirementItem(name="AWS", category="Tool & Platform", importance="Preferred"),
                ],
            ),
        ),
    ]

    try:
        for title, desc, mock_out in cases:
            jd = _create_jd(user_id, job_title=title, description=desc)
            with patch(
                "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
                new=AsyncMock(return_value=mock_out),
            ):
                res = client.post(
                    f"{ENDPOINT}/{jd['id']}/requirements-analysis",
                    headers={"X-User-Id": user_id},
                )
                assert res.status_code == 200, res.text
                data = res.json()["data"]
                assert len(data["technical_skills"]) == len(mock_out.technical_skills)
    finally:
        _cleanup_user(user_id)


def test_no_tech_skills_only_preferred_missing_edu_exp_and_ambiguous():
    user_id = str(uuid.uuid4())
    try:
        # 1. No technical skills, missing education & experience, ambiguous requirements
        jd_none = _create_jd(
            user_id,
            job_title="Operations Coordinator",
            description=(
                "Support general office coordination, cross-team scheduling, and stakeholder follow-ups "
                "in a dynamic environment."
            ),
        )
        mock_none = JobRequirementAIStructuredOutput(
            technical_skills=[],
            education=EducationRequirementSchema(),
            experience=ExperienceRequirementSchema(),
            soft_skills=[
                ExtractedRequirementItem(name="Communication", category="Soft Skill", importance="Unspecified")
            ],
            other_requirements=[
                ExtractedRequirementItem(name="Stakeholder coordination", category="Other", importance="Unspecified")
            ],
        )
        with patch(
            "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
            new=AsyncMock(return_value=mock_none),
        ):
            res = client.post(
                f"{ENDPOINT}/{jd_none['id']}/requirements-analysis",
                headers={"X-User-Id": user_id},
            )
            assert res.status_code == 200
            data = res.json()["data"]
            assert data["technical_skills"] == []
            assert data["education"]["minimum_level"] is None
            assert data["experience"]["minimum_years"] is None
            assert data["summary_counts"]["unspecified_count"] == 2

        # 2. Only preferred skills
        jd_pref = _create_jd(
            user_id,
            job_title="Junior Research Assistant",
            description=(
                "Familiarity with Python, PyTorch, and Vector Databases is nice to have and considered a plus."
            ),
        )
        mock_pref = JobRequirementAIStructuredOutput(
            technical_skills=[
                ExtractedRequirementItem(name="Python", category="Programming Language", importance="Preferred"),
                ExtractedRequirementItem(name="PyTorch", category="Framework & Library", importance="Preferred"),
                ExtractedRequirementItem(name="Vector Databases", category="Database", importance="Preferred"),
            ]
        )
        with patch(
            "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
            new=AsyncMock(return_value=mock_pref),
        ):
            res = client.post(
                f"{ENDPOINT}/{jd_pref['id']}/requirements-analysis",
                headers={"X-User-Id": user_id},
            )
            assert res.status_code == 200
            counts = res.json()["data"]["summary_counts"]
            assert counts["mandatory_count"] == 0
            assert counts["preferred_count"] == 3
    finally:
        _cleanup_user(user_id)


def test_repeated_extraction_caching_and_no_duplicates():
    user_id = str(uuid.uuid4())
    mock_out = JobRequirementAIStructuredOutput(
        technical_skills=[
            ExtractedRequirementItem(name="Python", category="Programming Language", importance="Mandatory")
        ]
    )
    try:
        jd = _create_jd(user_id)
        mock_fn = AsyncMock(return_value=mock_out)
        with patch(
            "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
            new=mock_fn,
        ):
            first = client.post(
                f"{ENDPOINT}/{jd['id']}/requirements-analysis",
                headers={"X-User-Id": user_id},
            )
            assert first.status_code == 200
            assert first.json()["data"]["cached"] is False
            assert mock_fn.await_count == 1

            second = client.post(
                f"{ENDPOINT}/{jd['id']}/requirements-analysis",
                headers={"X-User-Id": user_id},
            )
            assert second.status_code == 200
            assert second.json()["data"]["cached"] is True
            assert mock_fn.await_count == 1

            third = client.post(
                f"{ENDPOINT}/{jd['id']}/requirements-analysis?force_recalculate=true",
                headers={"X-User-Id": user_id},
            )
            assert third.status_code == 200
            assert third.json()["data"]["cached"] is False
            assert mock_fn.await_count == 2

        db = SessionLocal()
        try:
            rows = db.execute(
                select(JobRequirementAnalysis).where(
                    JobRequirementAnalysis.job_description_id == uuid.UUID(jd["id"])
                )
            ).scalars().all()
            assert len(rows) == 1
        finally:
            db.close()
    finally:
        _cleanup_user(user_id)


def test_invalid_ai_json_and_ollama_unavailable():
    user_id = str(uuid.uuid4())
    try:
        jd = _create_jd(user_id)

        with patch(
            "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
            new=AsyncMock(side_effect=AIOutputValidationError("Invalid AI JSON")),
        ):
            res = client.post(
                f"{ENDPOINT}/{jd['id']}/requirements-analysis",
                headers={"X-User-Id": user_id},
            )
            assert res.status_code == 502

        with patch(
            "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
            new=AsyncMock(side_effect=OllamaUnavailableError("Ollama unavailable")),
        ):
            res = client.post(
                f"{ENDPOINT}/{jd['id']}/requirements-analysis",
                headers={"X-User-Id": user_id},
            )
            assert res.status_code == 503

        extractor = JobRequirementAIExtractor(base_url="http://localhost:11434", model="qwen2.5:3b", timeout=1.0)
        fake_llm = MagicMock()
        fake_structured = MagicMock()
        fake_structured.ainvoke = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        fake_llm.with_structured_output.return_value = fake_structured

        with patch.object(extractor, "_get_llm", return_value=fake_llm):
            try:
                asyncio.run(extractor.extract_requirements(description="Test JD for connection error."))
                assert False, "Expected OllamaUnavailableError"
            except OllamaUnavailableError:
                pass

        fake_structured.ainvoke = AsyncMock(return_value="{bad-json")
        with patch.object(extractor, "_get_llm", return_value=fake_llm):
            try:
                asyncio.run(extractor.extract_requirements(description="Test JD for invalid JSON."))
                assert False, "Expected AIOutputValidationError"
            except AIOutputValidationError:
                pass
    finally:
        _cleanup_user(user_id)


def test_unauthorized_and_user_data_isolation():
    owner_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())
    try:
        jd_owner = _create_jd(owner_id, job_title="Owner Role")
        jd_other = _create_jd(other_id, job_title="Other Role")

        # Unauthenticated
        assert client.post(f"{ENDPOINT}/{jd_owner['id']}/requirements-analysis").status_code == 401

        # Cross-user POST & GET blocked
        assert (
            client.post(
                f"{ENDPOINT}/{jd_owner['id']}/requirements-analysis",
                headers={"X-User-Id": other_id},
            ).status_code
            == 403
        )
        assert (
            client.get(
                f"{ENDPOINT}/{jd_other['id']}/requirements-analysis",
                headers={"X-User-Id": owner_id},
            ).status_code
            == 403
        )
    finally:
        _cleanup_user(owner_id)
        _cleanup_user(other_id)
