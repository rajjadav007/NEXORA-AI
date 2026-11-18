"""
DOCX Text Extraction Service
Phase 2 | Feature 3: Resume Text Extraction (Task 2, 3, 4, 5)
"""

import io
import logging
from pathlib import Path
from typing import List, Dict, Any

import docx
from docx.text.paragraph import Paragraph
from docx.table import Table

from app.schemas.extraction import ExtractionStatus, ContentBlock

logger = logging.getLogger(__name__)

BULLET_PREFIXES = ("•", "-", "*", "–", "—", "▪", "▫", "►")


class DOCXExtractionResult:
    """Internal result container for DOCX extraction."""

    def __init__(
        self,
        raw_text: str,
        blocks: List[ContentBlock],
        status: ExtractionStatus,
    ):
        self.raw_text = raw_text
        self.blocks = blocks
        self.status = status


class DOCXExtractor:
    """
    Extracts text from DOCX documents using python-docx.
    Traverses paragraphs, headings, bullet lists, and tables in natural document order.
    """

    def extract(self, file_path: Path) -> DOCXExtractionResult:
        """
        Extract readable text and structural content blocks from a DOCX file.
        Uses in-memory stream to prevent OS file locks.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"DOCX file not found: {file_path}")

        docx_bytes = file_path.read_bytes()
        buf = io.BytesIO(docx_bytes)

        try:
            doc = docx.Document(buf)
            blocks: List[ContentBlock] = []
            text_sections: List[str] = []

            # Traverse paragraphs and tables in natural interleaved document order
            if hasattr(doc, "iter_inner_content"):
                items = doc.iter_inner_content()
            else:
                items = doc.paragraphs

            for item in items:
                if isinstance(item, Paragraph):
                    text = item.text.strip()
                    if not text:
                        continue

                    style_name = (item.style.name or "").lower() if item.style else ""

                    # Detect headings
                    if "heading" in style_name or "title" in style_name:
                        block_type = "heading"
                    # Detect list items / bullet points
                    elif "list" in style_name or "bullet" in style_name or text.startswith(BULLET_PREFIXES):
                        block_type = "list_item"
                    else:
                        block_type = "paragraph"

                    blocks.append(ContentBlock(type=block_type, content=text))
                    text_sections.append(text)

                elif isinstance(item, Table):
                    table_rows: List[str] = []
                    for row in item.rows:
                        # Extract cell texts and clean up
                        cell_texts = [cell.text.strip() for cell in row.cells]
                        # Remove consecutive identical cell contents (common with merged cells)
                        deduped_cells: List[str] = []
                        for ct in cell_texts:
                            if not deduped_cells or ct != deduped_cells[-1]:
                                deduped_cells.append(ct)

                        row_str = " | ".join(c for c in deduped_cells if c)
                        if row_str:
                            table_rows.append(row_str)

                    if table_rows:
                        table_content = "\n".join(table_rows)
                        blocks.append(ContentBlock(type="table", content=table_content))
                        text_sections.append(table_content)

            raw_text = "\n\n".join(text_sections).strip()

            if not raw_text:
                status = ExtractionStatus.EMPTY_DOCUMENT
            else:
                status = ExtractionStatus.SUCCESS

            return DOCXExtractionResult(
                raw_text=raw_text,
                blocks=blocks,
                status=status,
            )

        except Exception as e:
            logger.error("Error extracting text from DOCX %s: %s", file_path.name, e)
            raise


docx_extractor = DOCXExtractor()
