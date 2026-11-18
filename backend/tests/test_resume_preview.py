"""
Tests for Resume Preview
Phase 2 | Feature 5: Resume Preview
"""

import io
import pytest
import fitz
import docx
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.storage import staging_service
from app.services.preview_service import preview_service, parse_structured_blocks
from app.schemas.preview import PreviewStatus

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
PREVIEW_ENDPOINT_TEMPLATE = f"{settings.API_V1_PREFIX}/resumes/{{resume_id}}/preview"
FILE_ENDPOINT_TEMPLATE = f"{settings.API_V1_PREFIX}/resumes/{{resume_id}}/file"


def create_pdf_bytes(text_lines: list[str]) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    y = 50
    for line in text_lines:
        page.insert_text((50, y), line)
        y += 25
    stream = doc.write()
    doc.close()
    return stream


def create_docx_bytes(title: str, paragraphs: list[str]) -> bytes:
    doc = docx.Document()
    doc.add_heading(title, level=0)
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_parse_structured_blocks_detects_headings_and_lists():
    text = (
        "Jane Doe\n"
        "Senior Cloud Architect\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Experienced software leader with 10 years building distributed applications.\n\n"
        "TECHNICAL SKILLS\n"
        "• Python, FastAPI, Docker\n"
        "• React, Tailwind CSS, Vite\n"
        "1. Cloud Architecture\n"
        "2. Database Optimization\n\n"
        "WORK EXPERIENCE\n"
        "Lead Engineer at CloudCorp from 2020 to Present."
    )
    blocks = parse_structured_blocks(text)
    types = [b.type for b in blocks]
    assert "heading" in types
    assert "list_item" in types
    assert "paragraph" in types

    heading_contents = [b.content for b in blocks if b.type == "heading"]
    assert "PROFESSIONAL SUMMARY" in heading_contents
    assert "TECHNICAL SKILLS" in heading_contents
    assert "WORK EXPERIENCE" in heading_contents

    list_contents = [b.content for b in blocks if b.type == "list_item"]
    assert any("Python" in c for c in list_contents)
    assert any("Cloud Architecture" in c for c in list_contents)


