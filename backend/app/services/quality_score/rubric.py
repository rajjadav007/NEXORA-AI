"""
Quality Score Rubric Definitions and Weight Calculations
Phase 4 | Feature 21: Resume Quality Score Engine
"""

from typing import Dict, Any, NamedTuple


class RubricCategory(NamedTuple):
    key: str
    name: str
    weight: float
    max_score: float
    description: str


# Transparent 8-category scoring rubric summing to 100 points
RUBRIC_CATEGORIES: Dict[str, RubricCategory] = {
    "completeness": RubricCategory(
        key="completeness",
        name="Resume Completeness",
        weight=15.0,
        max_score=15.0,
        description="Presence and depth of all core sections: contact info, professional summary, experience, education, skills, projects, and achievements."
    ),
    "professional_summary": RubricCategory(
        key="professional_summary",
        name="Professional Summary",
        weight=10.0,
        max_score=10.0,
        description="Clarity of career identity, target role positioning, value proposition, and avoidance of generic buzzwords."
    ),
    "technical_skills": RubricCategory(
        key="technical_skills",
        name="Technical Skills",
        weight=15.0,
        max_score=15.0,
        description="Categorization, relevance, depth, modern tech stack coverage, and context-backed proficiency."
    ),
    "work_experience": RubricCategory(
        key="work_experience",
        name="Work Experience",
        weight=20.0,
        max_score=20.0,
        description="Action-oriented bullet points, measurable impact (percentages, revenue, scale), career progression, and clear responsibilities."
    ),
    "project_descriptions": RubricCategory(
        key="project_descriptions",
        name="Project Descriptions",
        weight=15.0,
        max_score=15.0,
        description="Technical complexity, problem statements, technology stack, architectural decisions, and tangible outcomes."
    ),
    "education": RubricCategory(
        key="education",
        name="Education",
        weight=10.0,
        max_score=10.0,
        description="Degree level, institution credibility, field of study, graduation timeline, and relevant honors or coursework."
    ),
    "achievements": RubricCategory(
        key="achievements",
        name="Achievements & Certifications",
        weight=5.0,
        max_score=5.0,
        description="Demonstrable external validation: verified certifications, awards, competitions, hackathons, publications, and scholarships."
    ),
    "content_clarity": RubricCategory(
        key="content_clarity",
        name="Content Clarity & Structure",
        weight=10.0,
        max_score=10.0,
        description="Conciseness, readability, bullet consistency, tone, active voice, and avoiding length padding or unnecessary filler."
    ),
}

# Verify rubric invariant: weights sum to exactly 100.0
TOTAL_RUBRIC_WEIGHT = sum(cat.weight for cat in RUBRIC_CATEGORIES.values())
assert abs(TOTAL_RUBRIC_WEIGHT - 100.0) < 1e-6, f"Rubric weights must sum to 100, got {TOTAL_RUBRIC_WEIGHT}"


def get_rating_level(score_percentage: float) -> str:
    """Classifies a score percentage (0-100) into a transparent qualitative rating."""
    if score_percentage >= 90.0:
        return "Exceptional"
    if score_percentage >= 80.0:
        return "Strong"
    if score_percentage >= 70.0:
        return "Good"
    if score_percentage >= 50.0:
        return "Needs Improvement"
    return "Critical Gaps"
