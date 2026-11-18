"""
Unit tests for DOCXExtractor.
Phase 2 | Feature 3: Resume Text Extraction (Task 2)
"""

import pytest
from pathlib import Path
import docx

from app.services.extraction.docx_extractor import docx_extractor
from app.schemas.extraction import ExtractionStatus


@pytest.fixture
def rich_docx(tmp_path: Path) -> Path:
    docx_path = tmp_path / "rich_resume.docx"
    doc = docx.Document()
    doc.add_heading("Alex Johnson", level=0)
    doc.add_heading("Summary", level=1)
    doc.add_paragraph("Full Stack Software Engineer with 5 years experience.")

    doc.add_heading("Skills", level=1)
    doc.add_paragraph("• React, TypeScript, Node.js")
    doc.add_paragraph("• Python, FastAPI, PostgreSQL")

    doc.add_heading("Experience History", level=1)
    table = doc.add_table(rows=2, cols=3)
    table.rows[0].cells[0].text = "Company"
    table.rows[0].cells[1].text = "Role"
    table.rows[0].cells[2].text = "Years"

    table.rows[1].cells[0].text = "TechCorp"
    table.rows[1].cells[1].text = "Senior Engineer"
    table.rows[1].cells[2].text = "2022-2026"

    doc.save(str(docx_path))
    return docx_path


@pytest.fixture
def empty_docx(tmp_path: Path) -> Path:
    docx_path = tmp_path / "empty_document.docx"
    doc = docx.Document()
    doc.save(str(docx_path))
    return docx_path


def test_extract_rich_docx(rich_docx: Path):
    result = docx_extractor.extract(rich_docx)

    assert result.status == ExtractionStatus.SUCCESS
    assert "Alex Johnson" in result.raw_text
    assert "Full Stack Software Engineer" in result.raw_text
    assert "TechCorp | Senior Engineer | 2022-2026" in result.raw_text

    # Verify structural block typing
    block_types = [b.type for b in result.blocks]
    assert "heading" in block_types
    assert "paragraph" in block_types
    assert "list_item" in block_types
    assert "table" in block_types


def test_extract_empty_docx(empty_docx: Path):
    result = docx_extractor.extract(empty_docx)

    assert result.status == ExtractionStatus.EMPTY_DOCUMENT
    assert result.raw_text == ""
    assert result.blocks == []


def test_extract_non_existent_docx(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        docx_extractor.extract(tmp_path / "missing.docx")
