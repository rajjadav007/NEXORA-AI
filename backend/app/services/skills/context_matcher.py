"""
Contextual Skill Matcher and Disambiguation Engine
Phase 3 | Feature 17: Skill Normalization
Resolves ambiguous skill tokens (such as 'R', 'Go', 'C', 'Word') using section context and surrounding tokens.
"""

import re
from typing import Optional, Tuple, List, Dict, Any

# Ambiguous tokens mapped to target canonical technology and required technical indicator keywords
AMBIGUOUS_TERMS: Dict[str, Dict[str, Any]] = {
    "r": {
        "canonical": "R",
        "category": "Programming Languages",
        "indicators": [
            "data science", "statistics", "statistical", "machine learning", "ggplot", "dplyr",
            "tidyverse", "biostatistics", "analytics", "r programming", "rstudio", "python",
            "programming", "scripting", "language", "data analysis", "shiny", "cran"
        ],
        "negative_indicators": ["grades", "grade r", "section r", "r&d", "research & development"]
    },
    "go": {
        "canonical": "Go",
        "category": "Programming Languages",
        "indicators": [
            "golang", "backend", "concurrency", "goroutines", "docker", "kubernetes",
            "grpc", "microservices", "gin", "fiber", "programming language", "developer", "distributed"
        ],
        "negative_indicators": ["go to", "ready to go", "go through", "let go", "on the go"]
    },
    "c": {
        "canonical": "C",
        "category": "Programming Languages",
        "indicators": [
            "c++", "embedded", "linux", "kernel", "systems programming", "memory management",
            "pointers", "compilers", "c/c++", "assembly", "c language", "low-level"
        ],
        "negative_indicators": ["vitamin c", "suite c", "grade c", "part c", "c level"]
    },
    "word": {
        "canonical": "Microsoft Word",
        "category": "Tools",
        "indicators": [
            "office", "excel", "powerpoint", "ms word", "microsoft", "documentation",
            "typing", "spreadsheets", "word processing"
        ],
        "negative_indicators": ["in other words", "word of mouth", "written word"]
    },
    "py": {
        "canonical": "Python",
        "category": "Programming Languages",
        "indicators": [
            "scripting", "backend", "numpy", "pandas", "django", "flask", "fastapi",
            "data science", "machine learning", "automation", "python"
        ],
        "negative_indicators": []
    }
}


def disambiguate_token(
    raw_token: str,
    section_name: Optional[str] = None,
    context_text: Optional[str] = None,
    surrounding_skills: Optional[List[str]] = None,
) -> Tuple[Optional[str], Optional[str], float, str]:
    """
    Evaluates whether an ambiguous token represents a valid canonical technology.
    Returns (canonical_name, category, confidence, status).
    Status can be 'normalized', 'pending_review', or 'unknown'.
    """
    clean_token = raw_token.strip().lower()

    if clean_token not in AMBIGUOUS_TERMS:
        return None, None, 0.0, "unknown"

    spec = AMBIGUOUS_TERMS[clean_token]
    canonical = spec["canonical"]
    category = spec["category"]
    indicators = spec["indicators"]
    negative_indicators = spec["negative_indicators"]

    search_corpus = ""
    if section_name:
        search_corpus += f" {section_name.lower()} "
    if context_text:
        search_corpus += f" {context_text.lower()} "
    if surrounding_skills:
        search_corpus += " " + " ".join(s.lower() for s in surrounding_skills) + " "

    # Check negative indicators first
    for neg in negative_indicators:
        if neg in search_corpus:
            return raw_token, "Other", 0.3, "pending_review"

    # Count positive indicators
    matched_count = 0
    for ind in indicators:
        if ind in search_corpus:
            matched_count += 1

    # In explicit skill sections, we give higher baseline weight
    is_skill_section = bool(
        section_name and any(kw in section_name.lower() for kw in ("skill", "technolog", "stack", "competenc", "language"))
    )

    if matched_count >= 2 or (is_skill_section and matched_count >= 1):
        return canonical, category, 0.90, "normalized"
    elif matched_count == 1 or is_skill_section:
        # Suggest canonical but flag for review
        return canonical, category, 0.65, "pending_review"
    else:
        # Insufficient context: preserve original and flag for manual confirmation
        return raw_token, "Other", 0.40, "pending_review"
