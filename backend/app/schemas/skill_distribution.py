"""
Pydantic Schemas for Resume Skill Distribution Analytics
Phase 5 | Feature 29: Skill Distribution
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SkillCategoryData(BaseModel):
    """Category-wise skill group."""
    name: str = Field(..., description="Canonical category name")
    count: int = Field(..., description="Number of unique skills in this category")
    skills: List[str] = Field(default_factory=list, description="Extracted skill names")


class MostPopulatedCategory(BaseModel):
    """Details of the category with the highest skill count."""
    name: str = Field(..., description="Category name")
    count: int = Field(..., description="Skill count")


class SkillDistributionSummary(BaseModel):
    """Aggregate summary statistics for extracted skills."""
    total_skills: int = Field(0, description="Total unique skills identified")
    total_categories: int = Field(0, description="Total skill categories populated")
    most_populated_category: Optional[MostPopulatedCategory] = Field(
        None, description="Category with the most skills"
    )
    uncategorized_skills: List[str] = Field(
        default_factory=list, description="Skills without a specific category or in Other Skills"
    )


class SkillDistributionData(BaseModel):
    """Core payload for skill distribution analytics."""
    resume_id: str = Field(..., description="Resume UUID")
    total_skills: int = Field(0, description="Total unique skills identified")
    categories: List[SkillCategoryData] = Field(
        default_factory=list, description="Populated skill categories in canonical order"
    )
    summary: SkillDistributionSummary = Field(
        default_factory=SkillDistributionSummary, description="Aggregate summary metrics"
    )


class SkillDistributionResponse(BaseModel):
    """Standard API response envelope."""
    success: bool = True
    message: str = "Resume skill distribution retrieved successfully"
    data: Optional[SkillDistributionData] = None
