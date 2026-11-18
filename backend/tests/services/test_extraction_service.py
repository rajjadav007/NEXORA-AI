"""
Unit tests for ExtractionService.
Phase 2 | Feature 3: Resume Text Extraction (Task 3, 5, 6)
"""

import pytest
from pathlib import Path
import fitz
import docx

from app.services.extraction.extraction_service import extraction_service
from app.schemas.extraction import ExtractionStatus


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Jane Developer\nExpert in Python & FastAPI")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def sample_docx(tmp_path: Path) -> Path:
    docx_path = tmp_path / "sample.docx"
    doc = docx.Document()
    doc.add_heading("John Engineer", 0)
    doc.add_paragraph("Specialized in scalable distributed backends")
    doc.save(str(docx_path))
    return docx_path


def test_extraction_service_pdf(sample_pdf: Path):
    data = extraction_service.extract_from_file(
        file_path=sample_pdf,
        original_filename="sample.pdf",
        resume_id="test-pdf-id-123",
        file_type="pdf",
    )

    assert data.resume_id == "test-pdf-id-123"
    assert data.file_type == "pdf"
    assert data.extraction_method == "pymupdf"
    assert data.extraction_status == ExtractionStatus.SUCCESS
    assert data.page_count == 1
    assert data.character_count > 0
    assert data.word_count > 0
    assert "Jane Developer" in data.raw_text
    assert len(data.pages) == 1
    assert data.pages[0].page_number == 1


def test_extraction_service_docx(sample_docx: Path):
    data = extraction_service.extract_from_file(
        file_path=sample_docx,
        original_filename="sample.docx",
        resume_id="test-docx-id-456",
        file_type="docx",
    )

    assert data.resume_id == "test-docx-id-456"
    assert data.file_type == "docx"
    assert data.extraction_method == "python-docx"
    assert data.extraction_status == ExtractionStatus.SUCCESS
    assert data.page_count is None
    assert data.character_count > 0
    assert data.word_count > 0
    assert "John Engineer" in data.raw_text
    assert len(data.blocks) >= 2


def test_extraction_service_unsupported_type(sample_pdf: Path):
    with pytest.raises(ValueError) as exc:
        extraction_service.extract_from_file(
            file_path=sample_pdf,
            original_filename="sample.txt",
            resume_id="id",
            file_type="txt",
        )
    assert "Unsupported file type" in str(exc.value)
