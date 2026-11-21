"""
API Integration Tests for Resume Achievement Analysis Endpoints
Phase 4 | Feature 26: Achievement Analysis
"""

import io
import uuid
import pytest
import fitz
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.schemas.achievement_analysis import (
    ResumeAchievementAIStructuredOutput,
    AchievementItemAI,
)

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_achievement_resume_pdf_bytes() -> bytes:
    """Generates a sample PDF resume with quantified accomplishments and unquantified duties."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Elena Rostova")
    page.insert_text((50, 70), "elena.rostova@example.com | (555) 789-0123 | Seattle, WA")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "Senior backend engineer with 5+ years of experience optimizing high-throughput distributed systems.")
    page.insert_text((50, 145), "WORK EXPERIENCE")
    page.insert_text((50, 160), "Lead Backend Engineer - CloudStream Systems (2022 - Present)")
    page.insert_text((50, 175), "- Reduced API p99 latency by 42% by redesigning Redis caching layer across 12 microservices.")
    page.insert_text((50, 190), "- Scaled streaming pipeline to process 3.5M daily events with 99.99% uptime.")
    page.insert_text((50, 205), "- Responsible for code reviews and sprint planning for the backend engineering squad.")
    page.insert_text((50, 235), "PROJECTS")
    page.insert_text((50, 250), "Distributed Task Queue (Open Source)")
    page.insert_text((50, 265), "- Engineered lightweight Python task broker with 500+ GitHub stars, serving 20+ production teams.")
    page.insert_text((50, 295), "HACKATHONS & AWARDS")
    page.insert_text((50, 310), "- 1st Place Winner at Global Cloud Hackathon 2023 out of 120 competing teams.")
    page.insert_text((50, 340), "CERTIFICATIONS")
    page.insert_text((50, 355), "- AWS Certified Solutions Architect - Professional (2023)")
    page.insert_text((50, 385), "EDUCATION")
    page.insert_text((50, 400), "Bachelor of Science in Computer Science - University of Washington (2018)")

    stream = doc.write()
    doc.close()
    return stream


def _upload_and_save_resume(filename: str = "elena_rostova_achievements.pdf") -> str:
    """Helper to upload and persist a resume, returning its permanent resume_id."""
    pdf_bytes = create_sample_achievement_resume_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201, save_res.text
    return save_res.json()["data"]["id"]


def mock_achievement_ai_output() -> ResumeAchievementAIStructuredOutput:
    return ResumeAchievementAIStructuredOutput(
        executive_summary="Candidate demonstrates exceptional engineering accomplishments with verified quantitative outcomes, including 42% latency reduction and top hackathon placement.",
        achievements=[
            AchievementItemAI(
                title="Redis Caching Redesign & Latency Reduction",
                category="experience",
                original_statement="Reduced API p99 latency by 42% by redesigning Redis caching layer across 12 microservices.",
                is_quantified=True,
                percentages=["42%"],
                numbers=["12 microservices"],
                time_saved=["42% latency reduction"],
                users_impacted=[],
                performance_gain=["p99 latency reduced by 42%"],
                has_verified_metrics=True,
                missing_metrics_note=None,
                evidence=["Reduced API p99 latency by 42%", "12 microservices"],
                impact_level="High",
                professional_relevance="High",
                quality_rating="Strong",
                suggested_statement="Reduced API p99 latency by 42% across 12 microservices by architecting an optimized Redis multi-tier caching system.",
                explanation="Demonstrates measurable architecture optimization with direct system throughput benefits.",
            ),
            AchievementItemAI(
                title="Event Pipeline Scaling to 3.5M Daily Events",
                category="experience",
                original_statement="Scaled streaming pipeline to process 3.5M daily events with 99.99% uptime.",
                is_quantified=True,
                percentages=["99.99%"],
                numbers=["3.5M daily events"],
                time_saved=[],
                users_impacted=["3.5M events/day"],
                performance_gain=["99.99% reliability"],
                has_verified_metrics=True,
                missing_metrics_note=None,
                evidence=["process 3.5M daily events", "99.99% uptime"],
                impact_level="High",
                professional_relevance="High",
                quality_rating="Strong",
                suggested_statement="Processed 3.5M daily events at 99.99% uptime by engineering a distributed fault-tolerant event streaming pipeline.",
                explanation="Exhibits production-grade high-availability infrastructure capabilities.",
            ),
            AchievementItemAI(
                title="Backend Sprint & Code Review Leadership",
                category="experience",
                original_statement="Responsible for code reviews and sprint planning for the backend engineering squad.",
                is_quantified=False,
                percentages=[],
                numbers=[],
                time_saved=[],
                users_impacted=[],
                performance_gain=[],
                has_verified_metrics=True,
                missing_metrics_note="Consider quantifying squad size (e.g. '8 engineers') and sprint velocity improvement or review SLA.",
                evidence=["Responsible for code reviews and sprint planning"],
                impact_level="Medium",
                professional_relevance="High",
                quality_rating="Moderate",
                suggested_statement="Maintained code quality and sprint delivery standards by leading weekly sprint planning and peer reviews for backend team.",
                explanation="Valid engineering responsibility that can be further elevated with team size and velocity metrics.",
            ),
            AchievementItemAI(
                title="Global Cloud Hackathon 1st Place",
                category="competitions",
                original_statement="1st Place Winner at Global Cloud Hackathon 2023 out of 120 competing teams.",
                is_quantified=True,
                percentages=[],
                numbers=["1st Place", "120 competing teams"],
                time_saved=[],
                users_impacted=[],
                performance_gain=[],
                has_verified_metrics=True,
                missing_metrics_note=None,
                evidence=["1st Place Winner", "120 competing teams"],
                impact_level="High",
                professional_relevance="High",
                quality_rating="Strong",
                suggested_statement="Achieved 1st Place out of 120 competitive international teams at Global Cloud Hackathon 2023 by engineering a serverless event platform.",
                explanation="Competitive recognition proving elite technical execution under time-constrained hackathon conditions.",
            ),
        ],
        category_highlights={
            "experience": "Strong operational metrics with verified latency and throughput enhancements.",
            "competitions": "First-place recognition demonstrating elite problem-solving under deadline constraints.",
        },
    )


def test_achievement_analysis_api_lifecycle():
    """Tests complete achievement analysis lifecycle: upload, 404 before analyze, analyze, and retrieval."""
    # 1. Upload & save resume
    resume_id = _upload_and_save_resume("test_achievement_lifecycle.pdf")

    # 2. GET before analysis should return 404
    get_res_before = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/achievements/analysis")
    assert get_res_before.status_code == 404

    # 3. POST /analyze with mocked AI evaluator
    with patch(
        "app.services.achievement_analysis.service.achievement_analysis_service.ai_evaluator.evaluate_achievements",
        new=AsyncMock(return_value=mock_achievement_ai_output()),
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/achievements/analyze?force_recalculate=true")
        assert analyze_res.status_code == 200, analyze_res.text
        data = analyze_res.json()["data"]

        assert data["resume_id"] == resume_id
        assert 0 <= data["achievement_score"] <= 100
        assert data["score_grade"] in ["Exceptional", "Strong", "Moderate", "Developing"]
        assert data["total_achievements_count"] == 4
        assert data["quantified_count"] == 3
        assert data["unquantified_count"] == 1
        assert data["quantification_rate"] == 75.0

        # Rubric breakdown checks
        rubric = data["rubric_breakdown"]
        assert "quantification_rate_score" in rubric
        assert "impact_magnitude_score" in rubric
        assert "cross_category_diversity_score" in rubric
        assert "action_clarity_score" in rubric
        assert "metric_verification_fidelity_score" in rubric
        assert rubric["total_score"] == data["achievement_score"]

        # Achievements list checks
        achievements = data["achievements"]
        assert len(achievements) == 4
        item0 = achievements[0]
        assert item0["id"] is not None
        assert item0["category"] in ["experience", "academic_projects", "projects", "competitions", "awards", "certifications", "leadership"]
        assert item0["category_name"] is not None
        assert item0["is_quantified"] is True
        assert len(item0["measurable_metrics"]["percentages"]) > 0 or len(item0["measurable_metrics"]["numbers"]) > 0
        assert item0["suggested_statement"].startswith("Reduced") or len(item0["suggested_statement"]) > 10
        assert item0["quality_rating"] in ["Strong", "Moderate", "Weak"]

        # Category breakdown checks
        category_breakdown = data["category_breakdown"]
        assert isinstance(category_breakdown, dict)
        exp_cat = category_breakdown.get("experience")
        assert exp_cat is not None
        assert exp_cat["total_count"] == 3
        assert exp_cat["quantified_count"] == 2
        assert exp_cat["unquantified_count"] == 1

    # 4. GET after analysis retrieves cached result
    get_res_after = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/achievements/analysis")
    assert get_res_after.status_code == 200
    retrieved_data = get_res_after.json()["data"]
    assert retrieved_data["achievement_score"] == data["achievement_score"]
    assert retrieved_data["total_achievements_count"] == data["total_achievements_count"]

    # 5. GET alias endpoint also returns 200
    alias_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/achievement-analysis")
    assert alias_res.status_code == 200
    assert alias_res.json()["data"]["achievement_score"] == data["achievement_score"]


def test_achievement_analysis_nonexistent_resume():
    """Verify 404 response for invalid/non-existent resume UUID."""
    fake_id = str(uuid.uuid4())
    res_analyze = client.post(f"{RESUMES_ENDPOINT}/{fake_id}/achievements/analyze")
    assert res_analyze.status_code == 404

    res_get = client.get(f"{RESUMES_ENDPOINT}/{fake_id}/achievements/analysis")
    assert res_get.status_code == 404


def test_achievement_analysis_fallback_resilience():
    """Verify that if Ollama / AI is unavailable, deterministic fallback extracts achievements and produces valid score."""
    resume_id = _upload_and_save_resume("test_achievement_fallback.pdf")

    # In standard test environment, Ollama may be offline or we force an exception in ChatOllama
    with patch(
        "langchain_ollama.ChatOllama.with_structured_output",
        side_effect=Exception("Ollama connection failed"),
    ):
        res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/achievements/analyze?force_recalculate=true")
        assert res.status_code == 200, res.text
        data = res.json()["data"]

        # Fallback should extract accomplishments using deterministic regex & section parsers
        assert data["resume_id"] == resume_id
        assert 0 <= data["achievement_score"] <= 100
        assert data["total_achievements_count"] > 0
        assert data["quantification_rate"] >= 0
        assert len(data["achievements"]) > 0
        assert data["achievements"][0]["suggested_statement"] is not None
        assert data["achievements"][0]["category"] in [
            "experience", "academic_projects", "projects", "competitions",
            "awards", "certifications", "leadership"
        ]


def test_achievement_analysis_preserves_original_resume():
    """Verify that analyzing achievements never mutates or overwrites original resume text."""
    resume_id = _upload_and_save_resume("test_achievement_preserve.pdf")

    # Get preview before
    preview_before = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/preview").json()["data"]

    # Run achievement analysis
    with patch(
        "app.services.achievement_analysis.service.achievement_analysis_service.ai_evaluator.evaluate_achievements",
        new=AsyncMock(return_value=mock_achievement_ai_output()),
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/achievements/analyze?force_recalculate=true")
        assert analyze_res.status_code == 200

    # Get preview after
    preview_after = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/preview").json()["data"]

    # Text must be completely identical
    assert preview_before["cleaned_text"] == preview_after["cleaned_text"]
