"""
Integration & Unit Tests for Mandatory & Preferred Skills Classification
Phase 6 | Feature 37: Mandatory & Preferred Skills Classification
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
from app.models.job_skill_classification import JobSkillClassification
from app.models.user import User
from app.schemas.job_requirement_analysis import (
    EducationRequirementSchema,
    ExperienceRequirementSchema,
    ExtractedRequirementItem,
    JobRequirementAIStructuredOutput,
)
from app.schemas.job_skill_classification import (
    ClassifiedSkillItem,
    SkillClassificationAIStructuredOutput,
)
from app.services.job_skill_classification.ai_classifier import SkillClassificationAIExtractor
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
        for model in (JobSkillClassification, JobRequirementAnalysis, JobDescription):
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
        "Must have Python programming skills. Experience with LangChain is preferred. "
        "Knowledge of Docker is optional. Exposure to Kubernetes is mentioned."
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


def _sample_f36_output() -> JobRequirementAIStructuredOutput:
    return JobRequirementAIStructuredOutput(
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
                name="LangChain",
                category="AI Framework",
                importance="Preferred",
                evidence="Experience with LangChain is preferred",
                confidence=0.95,
                source_type="explicit",
            ),
        ],
        education=EducationRequirementSchema(),
        experience=ExperienceRequirementSchema(),
        soft_skills=[],
        domain_knowledge=[],
        other_requirements=[],
    )


def test_mandatory_preferred_optional_ambiguous_and_db_persistence():
    """Tests #1, #2, #3, #4, #7, #8, #12, #15: classifications, categories, missing proficiency, DB persistence, F36 integration."""
    user_id = str(uuid.uuid4())
    mock_f36 = _sample_f36_output()
    mock_f37 = SkillClassificationAIStructuredOutput(
        skills=[
            ClassifiedSkillItem(
                name="Python",
                category="Programming Language",
                classification="Mandatory",
                priority_score=95,
                expected_proficiency="Intermediate",
                evidence="Must have Python programming skills",
                source_type="explicit",
                confidence_score=0.98,
            ),
            ClassifiedSkillItem(
                name="LangChain",
                category="AI Framework",
                classification="Preferred",
                priority_score=65,
                expected_proficiency="Unspecified",
                evidence="Experience with LangChain is preferred",
                source_type="explicit",
                confidence_score=0.95,
            ),
            ClassifiedSkillItem(
                name="Docker",
                category="Tool & Platform",
                classification="Optional",
                priority_score=25,
                expected_proficiency="Unspecified",
                evidence="Knowledge of Docker is optional",
                source_type="explicit",
                confidence_score=0.88,
            ),
            ClassifiedSkillItem(
                name="Kubernetes",
                category="Tool & Platform",
                classification="Unspecified",
                priority_score=50,  # Should be forced to None for Unspecified
                expected_proficiency="Unspecified",
                evidence="Exposure to Kubernetes is mentioned",
                source_type="inferred",
                confidence_score=0.60,
            ),
        ]
    )

    try:
        jd = _create_jd(user_id)
        with (
            patch(
                "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
                new=AsyncMock(return_value=mock_f36),
            ) as f36_mock,
            patch(
                "app.services.job_skill_classification.service.job_skill_classification_service.ai_classifier.classify_skills",
                new=AsyncMock(return_value=mock_f37),
            ),
        ):
            res = client.post(
                f"{ENDPOINT}/{jd['id']}/skills-classification",
                headers={"X-User-Id": user_id},
            )
            assert res.status_code == 200, res.text
            f36_mock.assert_awaited_once()
            data = res.json()["data"]
            assert data["job_id"] == jd["id"]
            assert data["cached"] is False
            assert data["classification_summary"] == {
                "mandatory_count": 1,
                "preferred_count": 1,
                "optional_count": 1,
                "unspecified_count": 1,
                "total_skills": 4,
            }

            by_name = {s["name"]: s for s in data["skills"]}
            assert by_name["Python"]["classification"] == "Mandatory"
            assert by_name["Python"]["priority_score"] == 95
            assert by_name["Python"]["priority_level"] == "High"
            assert by_name["Python"]["expected_proficiency"] == "Intermediate"

            assert by_name["LangChain"]["classification"] == "Preferred"
            assert by_name["LangChain"]["priority_score"] == 65
            assert by_name["LangChain"]["priority_level"] == "Medium"
            assert by_name["LangChain"]["expected_proficiency"] == "Unspecified"

            assert by_name["Docker"]["classification"] == "Optional"
            assert by_name["Docker"]["priority_score"] == 25
            assert by_name["Docker"]["priority_level"] == "Low"

            assert by_name["Kubernetes"]["classification"] == "Unspecified"
            assert by_name["Kubernetes"]["priority_score"] is None
            assert by_name["Kubernetes"]["priority_level"] == "Low"

            # Verify GET returns persisted DB record
            get_res = client.get(
                f"{ENDPOINT}/{jd['id']}/skills-classification",
                headers={"X-User-Id": user_id},
            )
            assert get_res.status_code == 200
            assert get_res.json()["data"]["cached"] is True
            assert len(get_res.json()["data"]["skills"]) == 4
    finally:
        _cleanup_user(user_id)


