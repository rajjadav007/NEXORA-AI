"""
Integration & Unit Tests for Job Description Report
Phase 6 | Feature 38: Job Description Report
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
from app.models.job_description_report import JobDescriptionReport
from app.models.job_requirement_analysis import JobRequirementAnalysis
from app.models.job_role_analysis import JobRoleAnalysis
from app.models.job_skill_classification import JobSkillClassification
from app.models.user import User
from app.schemas.job_description_report import (
    JobReportAIStructuredOutput,
    JobReportComplexityAnalysis,
    JobReportInsightItem,
)
from app.schemas.job_requirement_analysis import (
    EducationRequirementSchema,
    ExperienceRequirementSchema,
    ExtractedRequirementItem,
    JobRequirementAIStructuredOutput,
)
from app.schemas.job_role_analysis import ExperienceLevelSchema, JobRoleAIStructuredOutput
from app.schemas.job_skill_classification import (
    ClassifiedSkillItem,
    SkillClassificationAIStructuredOutput,
)
from app.services.job_description_report.ai_insights import JobReportAIInsightsGenerator
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
        for model in (
            JobDescriptionReport,
            JobSkillClassification,
            JobRequirementAnalysis,
            JobRoleAnalysis,
            JobDescription,
        ):
            rows = db.execute(select(model).where(model.user_id == uid)).scalars().all()
            for row in rows:
                db.delete(row)
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
        "Must have Python programming skills and AWS experience. "
        "LangChain is preferred. Docker is optional. Bachelor's degree in Computer Science required."
    ),
) -> dict:
    res = client.post(
        ENDPOINT,
        json={
            "job_title": job_title,
            "company_name": company_name,
            "description": description,
        },
        headers={"X-User-Id": user_id},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]


def _seed_prerequisites(user_id: str, job_id: str, role_name: str = "AI Engineer") -> None:
    role_out = JobRoleAIStructuredOutput(
        job_title=role_name,
        standardized_role=role_name,
        department="Engineering",
        category="Artificial Intelligence",
        seniority="Mid-Level",
        experience_level=ExperienceLevelSchema(minimum_years=2, maximum_years=4, description="2-4 years"),
        employment_type="Full-time",
        work_arrangement="Hybrid",
        industry="Software",
        responsibilities=["Build LLM pipelines", "Deploy ML services"],
        role_summary=f"Build production AI systems as {role_name}.",
        confidence_score=0.92,
    )
    req_out = JobRequirementAIStructuredOutput(
        technical_skills=[
            ExtractedRequirementItem(
                name="Python",
                category="Programming Language",
                importance="Mandatory",
                evidence="Must have Python programming skills",
                confidence=0.98,
                source_type="explicit",
            ),
            ExtractedRequirementItem(
                name="AWS",
                category="Tool & Platform",
                importance="Mandatory",
                evidence="AWS experience required",
                confidence=0.94,
                source_type="explicit",
            ),
            ExtractedRequirementItem(
                name="LangChain",
                category="AI Framework",
                importance="Preferred",
                evidence="LangChain is preferred",
                confidence=0.95,
                source_type="explicit",
            ),
        ],
        education=EducationRequirementSchema(
            minimum_level="Bachelor's Degree",
            required_degree="Bachelor's Degree",
            required_fields=["Computer Science"],
        ),
        experience=ExperienceRequirementSchema(
            minimum_years=2,
            maximum_years=4,
            fresher_eligible=False,
        ),
        soft_skills=[
            ExtractedRequirementItem(
                name="Communication",
                category="Soft Skill",
                importance="Mandatory",
                evidence="Cross-functional collaboration",
                confidence=0.85,
                source_type="inferred",
            )
        ],
    )
    skill_out = SkillClassificationAIStructuredOutput(
        skills=[
            ClassifiedSkillItem(
                name="Python",
                category="Programming Language",
                classification="Mandatory",
                priority_score=95,
                expected_proficiency="Advanced",
                evidence="Must have Python programming skills",
                source_type="explicit",
                confidence_score=0.98,
            ),
            ClassifiedSkillItem(
                name="AWS",
                category="Tool & Platform",
                classification="Mandatory",
                priority_score=88,
                expected_proficiency="Intermediate",
                evidence="AWS experience required",
                source_type="explicit",
                confidence_score=0.94,
            ),
            ClassifiedSkillItem(
                name="LangChain",
                category="AI Framework",
                classification="Preferred",
                priority_score=65,
                expected_proficiency="Unspecified",
                evidence="LangChain is preferred",
                source_type="explicit",
                confidence_score=0.95,
            ),
            ClassifiedSkillItem(
                name="Docker",
                category="Tool & Platform",
                classification="Optional",
                priority_score=25,
                expected_proficiency="Unspecified",
                evidence="Docker is optional",
                source_type="explicit",
                confidence_score=0.85,
            ),
        ]
    )

    with (
        patch(
            "app.services.job_role_extraction.service.job_role_extraction_service.ai_extractor.extract_role",
            new=AsyncMock(return_value=role_out),
        ),
        patch(
            "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
            new=AsyncMock(return_value=req_out),
        ),
        patch(
            "app.services.job_skill_classification.service.job_skill_classification_service.ai_classifier.classify_skills",
            new=AsyncMock(return_value=skill_out),
        ),
    ):
        assert client.post(f"{ENDPOINT}/{job_id}/role-analysis", headers={"X-User-Id": user_id}).status_code == 200
        assert client.post(f"{ENDPOINT}/{job_id}/requirements-analysis", headers={"X-User-Id": user_id}).status_code == 200
        assert client.post(f"{ENDPOINT}/{job_id}/skills-classification", headers={"X-User-Id": user_id}).status_code == 200


def _sample_ai_insights(level: str = "Intermediate") -> JobReportAIStructuredOutput:
    return JobReportAIStructuredOutput(
        complexity_analysis=JobReportComplexityAnalysis(
            level=level,
            explanation="Requires solid Python, AWS cloud, and LLM framework experience.",
        ),
        ai_insights=[
            JobReportInsightItem(
                title="Core Technical Focus",
                detail="Strong Python and AWS skills are mandatory, with LangChain as a key advantage.",
                source_type="inferred",
            ),
            JobReportInsightItem(
                title="Experience & Education",
                detail="Targets mid-level engineers (2-4 years) with a Computer Science degree.",
                source_type="inferred",
            ),
        ],
    )


def test_complete_report_generation_regeneration_and_persistence():
    """Tests #1, #2, #3, #9, #10, #11: full report generation, cloud bucketing, versioning, caching, regeneration, DB persistence."""
    user_id = str(uuid.uuid4())
    try:
        jd = _create_jd(user_id, job_title="Machine Learning Engineer")
        _seed_prerequisites(user_id, jd["id"], role_name="Machine Learning Engineer")

        with patch(
            "app.services.job_description_report.service.job_description_report_service.ai_insights_generator.generate_insights",
            new=AsyncMock(return_value=_sample_ai_insights("Advanced")),
        ) as ai_mock:
            # First generation -> v1.0
            res1 = client.post(f"{ENDPOINT}/{jd['id']}/report", headers={"X-User-Id": user_id})
            assert res1.status_code == 200, res1.text
            data1 = res1.json()["data"]
            assert data1["report_version"] == "1.0"
            assert data1["cached"] is False
            assert data1["overview"]["job_title"] == "Machine Learning Engineer"
            assert data1["role_analysis"]["standardized_role"] == "Machine Learning Engineer"
            assert len(data1["technical_requirements"]["cloud_technologies"]) == 1
            assert data1["technical_requirements"]["cloud_technologies"][0]["name"] == "AWS"
            assert len(data1["skill_classification"]["mandatory"]) == 2
            assert len(data1["skill_classification"]["preferred"]) == 1
            assert len(data1["skill_classification"]["optional"]) == 1
            assert data1["complexity_analysis"]["level"] == "Advanced"
            assert data1["complexity_analysis"]["is_ai_estimate"] is True
            assert len(data1["ai_insights"]) == 2
            assert ai_mock.await_count == 1

            # Cached call -> no LLM call
            res2 = client.post(f"{ENDPOINT}/{jd['id']}/report", headers={"X-User-Id": user_id})
            assert res2.status_code == 200
            assert res2.json()["data"]["cached"] is True
            assert res2.json()["data"]["report_version"] == "1.0"
            assert ai_mock.await_count == 1

            # Regenerate -> v2.0
            res3 = client.post(f"{ENDPOINT}/{jd['id']}/report?regenerate=true", headers={"X-User-Id": user_id})
            assert res3.status_code == 200
            assert res3.json()["data"]["cached"] is False
            assert res3.json()["data"]["report_version"] == "2.0"
            assert ai_mock.await_count == 2

            # GET persisted report
            get_res = client.get(f"{ENDPOINT}/{jd['id']}/report", headers={"X-User-Id": user_id})
            assert get_res.status_code == 200
            assert get_res.json()["data"]["report_version"] == "2.0"
    finally:
        _cleanup_user(user_id)


