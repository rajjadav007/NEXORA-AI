"""
API Integration Tests for Resume Grammar & Clarity Analysis Endpoints
Phase 4 | Feature 25: Grammar & Clarity Analysis
"""

import io
import uuid
import pytest
import fitz
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.schemas.grammar_analysis import (
    ResumeGrammarAIStructuredOutput,
    GrammarIssueAI,
    SentenceComparisonAI,
)

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"


def create_sample_resume_pdf_bytes() -> bytes:
    """Generates a sample PDF resume with intentional grammar and passive tone."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Devon Vance")
    page.insert_text((50, 70), "devon.vance@example.com | (555) 234-5678 | San Francisco, CA")
    page.insert_text((50, 100), "PROFESSIONAL SUMMARY")
    page.insert_text((50, 115), "I am a hardworking engineer which is responsible for building web apps successfully.")
    page.insert_text((50, 145), "WORK EXPERIENCE")
    page.insert_text((50, 160), "Software Developer - FinScale Inc (2021 - Present)")
    page.insert_text((50, 175), "- I helped with fixing bugs and was responsible for maintaining servers daily.")
    page.insert_text((50, 190), "- Worked on various different frontend tasks using React in order to satisfy clients.")
    page.insert_text((50, 220), "EDUCATION")
    page.insert_text((50, 235), "Bachelor of Science in Computer Science - UC Berkeley (2017 - 2021)")
    page.insert_text((50, 265), "TECHNICAL SKILLS")
    page.insert_text((50, 280), "Python, JavaScript, React, FastAPI, PostgreSQL, Git")

    stream = doc.write()
    doc.close()
    return stream


def _upload_and_save_resume(filename: str = "devon_vance_grammar.pdf") -> str:
    """Helper to upload and persist a resume, returning its permanent resume_id."""
    pdf_bytes = create_sample_resume_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200, upload_res.text
    staging_id = upload_res.json()["data"]["upload_id"]
    save_res = client.post(f"{RESUMES_ENDPOINT}/{staging_id}/save")
    assert save_res.status_code == 201, save_res.text
    return save_res.json()["data"]["id"]


def mock_grammar_ai_output() -> ResumeGrammarAIStructuredOutput:
    return ResumeGrammarAIStructuredOutput(
        overall_assessment="Resume possesses strong technical foundations but suffers from first-person pronouns, passive duty constructions, and redundant filler words.",
        issues=[
            GrammarIssueAI(
                original_text="I am a hardworking engineer which is responsible for building web apps successfully",
                suggested_text="Full Stack Software Engineer specializing in scalable, high-availability web applications",
                category="tone",
                explanation="Eliminate first-person pronoun 'I' and replace casual claim with targeted technical specialization.",
                severity="High",
                section="Professional Summary",
            ),
            GrammarIssueAI(
                original_text="I helped with fixing bugs and was responsible for maintaining servers daily",
                suggested_text="Engineered automated defect remediation and maintained 99.9% server uptime across production environments",
                category="clarity",
                explanation="Replace passive phrasing ('helped with', 'was responsible for') with authoritative outcome-oriented action verbs.",
                severity="High",
                section="Work Experience",
            ),
            GrammarIssueAI(
                original_text="various different frontend tasks in order to",
                suggested_text="frontend features to",
                category="wordiness",
                explanation="'Various different' is redundant; 'in order to' can be simplified to 'to'.",
                severity="Low",
                section="Work Experience",
            ),
        ],
        sentence_comparisons=[
            SentenceComparisonAI(
                original_sentence="I helped with fixing bugs and was responsible for maintaining servers daily.",
                improved_sentence="Maintained 99.9% production server uptime and resolved critical software defects.",
                reason="Converts passive duties into quantifiable, professional achievements without first-person pronouns.",
                section="Work Experience",
            ),
            SentenceComparisonAI(
                original_sentence="Worked on various different frontend tasks using React in order to satisfy clients.",
                improved_sentence="Developed high-performance client-facing React interfaces, enhancing user satisfaction.",
                reason="Removes filler wording and sharpens technical diction.",
                section="Work Experience",
            ),
        ],
        readability_summary="Good base reading speed with concise bullet lengths.",
    )


def test_grammar_analysis_api_lifecycle():
    """Tests complete grammar analysis lifecycle: upload, 404 before analyze, analyze, and retrieval."""
    # 1. Upload & save resume
    resume_id = _upload_and_save_resume("test_grammar_lifecycle.pdf")

    # 2. GET before analysis should return 404
    get_res_before = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/grammar")
    assert get_res_before.status_code == 404

    # 3. POST /analyze with mocked AI evaluator
    with patch(
        "app.services.grammar_analysis.service.grammar_analysis_service.ai_evaluator.evaluate_grammar",
        new=AsyncMock(return_value=mock_grammar_ai_output())
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/grammar/analyze?force_recalculate=true")
        assert analyze_res.status_code == 200, analyze_res.text
        data = analyze_res.json()["data"]

        assert data["resume_id"] == resume_id
        assert 0 <= data["writing_score"] <= 100
        assert data["writing_grade"] in ["Excellent", "Professional", "Needs Polish", "Needs Substantial Revision"]

        # Readability metrics
        assert "readability_score" in data["readability_metrics"]
        assert "grade_level" in data["readability_metrics"]
        assert data["readability_metrics"]["total_words"] > 0

        # Issues
        assert len(data["issues"]) == 3
        assert data["issues"][0]["category"] in ["tone", "clarity", "wordiness", "grammar", "spelling"]
        assert len(data["issues"][0]["original_text"]) > 0
        assert len(data["issues"][0]["suggested_text"]) > 0
        assert data["issues"][0]["severity"] in ["High", "Medium", "Low"]

        # Sentence comparisons
        assert len(data["sentence_comparisons"]) == 2
        assert len(data["sentence_comparisons"][0]["original_sentence"]) > 0
        assert len(data["sentence_comparisons"][0]["improved_sentence"]) > 0
        assert len(data["sentence_comparisons"][0]["reason"]) > 0

        # Category counts
        assert "tone" in data["category_counts"]
        assert "clarity" in data["category_counts"]

    # 4. GET /grammar should return 200 with saved analysis
    get_res_after = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/grammar")
    assert get_res_after.status_code == 200
    retrieved = get_res_after.json()["data"]
    assert retrieved["resume_id"] == resume_id
    assert retrieved["writing_score"] == data["writing_score"]
    assert len(retrieved["issues"]) == 3
    assert len(retrieved["sentence_comparisons"]) == 2


def test_grammar_analysis_non_existent_resume():
    """Verify 404 for non-existent resume ID."""
    fake_id = str(uuid.uuid4())
    res_get = client.get(f"{RESUMES_ENDPOINT}/{fake_id}/grammar")
    assert res_get.status_code == 404

    res_post = client.post(f"{RESUMES_ENDPOINT}/{fake_id}/grammar/analyze")
    assert res_post.status_code == 404


def test_grammar_analysis_offline_fallback():
    """Verify that grammar analysis falls back smoothly if Ollama is unavailable."""
    resume_id = _upload_and_save_resume("test_grammar_offline.pdf")

    analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/grammar/analyze?force_recalculate=true")
    assert analyze_res.status_code == 200
    data = analyze_res.json()["data"]
    assert data["resume_id"] == resume_id
    assert data["writing_score"] > 0
    assert "readability_metrics" in data
    assert len(data["sentence_comparisons"]) >= 1


def test_grammar_analysis_preserves_original_resume():
    """Verify that running grammar analysis never mutates or overwrites original resume text."""
    resume_id = _upload_and_save_resume("test_grammar_preserve.pdf")

    # Get preview before
    preview_before = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/preview").json()["data"]

    # Run grammar analysis
    with patch(
        "app.services.grammar_analysis.service.grammar_analysis_service.ai_evaluator.evaluate_grammar",
        new=AsyncMock(return_value=mock_grammar_ai_output())
    ):
        analyze_res = client.post(f"{RESUMES_ENDPOINT}/{resume_id}/grammar/analyze?force_recalculate=true")
        assert analyze_res.status_code == 200

    # Get preview after
    preview_after = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/preview").json()["data"]

    # Text must be completely identical
    assert preview_before["cleaned_text"] == preview_after["cleaned_text"]
    assert preview_before["word_count"] == preview_after["word_count"]
