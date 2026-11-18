"""Integration tests for Resume Text Cleaning endpoint."""

import io
import fitz
import docx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.storage import staging_service
from app.schemas.cleaning import CleaningStatus

client = TestClient(app)


def create_minimal_pdf_with_text(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_minimal_docx_with_text(text: str) -> bytes:
    doc = docx.Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


@pytest.fixture(autouse=True)
def cleanup_staging_files():
    yield
    for p in staging_service.staging_dir.glob("*"):
        if p.is_file():
            try:
                p.unlink()
            except OSError:
                pass


def test_clean_endpoint_from_staged_pdf():
    pdf_text = (
        "John Doe  \n"
        "Senior   Developer\n\n\n"
        "EXPERIENCE\n"
        "- Experience with C++ and C#\n"
        "- Experience with Node.js and .NET\n"
        "Contact: john@example.com"
    )
    pdf_bytes = create_minimal_pdf_with_text(pdf_text)

    # 1. Upload & validate
    upload_res = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("candidate_resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 200
    upload_id = upload_res.json()["data"]["upload_id"]

    # 2. Call clean endpoint with no body (auto-extract from staged file)
    clean_res = client.post(f"/api/v1/resumes/{upload_id}/clean")
    assert clean_res.status_code == 200
    res_data = clean_res.json()

    assert res_data["success"] is True
    data = res_data["data"]
    assert data["resume_id"] == upload_id
    assert data["cleaning_status"] in (CleaningStatus.SUCCESS.value, CleaningStatus.NO_CHANGE.value)

    cleaned = data["cleaned_text"]
    assert "C++" in cleaned
    assert "C#" in cleaned
    assert "Node.js" in cleaned
    assert ".NET" in cleaned
    assert "john@example.com" in cleaned
    assert "• Experience with C++ and C#" in cleaned


def test_clean_endpoint_from_staged_docx():
    docx_text = (
        "Jane Smith\n"
        "Lead Engineer\n"
        "SKILLS\n"
        "* Python & CI/CD pipelines\n"
        "* HTML/CSS architecture"
    )
    docx_bytes = create_minimal_docx_with_text(docx_text)

    upload_res = client.post(
        "/api/v1/resumes/upload",
        files={
            "file": (
                "resume.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload_res.status_code == 200
    upload_id = upload_res.json()["data"]["upload_id"]

    clean_res = client.post(f"/api/v1/resumes/{upload_id}/clean")
    assert clean_res.status_code == 200
    res_data = clean_res.json()
    assert res_data["success"] is True

    cleaned = res_data["data"]["cleaned_text"]
    assert "CI/CD" in cleaned
    assert "HTML/CSS" in cleaned
    assert "• Python & CI/CD pipelines" in cleaned


def test_clean_endpoint_with_explicit_raw_text():
    body = {
        "raw_text": (
            "Alex  Taylor  \r\n\r\n"
            "\u201cFull-Stack Specialist\u201d\r\n"
            "EXPERIENCE\r\n"
            "- Built REST APIs with Vue.js & Node.js\r\n"
            "- Built REST APIs with Vue.js & Node.js\r\n"
            "1) Deployed to Kubernetes\r\n"
            "Email: alex.t@domain.io"
        )
    }

    clean_res = client.post(
        "/api/v1/resumes/explicit-text-id/clean",
        json=body,
    )
    assert clean_res.status_code == 200
    data = clean_res.json()["data"]
    cleaned = data["cleaned_text"]

    # Check normalization
    assert '"Full-Stack Specialist"' in cleaned
    assert "• Built REST APIs with Vue.js & Node.js" in cleaned
    assert "1. Deployed to Kubernetes" in cleaned
    # Check deduplication
    assert cleaned.count("• Built REST APIs with Vue.js & Node.js") == 1
    # Check technical terms
    assert "Vue.js" in cleaned
    assert "Node.js" in cleaned
    assert "alex.t@domain.io" in cleaned


def test_clean_endpoint_not_found():
    res = client.post("/api/v1/resumes/00000000-0000-0000-0000-000000000000/clean")
    assert res.status_code == 404
    assert "Resume file not found" in res.json()["detail"]


def test_clean_endpoint_empty_raw_text():
    body = {"raw_text": "   \n\n\t  "}
    res = client.post("/api/v1/resumes/empty-test/clean", json=body)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["cleaning_status"] == CleaningStatus.EMPTY_INPUT.value
    assert data["cleaned_text"] == ""
