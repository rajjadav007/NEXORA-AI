"""
Degree Normalizer and Level Classifier
Phase 3 | Feature 14: Education Analysis
Normalizes academic degree variations and determines academic level.
"""

import re
from typing import Tuple, Optional, Dict

# Known standard degree title mappings
# Pattern (regex) -> (Normalized Title, Degree Level)
DEGREE_MAPPING_RULES = [
    # Doctorate
    (r"\b(?:ph\.?d\.?|doctor of philosophy|doctorate)\b", ("Doctor of Philosophy", "doctorate")),
    (r"\b(?:d\.?phil\.?)\b", ("Doctor of Philosophy", "doctorate")),
    (r"\b(?:m\.?d\.?|doctor of medicine)\b", ("Doctor of Medicine", "doctorate")),

    # Postgraduate
    (r"\b(?:m\.?tech\.?|mtech|master of technology)\b", ("Master of Technology", "postgraduate")),
    (r"\b(?:m\.?e\.?|master of engineering)\b", ("Master of Engineering", "postgraduate")),
    (r"\b(?:m\.?c\.?a\.?|mca|master of computer applications?)\b", ("Master of Computer Applications", "postgraduate")),
    (r"\b(?:m\.?s\.?|master of science|msc|m\.?sc\.?)\b", ("Master of Science", "postgraduate")),
    (r"\b(?:m\.?b\.?a\.?|mba|master of business administration)\b", ("Master of Business Administration", "postgraduate")),
    (r"\b(?:m\.?com\.?|mcom|master of commerce)\b", ("Master of Commerce", "postgraduate")),
    (r"\b(?:m\.?a\.?|master of arts)\b", ("Master of Arts", "postgraduate")),
    (r"\b(?:master['’]s(?:\s+degree)?|masters?)\b", ("Master's Degree", "postgraduate")),
    (r"\b(?:post\s*graduate\s*diploma|pgdca|pgdm)\b", ("Post Graduate Diploma", "postgraduate")),

    # Undergraduate
    (r"\b(?:b\.?tech\.?|btech|bachelor of technology)\b", ("Bachelor of Technology", "undergraduate")),
    (r"\b(?:b\.?e\.?|bachelor of engineering)\b", ("Bachelor of Engineering", "undergraduate")),
    (r"\b(?:b\.?c\.?a\.?|bca|bachelor of computer applications?)\b", ("Bachelor of Computer Applications", "undergraduate")),
    (r"\b(?:b\.?s\.?|bachelor of science|bsc|b\.?sc\.?)\b", ("Bachelor of Science", "undergraduate")),
    (r"\b(?:b\.?com\.?|bcom|bachelor of commerce)\b", ("Bachelor of Commerce", "undergraduate")),
    (r"\b(?:b\.?a\.?|bachelor of arts)\b", ("Bachelor of Arts", "undergraduate")),
    (r"\b(?:b\.?b\.?a\.?|bba|bachelor of business administration)\b", ("Bachelor of Business Administration", "undergraduate")),
    (r"\b(?:b\.?des\.?|bachelor of design)\b", ("Bachelor of Design", "undergraduate")),
    (r"\b(?:b\.?arch\.?|bachelor of architecture)\b", ("Bachelor of Architecture", "undergraduate")),
    (r"\b(?:l\.?l\.?b\.?|bachelor of laws?)\b", ("Bachelor of Laws", "undergraduate")),
    (r"\b(?:bachelor['’]s(?:\s+degree)?|bachelors?|undergraduate)\b", ("Bachelor's Degree", "undergraduate")),

    # Diploma
    (r"\b(?:polytechnic|diploma in [a-zA-Z\s]+|diploma)\b", ("Diploma", "diploma")),

    # Higher Secondary (12th / Intermediate)
    (r"\b(?:12th(?:\s+grade|\s+standard)?|class\s+xii|higher\s+secondary|hsc|intermediate|senior\s+secondary|plus\s+two|\+2)\b",
     ("Higher Secondary School Certificate (12th)", "higher_secondary")),

    # High School (10th / Secondary)
    (r"\b(?:10th(?:\s+grade|\s+standard)?|class\s+x|secondary\s+school|ssc|matriculation|high\s+school)\b",
     ("Secondary School Certificate (10th)", "high_school")),
]


def normalize_degree(raw_degree: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalizes degree title and returns (normalized_degree, degree_level).
    Preserves original title if unrecognized.
    """
    if not raw_degree or not raw_degree.strip():
        return None, None

    clean = raw_degree.strip()

    for pattern, (canonical_title, level) in DEGREE_MAPPING_RULES:
        if re.search(pattern, clean, re.IGNORECASE):
            return canonical_title, level

    # If unrecognized, check for generic degree keywords
    lower = clean.lower()
    if "bachelor" in lower:
        return clean, "undergraduate"
    elif "master" in lower:
        return clean, "postgraduate"
    elif "doctor" in lower or "phd" in lower:
        return clean, "doctorate"
    elif "diploma" in lower:
        return clean, "diploma"
    elif "certificate" in lower or "certification" in lower:
        return clean, "certification"

    # Preserves original degree title and avoids incorrect normalization
    return clean, "other"


def classify_degree_level(raw_degree: Optional[str]) -> Optional[str]:
    """Returns the academic level (undergraduate, postgraduate, doctorate, etc.)."""
    _, level = normalize_degree(raw_degree)
    return level


def infer_field_of_study(raw_degree: Optional[str]) -> Optional[str]:
    """
    Infers the field of study from a degree string.
    e.g. 'B.Tech in Computer Science' -> 'Computer Science'
         'Bachelor of Computer Applications' -> 'Computer Applications'
         'M.Sc. Physics' -> 'Physics'
    """
    if not raw_degree:
        return None

    clean = raw_degree.strip()

    # Known standard fields
    common_fields = [
        "Computer Science and Engineering", "Computer Science & Engineering", "Computer Science",
        "Information Technology", "Computer Applications", "Software Engineering", "Data Science",
        "Artificial Intelligence", "Electronics and Communication", "Mechanical Engineering",
        "Civil Engineering", "Electrical Engineering", "Business Administration", "Commerce",
        "Physics", "Chemistry", "Mathematics", "Economics", "Finance", "Biology"
    ]
    for f in common_fields:
        if re.search(r"\b" + re.escape(f) + r"\b", clean, re.IGNORECASE):
            return f

    # Pattern: 'in <Field>'
    in_match = re.search(r"\b(?:in|major in)\s+([A-Za-z\s&,/-]+)", clean, re.IGNORECASE)
    if in_match:
        field = in_match.group(1).strip()
        field = re.sub(r"[()]", "", field).strip()
        if field and len(field) > 2:
            return field.title()

    return None
