"""
Resume Storage API Schemas
Phase 2 | Feature 6: Resume Storage
"""

import uuid
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SaveResumeRequest(BaseModel):
    """Optional user identification payload when saving a staged resume."""
    user_id: Optional[str] = None
    user_email: Optional[str] = None


class ResumeVersionData(BaseModel):
    """Details for a stored resume version."""
    id: str
    resume_id: str
    version_number: int
    storage_key: str
    extracted_text: Optional[str] = None
    cleaned_text: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class StoredResumeData(BaseModel):
    """Consolidated stored resume record."""
    id: str
    user_id: Optional[str] = None
    original_filename: str
    storage_key: str
    file_type: str
    file_size: int
    processing_status: str
    current_version: int
    created_at: str
    updated_at: str
    versions: List[ResumeVersionData] = []

    model_config = ConfigDict(from_attributes=True)


class SaveResumeResponse(BaseModel):
    """Standardized API response for saving a resume."""
    success: bool = True
    message: str = "Resume saved successfully"
    data: StoredResumeData


class StoredResumeDetailResponse(BaseModel):
    """Standardized API response for retrieving a single stored resume."""
    success: bool = True
    message: str = "Resume retrieved successfully"
    data: StoredResumeData


class ResumeListResponse(BaseModel):
    """Standardized API response for listing stored resumes."""
    success: bool = True
    message: str = "Resumes retrieved successfully"
    data: List[StoredResumeData]
    total: int
