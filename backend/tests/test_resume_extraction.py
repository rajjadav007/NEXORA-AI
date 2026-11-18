"""
API Integration tests for Resume Text Extraction.
Phase 2 | Feature 3: Resume Text Extraction (All Tasks 1-6)
"""

import io
import pytest
import fitz
import docx
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.storage import staging_service
from app.schemas.extraction import ExtractionStatus

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
EXTRACT_ENDPOINT_TEMPLATE = f"{settings.API_V1_PREFIX}/resumes/{{resume_id}}/extract"


def create_pdf_bytes(text_lines: list[str]) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    y = 50
    for line in text_lines:
        page.insert_text((50, y), line)
        y += 30
    stream = doc.write()
    doc.close()
    return stream


def create_scanned_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    # Draw gray rectangle without any text
    page.draw_rect(fitz.Rect(50, 50, 400, 400), color=(0, 0, 0), fill=(0.7, 0.7, 0.7))
    stream = doc.write()
    doc.close()
    return stream


def create_docx_bytes(title: str, paragraphs: list[str], table_rows: list[list[str]] = None) -> bytes:
    doc = docx.Document()
    doc.add_heading(title, level=0)
    for p in paragraphs:
        doc.add_paragraph(p)
    if table_rows:
        t = doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
        for r_idx, row_vals in enumerate(table_rows):
            for c_idx, val in enumerate(row_vals):
                t.rows[r_idx].cells[c_idx].text = val
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_api_extract_valid_pdf():
    pdf_bytes = create_pdf_bytes([
        "Jane Doe - Staff Cloud Architect",
        "Experience: 8 years building enterprise distributed systems",
        "SKILLS: Python, FastAPI, Kubernetes, AWS, PostgreSQL",
    ])

    # 1. Upload and stage
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("Jane_Doe_Resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    upload_id = upload_res.json()["data"]["upload_id"]

    try:
        # 2. Call extraction endpoint
        extract_res = client.post(EXTRACT_ENDPOINT_TEMPLATE.format(resume_id=upload_id))
        assert extract_res.status_code == 200

        data = extract_res.json()
        assert data["success"] is True
        payload = data["data"]

        assert payload["extraction_id"] is not None
        assert payload["resume_id"] == upload_id
        assert payload["original_filename"] == "Jane_Doe_Resume.pdf"
        assert payload["file_type"] == "pdf"
        assert payload["extraction_status"] == ExtractionStatus.SUCCESS
        assert payload["extraction_method"] == "pymupdf"
        assert payload["page_count"] == 1
        assert payload["character_count"] > 0
        assert payload["word_count"] > 0
        assert "Jane Doe" in payload["raw_text"]
        assert "Staff Cloud Architect" in payload["raw_text"]
        assert len(payload["pages"]) == 1
        assert payload["pages"][0]["page_number"] == 1

        # Path leakage check
        assert "storage" not in str(payload).lower()
        assert "backend" not in str(payload).lower()

    finally:
        staging_service.cleanup_file(upload_id)


def test_api_extract_valid_docx():
    docx_bytes = create_docx_bytes(
        title="Marcus Vance - Lead Engineer",
        paragraphs=[
            "Summary: Expert in backend engineering and cloud architecture.",
            "• Designed microservices serving 10M daily active users.",
            "• Implemented zero-downtime database migration pipelines.",
        ],
        table_rows=[
            ["Skill", "Proficiency", "Experience"],
            ["Python", "Expert", "7 Years"],
            ["FastAPI", "Advanced", "4 Years"],
        ],
    )

    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={
            "file": (
                "Marcus_Vance_Resume.docx",
                io.BytesIO(docx_bytes),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload_res.status_code == 200
    upload_id = upload_res.json()["data"]["upload_id"]

    try:
        extract_res = client.post(EXTRACT_ENDPOINT_TEMPLATE.format(resume_id=upload_id))
        assert extract_res.status_code == 200

        data = extract_res.json()
        assert data["success"] is True
        payload = data["data"]

        assert payload["extraction_id"] is not None
        assert payload["resume_id"] == upload_id
        assert payload["original_filename"] == "Marcus_Vance_Resume.docx"
        assert payload["file_type"] == "docx"
        assert payload["extraction_status"] == ExtractionStatus.SUCCESS
        assert payload["extraction_method"] == "python-docx"
        assert "Marcus Vance" in payload["raw_text"]
        assert "Python | Expert | 7 Years" in payload["raw_text"]
        assert len(payload["blocks"]) >= 4

    finally:
        staging_service.cleanup_file(upload_id)


def test_api_extract_scanned_pdf_detects_no_text():
    scanned_bytes = create_scanned_pdf_bytes()

    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("scanned_resume.pdf", io.BytesIO(scanned_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    upload_id = upload_res.json()["data"]["upload_id"]

    try:
        extract_res = client.post(EXTRACT_ENDPOINT_TEMPLATE.format(resume_id=upload_id))
        assert extract_res.status_code == 200

        data = extract_res.json()
        assert data["success"] is True
        payload = data["data"]

        assert payload["extraction_status"] == ExtractionStatus.NO_SELECTABLE_TEXT
        assert payload["character_count"] == 0
        assert payload["word_count"] == 0
        assert payload["raw_text"] == ""
        assert "NO_SELECTABLE_TEXT" in data["message"]

    finally:
        staging_service.cleanup_file(upload_id)


def test_api_extract_non_existent_resume_id():
    extract_res = client.post(EXTRACT_ENDPOINT_TEMPLATE.format(resume_id="non-existent-uuid-12345"))
    assert extract_res.status_code == 404
    assert "not found" in extract_res.json()["detail"].lower()
