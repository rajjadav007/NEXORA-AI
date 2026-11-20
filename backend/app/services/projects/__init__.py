"""
Project Intelligence Service Package
Phase 3 | Feature 18: Project Intelligence
"""

from app.services.projects.service import (
    ProjectIntelligenceService,
    project_intelligence_service,
)
from app.services.projects.normalizer import (
    normalize_project_title,
    classify_project_category,
    extract_and_categorize_urls,
)
from app.services.projects.skill_linker import (
    link_technologies_to_canonical_skills,
)
from app.services.projects.section_detector import (
    extract_project_sections,
    split_section_into_project_blocks,
)
from app.services.projects.deterministic_extractor import (
    extract_deterministic_project,
)
from app.services.projects.deduplicator import (
    deduplicate_projects,
)
from app.services.projects.confidence_scorer import (
    compute_project_confidence,
)

__all__ = [
    "ProjectIntelligenceService",
    "project_intelligence_service",
    "normalize_project_title",
    "classify_project_category",
    "extract_and_categorize_urls",
    "link_technologies_to_canonical_skills",
    "extract_project_sections",
    "split_section_into_project_blocks",
    "extract_deterministic_project",
    "deduplicate_projects",
    "compute_project_confidence",
]