def test_missing_prerequisites_returns_422_with_details():
    """Tests #5, #6, #7: missing #35, #36, or #37 returns 422 explaining which feature is missing."""
    user_id = str(uuid.uuid4())
    try:
        jd = _create_jd(user_id)
        res = client.post(f"{ENDPOINT}/{jd['id']}/report", headers={"X-User-Id": user_id})
        assert res.status_code == 422
        detail = res.json()["detail"]
        assert "Feature #35" in detail
        assert "Feature #36" in detail
        assert "Feature #37" in detail
    finally:
        _cleanup_user(user_id)


def test_authorization_and_user_isolation():
    """Test #12: missing auth -> 401, wrong user -> 403, missing job -> 404."""
    owner_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())
    try:
        jd = _create_jd(owner_id)
        assert client.post(f"{ENDPOINT}/{jd['id']}/report").status_code == 401
        assert client.post(f"{ENDPOINT}/{jd['id']}/report", headers={"X-User-Id": other_id}).status_code == 403
        assert client.get(f"{ENDPOINT}/{jd['id']}/report", headers={"X-User-Id": other_id}).status_code == 403
        assert client.post(f"{ENDPOINT}/{uuid.uuid4()}/report", headers={"X-User-Id": owner_id}).status_code == 404
    finally:
        _cleanup_user(owner_id)
        _cleanup_user(other_id)


