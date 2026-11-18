"""
Unit tests for ResumeStagingService.
Phase 2 | Feature 1: Resume Upload
"""

import io
import pytest
from pathlib import Path
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.services.storage import (
    ResumeStagingService,
    sanitize_filename,
    StorageError,
    FileTooLargeError,
    EmptyFileError,
    InvalidFileTypeError,
)


@pytest.fixture
def temp_staging_dir(tmp_path: Path) -> Path:
    staging = tmp_path / "test_staging"
    return staging


@pytest.fixture
def staging_service(temp_staging_dir: Path) -> ResumeStagingService:
    # 1 MB max size for test speed
    return ResumeStagingService(staging_dir=temp_staging_dir, max_size_bytes=1024 * 1024)


def test_sanitize_filename_traversal():
    assert ".." not in sanitize_filename("../../../etc/passwd.pdf")
    assert sanitize_filename("..\\..\\windows\\system32\\calc.docx").endswith(".docx")
    assert "/" not in sanitize_filename("folder/sub/resume.pdf")
    assert "\\" not in sanitize_filename("C:\\Users\\Attacker\\resume.pdf")


def test_sanitize_filename_clean():
    clean = sanitize_filename("My Resume (2026) #v1.pdf")
    assert clean.endswith(".pdf")
    assert " " not in clean
    assert "#" not in clean


@pytest.mark.asyncio
async def test_stage_valid_pdf(staging_service: ResumeStagingService):
    content = b"%PDF-1.4 sample content for test"
    file = UploadFile(
        filename="developer_resume.pdf",
        file=io.BytesIO(content),
        headers=Headers({"content-type": "application/pdf"}),
    )

    metadata = await staging_service.stage_upload(file)

    assert metadata.upload_id is not None
    assert len(metadata.upload_id) == 36  # UUID length
    assert metadata.original_filename == "developer_resume.pdf"
    assert metadata.file_size == len(content)
    assert metadata.content_type == "application/pdf"
    assert metadata.status == "staged"

    # Verify physical file exists in private staging dir
    staged_path = staging_service.get_staged_path(metadata.upload_id)
    assert staged_path is not None
    assert staged_path.exists()
    assert staged_path.read_bytes() == content

    # Clean up
    assert staging_service.cleanup_file(metadata.upload_id) is True
    assert not staged_path.exists()


@pytest.mark.asyncio
async def test_stage_valid_docx(staging_service: ResumeStagingService):
    content = b"PK\x03\x04 mock docx binary bytes"
    file = UploadFile(
        filename="candidate.docx",
        file=io.BytesIO(content),
        headers=Headers({"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
    )

    metadata = await staging_service.stage_upload(file)
    assert metadata.upload_id is not None
    assert metadata.original_filename == "candidate.docx"
    assert metadata.file_size == len(content)

    # Clean up
    staging_service.cleanup_file(metadata.upload_id)


@pytest.mark.asyncio
async def test_reject_unsupported_file_extension(staging_service: ResumeStagingService):
    file = UploadFile(
        filename="malicious.exe",
        file=io.BytesIO(b"MZ executable"),
        headers=Headers({"content-type": "application/octet-stream"}),
    )

    with pytest.raises(InvalidFileTypeError) as exc:
        await staging_service.stage_upload(file)
    assert "Unsupported file format" in str(exc.value)


@pytest.mark.asyncio
async def test_reject_empty_file_and_cleanup(staging_service: ResumeStagingService, temp_staging_dir: Path):
    file = UploadFile(
        filename="empty.pdf",
        file=io.BytesIO(b""),
        headers=Headers({"content-type": "application/pdf"}),
    )

    with pytest.raises(EmptyFileError):
        await staging_service.stage_upload(file)

    # Confirm staging dir has no leftover files
    assert list(temp_staging_dir.glob("*")) == []


@pytest.mark.asyncio
async def test_reject_oversized_file_and_cleanup(staging_service: ResumeStagingService, temp_staging_dir: Path):
    # max is 1 MB (1024 * 1024 bytes)
    oversized = b"A" * (1024 * 1024 + 100)
    file = UploadFile(
        filename="huge.pdf",
        file=io.BytesIO(oversized),
        headers=Headers({"content-type": "application/pdf"}),
    )

    with pytest.raises(FileTooLargeError):
        await staging_service.stage_upload(file)

    # Ensure incomplete file was unlinked
    assert list(temp_staging_dir.glob("*")) == []
