"""
False Merge Prevention Guard
Phase 3 | Feature 17: Skill Normalization
Explicitly enforces separation of distinct technologies that share lexical or prefix similarities.
"""

from typing import Set, Tuple

# Pairwise distinctions that must NEVER be merged
DISTINCT_PAIRS: Set[Tuple[str, str]] = {
    ("java", "javascript"),
    ("javascript", "java"),
    ("react", "react native"),
    ("react native", "react"),
    ("python", "pytorch"),
    ("pytorch", "python"),
    ("aws", "azure"),
    ("azure", "aws"),
    ("html", "html5"),
    ("html5", "html"),
    ("machine learning", "deep learning"),
    ("deep learning", "machine learning"),
    ("sql", "postgresql"),
    ("postgresql", "sql"),
    ("sql", "mysql"),
    ("mysql", "sql"),
    ("sql", "sqlite"),
    ("sqlite", "sql"),
    ("git", "github"),
    ("github", "git"),
    ("git", "gitlab"),
    ("gitlab", "git"),
    ("langchain", "langgraph"),
    ("langgraph", "langchain"),
    ("c", "c++"),
    ("c++", "c"),
    ("c", "c#"),
    ("c#", "c"),
    ("r", "rust"),
    ("rust", "r"),
    ("go", "golang"),  # Note: Go and Golang are the SAME, but Go is distinct from Google
    ("go", "google"),
    ("google", "go"),
}


def are_distinct_technologies(skill_a: str, skill_b: str) -> bool:
    """
    Returns True if skill_a and skill_b are strictly distinct technologies
    and must NEVER be merged together under any circumstance.
    """
    if not skill_a or not skill_b:
        return False

    a_lower = skill_a.strip().lower()
    b_lower = skill_b.strip().lower()

    if a_lower == b_lower:
        return False

    return (a_lower, b_lower) in DISTINCT_PAIRS or (b_lower, a_lower) in DISTINCT_PAIRS


def validate_canonical_assignment(original_input: str, proposed_canonical: str) -> bool:
    """
    Validates whether a proposed canonical assignment violates false-merge guardrails.
    Returns False if the assignment represents an illegal false merge.
    """
    if not original_input or not proposed_canonical:
        return False

    orig_lower = original_input.strip().lower()
    prop_lower = proposed_canonical.strip().lower()

    if orig_lower == prop_lower:
        return True

    if are_distinct_technologies(orig_lower, prop_lower):
        return False

    # Guard specific prefixes
    if orig_lower in ("java", "core java") and "javascript" in prop_lower:
        return False
    if orig_lower in ("react native", "react-native") and prop_lower == "react":
        return False
    if orig_lower in ("pytorch", "torch") and prop_lower == "python":
        return False
    if orig_lower == "sql" and prop_lower in ("postgresql", "mysql", "sqlite", "oracle"):
        return False
    if orig_lower in ("postgresql", "postgres") and prop_lower == "sql":
        return False
    if orig_lower in ("github", "gh") and prop_lower == "git":
        return False
    if orig_lower == "git" and prop_lower in ("github", "gitlab", "bitbucket"):
        return False
    if orig_lower in ("deep learning", "dl") and prop_lower == "machine learning":
        return False
    if orig_lower == "langgraph" and prop_lower == "langchain":
        return False

    return True
