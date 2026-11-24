"""
Resume Skill Distribution Analytics Service
Phase 5 | Feature 29: Skill Distribution
Aggregates, categorizes, and organizes candidate skills into 8 canonical categories.
"""

import uuid
import logging
from typing import Optional, List, Dict, Set, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.resume import Resume
from app.models.skills import ResumeSkill
from app.services.skills.service import skill_normalization_service

logger = logging.getLogger(__name__)

# The 8 canonical categories for Feature #29
CANONICAL_CATEGORIES = [
    "Programming Languages",
    "AI and Machine Learning",
    "Data Science and Analytics",
    "Frameworks and Libraries",
    "Databases",
    "Cloud and DevOps",
    "Development Tools",
    "Other Skills",
]

# Specific technology name overrides for Data Science and Analytics
DATA_SCIENCE_SKILLS = {
    "pandas",
    "numpy",
    "scipy",
    "matplotlib",
    "seaborn",
    "tableau",
    "power bi",
    "powerbi",
    "apache spark",
    "pyspark",
    "spark",
    "hadoop",
    "bigquery",
    "snowflake",
    "data analysis",
    "data analytics",
    "data engineering",
    "statistics",
    "statistical modeling",
    "statistical analysis",
    "etl",
    "data warehousing",
    "looker",
    "business intelligence",
    "data visualization",
    "excel",
    "alteryx",
    "databricks",
    "sas",
    "spss",
    "dax",
    "plotly",
}

# Specific technology name overrides for AI and Machine Learning
AI_ML_SKILLS = {
    "machine learning",
    "deep learning",
    "natural language processing",
    "nlp",
    "computer vision",
    "large language models",
    "llm",
    "llms",
    "generative ai",
    "genai",
    "reinforcement learning",
    "neural networks",
    "pytorch",
    "tensorflow",
    "keras",
    "scikit-learn",
    "sklearn",
    "langchain",
    "langgraph",
    "hugging face",
    "huggingface",
    "transformers",
    "ollama",
    "rag",
    "stable diffusion",
    "bert",
    "gpt",
    "opencv",
    "xgboost",
    "lightgbm",
}


def classify_skill_category(skill_name: str, existing_category: Optional[str] = None) -> str:
    """
    Deterministically maps a skill and its optional stored category
    into one of the 8 canonical categories.
    """
    clean_name = (skill_name or "").strip().lower()
    clean_cat = (existing_category or "").strip().lower()

    # 1. Check specific high-priority name sets
    if clean_name in DATA_SCIENCE_SKILLS:
        return "Data Science and Analytics"
    if clean_name in AI_ML_SKILLS:
        return "AI and Machine Learning"

    # 2. Check existing stored category
    if clean_cat in ("programming languages", "programming language", "languages"):
        return "Programming Languages"
    if clean_cat in ("machine learning & ai", "ai and machine learning", "ai & machine learning", "machine learning", "artificial intelligence"):
        return "AI and Machine Learning"
    if clean_cat in ("data science and analytics", "data science", "analytics"):
        return "Data Science and Analytics"
    if clean_cat in ("frameworks & libraries", "frameworks and libraries", "frameworks", "libraries"):
        return "Frameworks and Libraries"
    if clean_cat in ("databases", "database"):
        return "Databases"
    if clean_cat in ("cloud & devops", "cloud and devops", "cloud", "devops"):
        return "Cloud and DevOps"
    if clean_cat in ("tools", "development tools", "developer tools"):
        return "Development Tools"
    if clean_cat in ("soft skills", "soft", "other", "other skills"):
        return "Other Skills"

    # 3. Fallback to Other Skills
    return "Other Skills"


class SkillDistributionService:
    """
    Extracts and organizes candidate skills into 8 canonical categories
    with duplicate prevention and aggregate summaries.
    """

    async def get_resume_skill_distribution(
        self,
        resume_id: str,
        db: Session,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves extracted skills for a resume, groups them into 8 categories,
        ensures no duplicate skills across/within categories, and returns structured data.
        """
        try:
            resume_uuid = uuid.UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume ID format: {resume_id}",
            )

        # 1. Verify Resume exists
        resume = db.execute(
            select(Resume).where(Resume.id == resume_uuid)
        ).scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found.",
            )

        # 2. Fetch existing ResumeSkill records
        stmt = (
            select(ResumeSkill)
            .where(ResumeSkill.resume_id == resume_uuid)
            .order_by(ResumeSkill.canonical_name)
        )
        skill_records = list(db.execute(stmt).scalars().all())

        # 3. If no skills found in DB, attempt extraction if resume has content
        if not skill_records:
            try:
                extracted = await skill_normalization_service.extract_and_normalize_skills(
                    resume_id=resume_id,
                    reprocess=False,
                    force_overwrite=False,
                    db=db,
                )
                if extracted:
                    skill_records = list(db.execute(stmt).scalars().all())
            except Exception as exc:
                logger.warning("Could not auto-extract skills for resume %s: %s", resume_id, exc)

        # 4. Group and deduplicate skills
        # Map: category_name -> list of display skill names
        grouped_skills: Dict[str, List[str]] = {cat: [] for cat in CANONICAL_CATEGORIES}
        seen_keys: Set[str] = set()

        for record in skill_records:
            display_name = (record.canonical_name or record.original_name or "").strip()
            if not display_name:
                continue

            dedup_key = display_name.lower()
            if dedup_key in seen_keys:
                continue  # Avoid duplicate skills across and within categories

            seen_keys.add(dedup_key)
            target_category = classify_skill_category(display_name, record.category)
            grouped_skills[target_category].append(display_name)

        # 5. Format category items (preserve order of CANONICAL_CATEGORIES, omit empty categories)
        categories_output = []
        for cat in CANONICAL_CATEGORIES:
            skills_in_cat = grouped_skills[cat]
            if skills_in_cat:
                categories_output.append({
                    "name": cat,
                    "count": len(skills_in_cat),
                    "skills": sorted(skills_in_cat, key=lambda s: s.lower()),
                })

        total_unique_skills = len(seen_keys)
        total_populated_categories = len(categories_output)

        # 6. Calculate most populated category
        most_populated = None
        if categories_output:
            top_cat = max(categories_output, key=lambda c: c["count"])
            most_populated = {
                "name": top_cat["name"],
                "count": top_cat["count"],
            }

        # 7. Identify uncategorized skills (those in "Other Skills")
        uncategorized_skills = sorted(grouped_skills["Other Skills"], key=lambda s: s.lower())

        summary = {
            "total_skills": total_unique_skills,
            "total_categories": total_populated_categories,
            "most_populated_category": most_populated,
            "uncategorized_skills": uncategorized_skills,
        }

        return {
            "resume_id": str(resume.id),
            "total_skills": total_unique_skills,
            "categories": categories_output,
            "summary": summary,
        }


skill_distribution_service = SkillDistributionService()
