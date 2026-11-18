"""
PDF Text Extraction Service
Phase 2 | Feature 3: Resume Text Extraction (Task 1, 3, 4, 5)
"""

import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any

import fitz  # PyMuPDF

from app.schemas.extraction import ExtractionStatus, PageExtraction, ContentBlock

logger = logging.getLogger(__name__)


class PDFExtractionResult:
    """Internal result container for PDF extraction."""

    def __init__(
        self,
        raw_text: str,
        pages: List[PageExtraction],
        blocks: List[ContentBlock],
        page_count: int,
        status: ExtractionStatus,
    ):
        self.raw_text = raw_text
        self.pages = pages
        self.blocks = blocks
        self.page_count = page_count
        self.status = status


class PDFExtractor:
    """
    Extracts text from PDF documents using PyMuPDF.
    Preserves page boundaries, reading order, and detects scanned/image-only PDFs.
    """

    def extract(self, file_path: Path) -> PDFExtractionResult:
        """
        Extract readable text page-by-page from a PDF file.
        Uses in-memory stream to prevent OS file locks.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        pdf_bytes = file_path.read_bytes()
        doc = None
        pages: List[PageExtraction] = []
        all_blocks: List[ContentBlock] = []
        page_texts: List[str] = []

        pages_with_text = 0
        pages_without_text = 0

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = doc.page_count

            if page_count == 0:
                return PDFExtractionResult(
                    raw_text="",
                    pages=[],
                    blocks=[],
                    page_count=0,
                    status=ExtractionStatus.EMPTY_DOCUMENT,
                )

            for page_idx in range(page_count):
                page = doc[page_idx]
                page_num = page_idx + 1

                # Extract text blocks: tuple (x0, y0, x1, y1, text, block_no, block_type)
                # block_type 0 is text, block_type 1 is image
                raw_blocks = page.get_text("blocks")
                text_blocks = [b for b in raw_blocks if len(b) >= 7 and b[6] == 0]

                # Sort by vertical position (y0), then horizontal (x0) for natural reading order
                text_blocks.sort(key=lambda b: (round(b[1], 1), round(b[0], 1)))

                page_block_strings: List[str] = []
                for b in text_blocks:
                    block_content = b[4].strip()
                    if block_content:
                        page_block_strings.append(block_content)
                        # Heuristic for headings vs paragraph: short line with no punctuation ending
                        block_type = "heading" if len(block_content) < 60 and "\n" not in block_content and not block_content.endswith(".") else "paragraph"
                        all_blocks.append(ContentBlock(type=block_type, content=block_content))

                page_text = "\n\n".join(page_block_strings).strip()

                if page_text:
                    pages_with_text += 1
                else:
                    pages_without_text += 1

                char_count = len(page_text)
                word_count = len(page_text.split())

                pages.append(
                    PageExtraction(
                        page_number=page_num,
                        text=page_text,
                        character_count=char_count,
                        word_count=word_count,
                    )
                )
                page_texts.append(page_text)

            consolidated_text = "\n\n--- Page Break ---\n\n".join(
                [pt for pt in page_texts if pt]
            ).strip()

            # Determine extraction status
            if pages_with_text == 0:
                logger.warning(
                    "PDF %s has %d pages but 0 selectable text characters (likely scanned or image-only).",
                    file_path.name,
                    page_count,
                )
                status = ExtractionStatus.NO_SELECTABLE_TEXT
            elif pages_without_text > 0 and pages_with_text > 0:
                logger.info(
                    "PDF %s has partial text extraction: %d/%d pages with text.",
                    file_path.name,
                    pages_with_text,
                    page_count,
                )
                status = ExtractionStatus.PARTIAL_EXTRACTION
            else:
                status = ExtractionStatus.SUCCESS

            return PDFExtractionResult(
                raw_text=consolidated_text,
                pages=pages,
                blocks=all_blocks,
                page_count=page_count,
                status=status,
            )

        except Exception as e:
            logger.error("Error extracting text from PDF %s: %s", file_path.name, e)
            raise
        finally:
            if doc:
                try:
                    doc.close()
                except Exception:
                    pass


pdf_extractor = PDFExtractor()