def test_ollama_failure_and_malformed_insights():
    """Tests #8, #13: malformed AI JSON -> AIOutputValidationError (502); Ollama offline -> OllamaUnavailableError (503)."""
    gen = JobReportAIInsightsGenerator(base_url="http://localhost:11434", model="qwen2.5:3b")

    bad_llm = MagicMock()
    bad_llm.with_structured_output.return_value.ainvoke = AsyncMock(return_value="{bad json")
    with patch.object(gen, "_get_llm", return_value=bad_llm):
        try:
            asyncio.run(gen.generate_insights("Data Scientist", "Acme", {}))
            assert False, "Expected AIOutputValidationError"
        except AIOutputValidationError:
            pass

    down_llm = MagicMock()
    down_llm.with_structured_output.return_value.ainvoke = AsyncMock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    with patch.object(gen, "_get_llm", return_value=down_llm):
        try:
            asyncio.run(gen.generate_insights("Data Scientist", "Acme", {}))
            assert False, "Expected OllamaUnavailableError"
        except OllamaUnavailableError:
            pass

    user_id = str(uuid.uuid4())
    try:
        jd = _create_jd(user_id, job_title="Data Scientist")
        _seed_prerequisites(user_id, jd["id"], role_name="Data Scientist")
        with patch(
            "app.services.job_description_report.service.job_description_report_service.ai_insights_generator.generate_insights",
            new=AsyncMock(side_effect=OllamaUnavailableError("Ollama offline")),
        ):
            res_503 = client.post(f"{ENDPOINT}/{jd['id']}/report", headers={"X-User-Id": user_id})
            assert res_503.status_code == 503
    finally:
        _cleanup_user(user_id)
