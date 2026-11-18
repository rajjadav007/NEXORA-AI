"""
Document Integrity Validation Service
Phase 2 | Feature 2: File Validation (Task 5)
"""

import io
import logging
import zipfile
from pathlib import Path
from typing import Dict, Any

import fitz  # PyMuPDF
import docx  # python-docx

from app.services.validation.exceptions import (
    CorruptedFileError,
    PasswordProtectedFileError,
    InvalidDocumentStructureError,
)

logger = logging.getLogger(__name__)

# Security boundaries for ZIP inspection
MAX_UNCOMPRESSED_DOCX_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_DECOMPRESSION_RATIO = 100  # ZIP bomb defense

# Required entries inside a genuine Office Open XML DOCX package
REQUIRED_DOCX_ENTRIES = {
    "[Content_Types].xml",
    "word/document.xml",
}


class IntegrityValidator:
    """Validates deep structure, integrity, and encryption status of PDF and DOCX files."""

    def validate_pdf_integrity(self, file_path: Path) -> Dict[str, Any]:
        """
        Inspect PDF document structure using PyMuPDF.
        Detects encryption, corrupted cross-reference tables, truncated bodies, and unreadable pages.
        Uses in-memory stream to prevent file lock contention on Windows.
        DOES NOT extract text.
        """
        doc = None
        try:
            pdf_bytes = file_path.read_bytes()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            if not doc.is_pdf:
                raise CorruptedFileError("File could not be parsed as a valid PDF document.")

            # Check password protection / encryption
            if doc.is_encrypted or doc.needs_pass:
                raise PasswordProtectedFileError(
                    "The uploaded PDF is password-protected. Please remove the password protection and re-upload."
                )

            # Check page tree validity
            page_count = doc.page_count
            if page_count < 1:
                raise CorruptedFileError("PDF document contains no readable pages.")

            # Probe first and last page to verify xref integrity
            _ = doc[0].rect
            if page_count > 1:
                _ = doc[page_count - 1].rect

            return {
                "page_count": page_count,
                "is_encrypted": False,
                "format": "PDF",
            }

        except PasswordProtectedFileError:
            raise
        except (fitz.FileDataError, fitz.EmptyFileError) as e:
            logger.warning("PyMuPDF rejected damaged PDF: %s", e)
            raise CorruptedFileError(
                "PDF file is damaged or corrupted. Please re-export your resume as a fresh PDF."
            ) from e
        except Exception as e:
            logger.error("Unexpected error parsing PDF %s: %s", file_path.name, e)
            raise CorruptedFileError(f"PDF validation failed: {str(e)}") from e
        finally:
            if doc:
                try:
                    doc.close()
                except Exception:
                    pass

    def validate_docx_integrity(self, file_path: Path) -> Dict[str, Any]:
        """
        Inspect DOCX package structure and XML schema integrity.
        Verifies required OpenXML package entries, protects against ZIP bombs,
        and ensures standard document XML parses properly.
        Uses in-memory buffer to prevent file lock contention on Windows.
        DOES NOT extract text.
        """
        docx_bytes = file_path.read_bytes()
        zip_buf = io.BytesIO(docx_bytes)

        if not zipfile.is_zipfile(zip_buf):
            raise CorruptedFileError(
                "File is corrupted or not a valid ZIP-based Office Open XML archive."
            )

        try:
            with zipfile.ZipFile(zip_buf, "r") as zf:
                # 1. Test ZIP archive integrity (CRC32 checks)
                corrupted_member = zf.testzip()
                if corrupted_member:
                    raise CorruptedFileError(
                        f"DOCX archive contains a corrupted component: {corrupted_member}"
                    )

                namelist = set(zf.namelist())

                # 2. Verify required Office Open XML entries (reject ordinary zips)
                missing_entries = REQUIRED_DOCX_ENTRIES - namelist
                if missing_entries:
                    raise InvalidDocumentStructureError(
                        "The file is a standard ZIP archive, not a valid Microsoft Word (.docx) document. "
                        f"Missing required document parts: {', '.join(sorted(missing_entries))}.",
                        details={"missing_entries": list(missing_entries)},
                    )

                # 3. Guard against ZIP bomb attacks
                total_uncompressed = 0
                total_compressed = 0
                for info in zf.infolist():
                    total_uncompressed += info.file_size
                    total_compressed += info.compress_size

                    if total_uncompressed > MAX_UNCOMPRESSED_DOCX_BYTES:
                        raise CorruptedFileError(
                            "DOCX document exceeds safe uncompressed size limit (ZIP bomb protection)."
                        )

                if total_compressed > 0 and (total_uncompressed / total_compressed) > MAX_DECOMPRESSION_RATIO:
                    raise CorruptedFileError(
                        "DOCX document has an unsafe compression ratio (ZIP bomb protection)."
                    )

            # 4. Validate WordprocessingML XML structure using python-docx
            try:
                doc = docx.Document(io.BytesIO(docx_bytes))
                # Verify document has body
                _ = len(doc.paragraphs)
            except Exception as xml_err:
                logger.warning("python-docx rejected invalid document XML: %s", xml_err)
                raise CorruptedFileError(
                    "Word document package is malformed or contains invalid XML structure."
                ) from xml_err

            return {
                "format": "DOCX",
                "is_encrypted": False,
                "uncompressed_bytes": total_uncompressed,
            }

        except (CorruptedFileError, InvalidDocumentStructureError):
            raise
        except zipfile.BadZipFile as e:
            logger.warning("BadZipFile error for DOCX %s: %s", file_path.name, e)
            raise CorruptedFileError("DOCX archive is corrupted and cannot be read.") from e
        except Exception as e:
            logger.error("Unexpected error validating DOCX %s: %s", file_path.name, e)
            raise CorruptedFileError(f"Word document validation failed: {str(e)}") from e


integrity_validator = IntegrityValidator()
