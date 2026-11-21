"""
Category definitions and normalization helpers for Resume Improvement Recommendations.
Phase 4 | Feature 27: Resume Improvement Recommendations
"""

from typing import Dict, Any, List

RECOMMENDATION_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "technical_skills": {
        "key": "technical_skills",
        "name": "Technical Skills Presentation",
        "description": "Organization, categorisation, proficiencies, and relevance of technical and soft skills.",
        "icon": "Code",
    },
    "professional_summary": {
        "key": "professional_summary",
        "name": "Professional Summary",
        "description": "Crafting a compelling executive hook, target role alignment, and core value proposition.",
        "icon": "FileText",
    },
    "project_descriptions": {
        "key": "project_descriptions",
        "name": "Project Descriptions",
        "description": "Architecture details, technologies used, live deployment links, and project impact.",
        "icon": "Layers",
    },
    "work_experience": {
        "key": "work_experience",
        "name": "Work & Internship Experience",
        "description": "Action-oriented bullet points, progression, responsibilities, and clear role scope.",
        "icon": "Briefcase",
    },
    "achievements_impact": {
        "key": "achievements_impact",
        "name": "Achievements & Measurable Impact",
        "description": "Quantification of accomplishments, metric percentages, Google X-Y-Z formula, and business scale.",
        "icon": "Trophy",
    },
    "ats_compatibility": {
        "key": "ats_compatibility",
        "name": "ATS Compatibility",
        "description": "Standard headings, single-column parsing, keyword distribution, and layout hygiene.",
        "icon": "ShieldCheck",
    },
    "grammar_clarity": {
        "key": "grammar_clarity",
        "name": "Grammar & Clarity",
        "description": "Writing mechanics, active voice, sentence conciseness, spelling, and professional tone.",
        "icon": "Sparkles",
    },
    "resume_completeness": {
        "key": "resume_completeness",
        "name": "Resume Completeness",
        "description": "Essential sections, contact info integrity, education details, dates, and consistency.",
        "icon": "CheckSquare",
    },
}

# Normalization mapping for variations and aliases
CATEGORY_ALIASES: Dict[str, str] = {
    "technical_skills": "technical_skills",
    "technical skills": "technical_skills",
    "skills": "technical_skills",
    "skill": "technical_skills",
    "tech_skills": "technical_skills",
    "skills_presentation": "technical_skills",
    
    "professional_summary": "professional_summary",
    "professional summary": "professional_summary",
    "summary": "professional_summary",
    "executive_summary": "professional_summary",
    "profile": "professional_summary",
    
    "project_descriptions": "project_descriptions",
    "project descriptions": "project_descriptions",
    "projects": "project_descriptions",
    "project": "project_descriptions",
    
    "work_experience": "work_experience",
    "work experience": "work_experience",
    "experience": "work_experience",
    "work": "work_experience",
    "internship": "work_experience",
    "internships": "work_experience",
    "employment": "work_experience",
    
    "achievements_impact": "achievements_impact",
    "achievements & measurable impact": "achievements_impact",
    "achievements": "achievements_impact",
    "impact": "achievements_impact",
    "accomplishments": "achievements_impact",
    "measurable_impact": "achievements_impact",
    
    "ats_compatibility": "ats_compatibility",
    "ats compatibility": "ats_compatibility",
    "ats": "ats_compatibility",
    "ats_optimization": "ats_compatibility",
    "parsing": "ats_compatibility",
    
    "grammar_clarity": "grammar_clarity",
    "grammar & clarity": "grammar_clarity",
    "grammar": "grammar_clarity",
    "clarity": "grammar_clarity",
    "spelling": "grammar_clarity",
    "tone": "grammar_clarity",
    "style": "grammar_clarity",
    
    "resume_completeness": "resume_completeness",
    "resume completeness": "resume_completeness",
    "completeness": "resume_completeness",
    "missing_sections": "resume_completeness",
    "structure": "resume_completeness",
    "personal_info": "resume_completeness",
    "education": "resume_completeness",
}


def normalize_category_key(raw_category: str) -> str:
    """Normalizes an arbitrary category string to one of the 8 standard category keys."""
    if not raw_category:
        return "resume_completeness"
    normalized = raw_category.strip().lower()
    return CATEGORY_ALIASES.get(normalized, "resume_completeness")


def get_category_display_name(category_key: str) -> str:
    """Returns human-friendly display name for category key."""
    norm_key = normalize_category_key(category_key)
    meta = RECOMMENDATION_CATEGORIES.get(norm_key)
    if meta:
        return meta["name"]
    return norm_key.replace("_", " ").title()
