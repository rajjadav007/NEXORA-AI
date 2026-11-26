"""
Job Description URL Import Services
Phase 6 | Feature 34: Job Description URL Import
"""

from app.services.job_import.fetcher import (
    JobImportBlockedError,
    JobImportError,
    JobImportFetchError,
    JobImportSizeError,
    SSRFBlockedError,
    UnsupportedDomainError,
    URLValidationError,
    fetch_job_page,
    normalize_and_validate_url,
)
from app.services.job_import.extractor import (
    JobImportExtractionError,
    extract_job_description_from_html,
)

__all__ = [
    "JobImportError",
    "URLValidationError",
    "UnsupportedDomainError",
    "SSRFBlockedError",
    "JobImportBlockedError",
    "JobImportSizeError",
    "JobImportFetchError",
    "JobImportExtractionError",
    "normalize_and_validate_url",
    "fetch_job_page",
    "extract_job_description_from_html",
]