def test_preview_valid_pdf():
    pdf_bytes = create_pdf_bytes([
        "Jane Doe",
        "Senior Software Engineer",
        "PROFESSIONAL SUMMARY",
        "Expert in building resilient web applications and microservices.",
        "SKILLS",
        "* Python, TypeScript, React",
        "* PostgreSQL, Docker, AWS",
    ])

    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("Jane_Doe_Resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["data"]["upload_id"]

    try:
        preview_res = client.get(PREVIEW_ENDPOINT_TEMPLATE.format(resume_id=resume_id))
        assert preview_res.status_code == 200
        body = preview_res.json()
        assert body["success"] is True
        data = body["data"]

        assert data["resume_id"] == resume_id
        assert data["original_filename"] == "Jane_Doe_Resume.pdf"
        assert data["file_type"] == "pdf"
        assert data["preview_status"] == PreviewStatus.READY.value
        assert "Jane Doe" in data["cleaned_text"]
        assert len(data["blocks"]) > 0
        assert data["character_count"] > 0
        assert data["word_count"] > 0
        assert data["page_count"] == 1
        assert data["file_available"] is True
        assert f"/api/v1/resumes/{resume_id}/file" in data["file_view_url"]
    finally:
        staging_service.cleanup_file(resume_id)


def test_preview_valid_docx():
    docx_bytes = create_docx_bytes(
        "John Smith Resume",
        [
            "WORK EXPERIENCE",
            "Software Developer at TechFlow 2021-Present",
            "• Built automated CI/CD deployment pipelines",
            "• Reduced database query latency by 45%",
            "EDUCATION",
            "B.S. in Computer Science, State University",
        ],
    )

    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("John_Smith_CV.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["data"]["upload_id"]

    try:
        preview_res = client.get(PREVIEW_ENDPOINT_TEMPLATE.format(resume_id=resume_id))
        assert preview_res.status_code == 200
        body = preview_res.json()
        assert body["success"] is True
        data = body["data"]

        assert data["resume_id"] == resume_id
        assert data["original_filename"] == "John_Smith_CV.docx"
        assert data["file_type"] == "docx"
        assert data["preview_status"] == PreviewStatus.READY.value
        assert "John Smith Resume" in data["cleaned_text"]
        assert "WORK EXPERIENCE" in data["cleaned_text"]
        assert data["file_available"] is True
    finally:
        staging_service.cleanup_file(resume_id)


def test_preview_reuses_cached_extraction_and_cleaning():
    pdf_bytes = create_pdf_bytes(["Cached Test Candidate", "Full Stack Developer"])

    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("cached_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    resume_id = upload_res.json()["data"]["upload_id"]

    try:
        # Pre-extract and clean via endpoints
        client.post(f"{settings.API_V1_PREFIX}/resumes/{resume_id}/extract")
        client.post(f"{settings.API_V1_PREFIX}/resumes/{resume_id}/clean")

        cached_cleaning = preview_service.get_cached_cleaning(resume_id)
        assert cached_cleaning is not None

        # Fetch preview - should use cached results without error
        preview_res = client.get(PREVIEW_ENDPOINT_TEMPLATE.format(resume_id=resume_id))
        assert preview_res.status_code == 200
        data = preview_res.json()["data"]
        assert data["cleaned_text"] == cached_cleaning.cleaned_text
    finally:
        staging_service.cleanup_file(resume_id)


def test_preview_not_found():
    res = client.get(PREVIEW_ENDPOINT_TEMPLATE.format(resume_id="non-existent-uuid-12345"))
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_preview_rejects_path_traversal():
    res = client.get(f"{settings.API_V1_PREFIX}/resumes/..%2F..%2Fetc/preview")
    assert res.status_code in (400, 404)


def test_file_access_pdf_inline_and_download():
    pdf_bytes = create_pdf_bytes(["Test User Document Access", "Developer"])

    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("MyDocument.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    resume_id = upload_res.json()["data"]["upload_id"]

    try:
        # 1. Inline view access
        res_view = client.get(FILE_ENDPOINT_TEMPLATE.format(resume_id=resume_id))
        assert res_view.status_code == 200
        assert res_view.headers["content-type"] == "application/pdf"
        assert "inline" in res_view.headers["content-disposition"]
        assert "MyDocument.pdf" in res_view.headers["content-disposition"]
        assert len(res_view.content) > 0

        # 2. Download access
        res_down = client.get(f"{FILE_ENDPOINT_TEMPLATE.format(resume_id=resume_id)}?download=true")
        assert res_down.status_code == 200
        assert res_down.headers["content-type"] == "application/pdf"
        assert "attachment" in res_down.headers["content-disposition"]
        assert "MyDocument.pdf" in res_down.headers["content-disposition"]
    finally:
        staging_service.cleanup_file(resume_id)


def test_file_access_docx_download():
    docx_bytes = create_docx_bytes("Docx Download Test", ["Some content here"])

    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("TestDocument.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    resume_id = upload_res.json()["data"]["upload_id"]

    try:
        res = client.get(FILE_ENDPOINT_TEMPLATE.format(resume_id=resume_id))
        assert res.status_code == 200
        assert "wordprocessingml.document" in res.headers["content-type"]
        assert "attachment" in res.headers["content-disposition"]
        assert "TestDocument.docx" in res.headers["content-disposition"]
        assert len(res.content) > 0
    finally:
        staging_service.cleanup_file(resume_id)


def test_file_access_not_found():
    res = client.get(FILE_ENDPOINT_TEMPLATE.format(resume_id="non-existent-uuid-999"))
    assert res.status_code == 404


def test_file_access_rejects_path_traversal():
    res = client.get(f"{settings.API_V1_PREFIX}/resumes/..%2F..%2Fboot.ini/file")
    assert res.status_code in (400, 404)


def test_preview_long_resume_content():
    lines = ["Jane Doe - Principal Systems Architect"]
    lines.append("SUMMARY")
    lines.append("Seasoned technical leader with over a decade of software systems engineering experience.")
    lines.append("EXPERIENCE")
    for i in range(1, 20):
        lines.append(f"• Project {i}: Designed and deployed high-performance microservices architecture.")
    lines.append("EDUCATION")
    lines.append("Master of Science in Distributed Computing")

    pdf_bytes = create_pdf_bytes(lines)
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("Jane_Doe_Long_CV.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["data"]["upload_id"]

    try:
        preview_res = client.get(PREVIEW_ENDPOINT_TEMPLATE.format(resume_id=resume_id))
        assert preview_res.status_code == 200
        data = preview_res.json()["data"]
        assert data["preview_status"] == PreviewStatus.READY.value
        assert data["word_count"] > 50
        assert data["character_count"] > 300
        assert len(data["blocks"]) >= 15
        assert any(b["type"] == "heading" and b["content"] == "EXPERIENCE" for b in data["blocks"])
        assert any(b["type"] == "list_item" for b in data["blocks"])
    finally:
        staging_service.cleanup_file(resume_id)


def test_preview_scanned_pdf_empty_status():
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(50, 50, 400, 400), color=(0, 0, 0), fill=(0.7, 0.7, 0.7))
    scanned_bytes = doc.write()
    doc.close()

    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("Scanned_Image_Resume.pdf", io.BytesIO(scanned_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["data"]["upload_id"]

    try:
        preview_res = client.get(PREVIEW_ENDPOINT_TEMPLATE.format(resume_id=resume_id))
        assert preview_res.status_code == 200
        data = preview_res.json()["data"]
        # Empty text on scanned image returns EMPTY status
        assert data["preview_status"] == PreviewStatus.EMPTY.value
        assert data["cleaned_text"] == ""
    finally:
        staging_service.cleanup_file(resume_id)

