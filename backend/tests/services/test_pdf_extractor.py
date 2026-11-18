"""
Unit tests for PDFExtractor.
Phase 2 | Feature 3: Resume Text Extraction (Task 1)
"""

import pytest
from pathlib import Path
import fitz

from app.services.extraction.pdf_extractor import pdf_extractor
from app.schemas.extraction import ExtractionStatus


@pytest.fixture
def single_page_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "single_page.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Jane Doe\nSenior Backend Engineer\nSan Francisco, CA")
    page.insert_text((50, 120), "SKILLS\n• Python, FastAPI, Docker, PostgreSQL")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def multi_page_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "multi_page.pdf"
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((50, 50), "John Doe - Page 1 - Experience and Background")
    p2 = doc.new_page()
    p2.insert_text((50, 50), "John Doe - Page 2 - Education and Certifications")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def scanned_pdf(tmp_path: Path) -> Path:
    # A PDF page that contains only a drawn shape / image rectangle, no text
    pdf_path = tmp_path / "scanned_image_only.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(50, 50, 200, 200), color=(0, 0, 0), fill=(0.8, 0.8, 0.8))
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_extract_single_page_pdf(single_page_pdf: Path):
    result = pdf_extractor.extract(single_page_pdf)

    assert result.status == ExtractionStatus.SUCCESS
    assert result.page_count == 1
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert "Jane Doe" in result.raw_text
    assert "FastAPI" in result.raw_text
    assert len(result.blocks) >= 2


def test_extract_multi_page_pdf(multi_page_pdf: Path):
    result = pdf_extractor.extract(multi_page_pdf)

    assert result.status == ExtractionStatus.SUCCESS
    assert result.page_count == 2
    assert len(result.pages) == 2
    assert "Page 1" in result.pages[0].text
    assert "Page 2" in result.pages[1].text
    assert "--- Page Break ---" in result.raw_text


def test_extract_scanned_pdf_detects_no_selectable_text(scanned_pdf: Path):
    result = pdf_extractor.extract(scanned_pdf)

    assert result.status == ExtractionStatus.NO_SELECTABLE_TEXT
    assert result.page_count == 1
    assert result.raw_text == ""
    assert result.pages[0].character_count == 0


def test_extract_non_existent_file(tmp_path: Path):
    missing_file = tmp_path / "does_not_exist.pdf"
    with pytest.raises(FileNotFoundError):
        pdf_extractor.extract(missing_file)