def test_conflicting_statements_and_duplicate_skills_normalization():
    """Tests #5, #6: duplicate skills (via alias normalization) and conflicting statements resolve cleanly."""
    output = SkillClassificationAIStructuredOutput(
        skills=[
            ClassifiedSkillItem(
                name="Python3",
                category="Programming Language",
                classification="Preferred",
                priority_score=60,
                evidence="Python3 is nice to have",
                source_type="inferred",
                confidence_score=0.75,
            ),
            ClassifiedSkillItem(
                name="Python",
                category="Programming Language",
                classification="Mandatory",
                priority_score=95,
                evidence="Candidates must have Python experience",
                source_type="explicit",
                confidence_score=0.98,
            ),
            ClassifiedSkillItem(
                name="JS",
                category="Programming Language",
                classification="Preferred",
                priority_score=70,
                evidence="JS is preferred",
                source_type="explicit",
                confidence_score=0.90,
            ),
        ]
    )
    assert len(output.skills) == 2
    by_name = {s.name: s for s in output.skills}
    assert by_name["Python"].classification == "Mandatory"
    assert by_name["Python"].priority_score == 95
    assert by_name["JavaScript"].original_name == "JS"


def test_repeated_classification_uses_cache_and_force_recalculate():
    """Tests #13, #15: repeated classification uses cache and reuses existing Feature #36 without re-running F36."""
    user_id = str(uuid.uuid4())
    mock_f36 = _sample_f36_output()
    mock_f37 = SkillClassificationAIStructuredOutput(
        skills=[
            ClassifiedSkillItem(
                name="Python",
                category="Programming Language",
                classification="Mandatory",
                priority_score=92,
                evidence="Must have Python",
                source_type="explicit",
                confidence_score=0.97,
            )
        ]
    )

    try:
        jd = _create_jd(user_id)
        with (
            patch(
                "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
                new=AsyncMock(return_value=mock_f36),
            ) as f36_mock,
            patch(
                "app.services.job_skill_classification.service.job_skill_classification_service.ai_classifier.classify_skills",
                new=AsyncMock(return_value=mock_f37),
            ) as f37_mock,
        ):
            # First run
            res1 = client.post(
                f"{ENDPOINT}/{jd['id']}/skills-classification",
                headers={"X-User-Id": user_id},
            )
            assert res1.status_code == 200
            assert res1.json()["data"]["cached"] is False
            assert f36_mock.await_count == 1
            assert f37_mock.await_count == 1

            # Second run -> cached, no AI calls
            res2 = client.post(
                f"{ENDPOINT}/{jd['id']}/skills-classification",
                headers={"X-User-Id": user_id},
            )
            assert res2.status_code == 200
            assert res2.json()["data"]["cached"] is True
            assert f36_mock.await_count == 1
            assert f37_mock.await_count == 1

            # Force recalculate -> calls F37, still reuses saved F36
            res3 = client.post(
                f"{ENDPOINT}/{jd['id']}/skills-classification?force_recalculate=true",
                headers={"X-User-Id": user_id},
            )
            assert res3.status_code == 200
            assert res3.json()["data"]["cached"] is False
            assert f36_mock.await_count == 1
            assert f37_mock.await_count == 2
    finally:
        _cleanup_user(user_id)


def test_unauthorized_and_user_data_isolation():
    """Tests #11, #14: unauthorized job ID and cross-user isolation."""
    owner_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())
    try:
        jd = _create_jd(owner_id)

        # Missing user header -> 401
        unauth_res = client.post(f"{ENDPOINT}/{jd['id']}/skills-classification")
        assert unauth_res.status_code == 401

        # Another user -> 403 Forbidden (isolation)
        other_post = client.post(
            f"{ENDPOINT}/{jd['id']}/skills-classification",
            headers={"X-User-Id": other_id},
        )
        assert other_post.status_code == 403

        other_get = client.get(
            f"{ENDPOINT}/{jd['id']}/skills-classification",
            headers={"X-User-Id": other_id},
        )
        assert other_get.status_code == 403

        # Non-existent job ID -> 404
        missing_post = client.post(
            f"{ENDPOINT}/{uuid.uuid4()}/skills-classification",
            headers={"X-User-Id": owner_id},
        )
        assert missing_post.status_code == 404
    finally:
        _cleanup_user(owner_id)
        _cleanup_user(other_id)


def test_malformed_ai_json_and_ollama_unavailable():
    """Tests #9, #10: malformed AI JSON -> AIOutputValidationError (502); Ollama unavailable -> OllamaUnavailableError (503)."""
    extractor = SkillClassificationAIExtractor(base_url="http://localhost:11434", model="qwen2.5:3b")

    # Malformed JSON
    bad_llm = MagicMock()
    bad_llm.with_structured_output.return_value.ainvoke = AsyncMock(return_value="{not valid json")
    with patch.object(extractor, "_get_llm", return_value=bad_llm):
        try:
            asyncio.run(extractor.classify_skills("Must have Python", []))
            assert False, "Expected AIOutputValidationError"
        except AIOutputValidationError:
            pass

    # Ollama unavailable
    down_llm = MagicMock()
    down_llm.with_structured_output.return_value.ainvoke = AsyncMock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    with patch.object(extractor, "_get_llm", return_value=down_llm):
        try:
            asyncio.run(extractor.classify_skills("Must have Python", []))
            assert False, "Expected OllamaUnavailableError"
        except OllamaUnavailableError:
            pass

    # Endpoint HTTP status mapping for 503 & 502
    user_id = str(uuid.uuid4())
    try:
        jd = _create_jd(user_id)
        with (
            patch(
                "app.services.job_requirement_extraction.service.job_requirement_extraction_service.ai_extractor.extract_requirements",
                new=AsyncMock(return_value=_sample_f36_output()),
            ),
            patch(
                "app.services.job_skill_classification.service.job_skill_classification_service.ai_classifier.classify_skills",
                new=AsyncMock(side_effect=OllamaUnavailableError("Ollama offline")),
            ),
        ):
            res_503 = client.post(
                f"{ENDPOINT}/{jd['id']}/skills-classification",
                headers={"X-User-Id": user_id},
            )
            assert res_503.status_code == 503
    finally:
        _cleanup_user(user_id)
