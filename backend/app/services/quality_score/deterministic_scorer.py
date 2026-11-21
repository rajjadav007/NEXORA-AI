"""
Deterministic Scorer for Resume Quality
Phase 4 | Feature 21: Resume Quality Score Engine
Computes objective baseline metrics directly from Phase 3 structured sections.
Evaluates evidence, completeness, metrics, and structural presence without subjective guessing.
"""

import re
from typing import Dict, Any, List, Optional
from app.services.quality_score.rubric import RUBRIC_CATEGORIES

# Metric regex pattern: matches numbers with %, $, x, X, k, K, M, B, or metric improvement verbs
METRIC_PATTERN = re.compile(
    r'(\b\d+(\.\d+)?%|\$\d+[\d,]*|\b\d+x\b|\b\d+\+?\s*(users|clients|customers|requests|req/s|rps|ms|seconds|minutes|hours|days|percent|increase|decrease|growth|reduced|improved|boosted)\b)',
    re.IGNORECASE
)

ACTION_VERB_PATTERN = re.compile(
    r'\b(developed|engineered|built|architected|designed|implemented|spearheaded|optimized|streamlined|automated|reduced|increased|led|managed|launched|delivered|scaled|refactored|mentored|created)\b',
    re.IGNORECASE
)


def evaluate_deterministic_baseline(
    personal_info: Optional[Any],
    education_records: List[Any],
    experience_records: List[Any],
    resume_skills: List[Any],
    projects: List[Any],
    certifications: List[Any],
    achievements: List[Any],
    cleaned_text: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Computes deterministic structural ratios (0.0 to 1.0) and observations
    for each of the 8 categories based on structured data evidence.
    """
    results: Dict[str, Dict[str, Any]] = {}
    text = cleaned_text or ""
    word_count = len(text.split()) if text else 0

    # 1. Completeness (15 pts)
    # Check for presence of essential sections: contact, summary, skills, experience, education, projects, achievements
    sections_present = 0
    missing_sections = []
    
    # Contact info check
    if personal_info and (getattr(personal_info, "full_name", None) or getattr(personal_info, "name", None)):
        sections_present += 1
    else:
        missing_sections.append("Full Name")
        
    if personal_info and (getattr(personal_info, "email", None) or getattr(personal_info, "phone", None)):
        sections_present += 1
    else:
        missing_sections.append("Contact Information (Email / Phone)")

    # Summary check
    has_summary = bool(personal_info and getattr(personal_info, "summary", None) and len(str(personal_info.summary).strip()) > 20)
    if has_summary:
        sections_present += 1
    else:
        missing_sections.append("Professional Summary")

    # Skills check
    if resume_skills and len(resume_skills) >= 3:
        sections_present += 1
    else:
        missing_sections.append("Skills Section")

    # Experience check
    if experience_records and len(experience_records) >= 1:
        sections_present += 1
    else:
        missing_sections.append("Work Experience Section")

    # Education check
    if education_records and len(education_records) >= 1:
        sections_present += 1
    else:
        missing_sections.append("Education Section")

    # Projects check
    if projects and len(projects) >= 1:
        sections_present += 1
    else:
        missing_sections.append("Projects Section")

    completeness_ratio = min(1.0, sections_present / 7.0)
    results["completeness"] = {
        "ratio": completeness_ratio,
        "sections_present": sections_present,
        "missing_sections": missing_sections,
    }

    # 2. Professional Summary (10 pts)
    summary_text = str(getattr(personal_info, "summary", "")) if (personal_info and getattr(personal_info, "summary", None)) else ""
    summary_words = len(summary_text.split())
    if summary_words == 0:
        summary_ratio = 0.0
        summary_obs = "No professional summary found."
    elif summary_words < 15:
        summary_ratio = 0.4
        summary_obs = "Professional summary is too brief to convey value proposition."
    elif 15 <= summary_words <= 90:
        summary_ratio = 0.95
        summary_obs = "Concise and well-dimensioned professional summary."
    elif summary_words > 150:
        summary_ratio = 0.65
        summary_obs = "Professional summary is overly verbose and takes focus from experience."
    else:
        summary_ratio = 0.8
        summary_obs = "Adequate professional summary."

    results["professional_summary"] = {
        "ratio": summary_ratio,
        "word_count": summary_words,
        "observation": summary_obs,
    }

    # 3. Technical Skills (15 pts)
    skill_count = len(resume_skills)
    categories = set()
    for s in resume_skills:
        cat = getattr(s, "category", None) or "Other"
        categories.add(cat)

    if skill_count == 0:
        skills_ratio = 0.0
    elif skill_count < 5:
        skills_ratio = 0.4
    elif skill_count < 10:
        skills_ratio = 0.75
    elif skill_count <= 35:
        # Balanced skills coverage
        category_bonus = min(0.2, len(categories) * 0.05)
        skills_ratio = min(1.0, 0.8 + category_bonus)
    else:
        # Overstuffed / buzzword heavy resume
        skills_ratio = 0.7

    results["technical_skills"] = {
        "ratio": skills_ratio,
        "count": skill_count,
        "categories_count": len(categories),
    }

    # 4. Work Experience (20 pts)
    exp_count = len(experience_records)
    metric_count = 0
    action_verb_count = 0
    total_exp_bullets = 0

    for exp in experience_records:
        desc = getattr(exp, "description", "") or ""
        bullets = getattr(exp, "key_responsibilities", []) or []
        combined_exp_text = desc + " " + " ".join(bullets if isinstance(bullets, list) else [str(bullets)])
        metric_matches = METRIC_PATTERN.findall(combined_exp_text)
        action_matches = ACTION_VERB_PATTERN.findall(combined_exp_text)
        metric_count += len(metric_matches)
        action_verb_count += len(action_matches)
        total_exp_bullets += len(bullets) if isinstance(bullets, list) else 1

    if exp_count == 0:
        exp_ratio = 0.1  # Minimal if no formal experience listed (e.g. student)
    else:
        base_exp = min(0.5, exp_count * 0.25)
        metric_factor = min(0.3, metric_count * 0.08)
        action_factor = min(0.2, action_verb_count * 0.04)
        exp_ratio = min(1.0, base_exp + metric_factor + action_factor)

    results["work_experience"] = {
        "ratio": exp_ratio,
        "count": exp_count,
        "quantified_metrics_count": metric_count,
        "action_verbs_count": action_verb_count,
    }

    # 5. Project Descriptions (15 pts)
    proj_count = len(projects)
    proj_with_tech = 0
    proj_with_outcomes = 0

    for p in projects:
        skills_linked = getattr(p, "skills_used", []) or getattr(p, "technologies", []) or []
        if skills_linked and len(skills_linked) > 0:
            proj_with_tech += 1
        desc = getattr(p, "description", "") or ""
        if len(desc) > 30:
            proj_with_outcomes += 1

    if proj_count == 0:
        proj_ratio = 0.1
    else:
        base_proj = min(0.5, proj_count * 0.25)
        tech_factor = min(0.3, (proj_with_tech / max(1, proj_count)) * 0.3)
        desc_factor = min(0.2, (proj_with_outcomes / max(1, proj_count)) * 0.2)
        proj_ratio = min(1.0, base_proj + tech_factor + desc_factor)

    results["project_descriptions"] = {
        "ratio": proj_ratio,
        "count": proj_count,
        "projects_with_tech": proj_with_tech,
    }

    # 6. Education (10 pts)
    edu_count = len(education_records)
    has_degree = False
    has_dates = False
    has_gpa_or_honors = False

    for edu in education_records:
        if getattr(edu, "degree_name", None) or getattr(edu, "degree", None):
            has_degree = True
        if getattr(edu, "start_date", None) or getattr(edu, "end_date", None) or getattr(edu, "graduation_year", None):
            has_dates = True
        if getattr(edu, "grade", None) or getattr(edu, "gpa", None):
            has_gpa_or_honors = True

    if edu_count == 0:
        edu_ratio = 0.0
    else:
        edu_ratio = 0.5
        if has_degree:
            edu_ratio += 0.3
        if has_dates:
            edu_ratio += 0.1
        if has_gpa_or_honors:
            edu_ratio += 0.1
        edu_ratio = min(1.0, edu_ratio)

    results["education"] = {
        "ratio": edu_ratio,
        "count": edu_count,
        "has_degree": has_degree,
        "has_dates": has_dates,
    }

    # 7. Achievements & Certifications (5 pts)
    cert_count = len(certifications)
    ach_count = len(achievements)
    total_validations = cert_count + ach_count

    if total_validations == 0:
        ach_ratio = 0.2  # Neutral baseline if absent
    elif total_validations == 1:
        ach_ratio = 0.7
    else:
        ach_ratio = 1.0

    results["achievements"] = {
        "ratio": ach_ratio,
        "certifications_count": cert_count,
        "achievements_count": ach_count,
    }

    # 8. Content Clarity (10 pts)
    # Avoid rewarding length! Evaluate structure, word density, and readability
    if word_count == 0:
        clarity_ratio = 0.0
    elif word_count < 100:
        clarity_ratio = 0.3
    elif 150 <= word_count <= 900:
        # Ideal 1-2 page resume length
        clarity_ratio = 0.95
    elif 900 < word_count <= 1400:
        # Acceptable for senior candidates
        clarity_ratio = 0.85
    else:
        # Length padding / Wall of text penalty
        clarity_ratio = 0.65

    results["content_clarity"] = {
        "ratio": clarity_ratio,
        "word_count": word_count,
    }

    return results
