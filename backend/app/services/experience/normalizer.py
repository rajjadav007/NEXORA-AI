"""
Experience Normalizer
Phase 3 | Feature 15: Experience Analysis
Normalizes company names, job titles, employment types, and technology mentions.
"""

import re
from typing import Optional, List, Tuple

# Comprehensive mapping of common tech keywords and aliases
TECH_TAXONOMY = {
    # Languages
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "golang": "Go",
    "go": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "bash": "Bash",
    "shell": "Shell",

    # Frameworks & Libraries
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "express.js": "Express.js",
    "spring": "Spring Boot",
    "spring boot": "Spring Boot",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "transformers": "Hugging Face Transformers",
    "huggingface": "Hugging Face",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",

    # Databases & Storage
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "pgvector": "pgvector",
    "pinecone": "Pinecone",
    "chroma": "ChromaDB",
    "chromadb": "ChromaDB",
    "qdrant": "Qdrant",

    # Cloud & DevOps
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "ci/cd": "CI/CD",
    "linux": "Linux",
    "terraform": "Terraform",
    "kafka": "Apache Kafka",
    "rabbitmq": "RabbitMQ",
    "celery": "Celery",
    "graphql": "GraphQL",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "ollama": "Ollama",
}

# Employment type indicators
EMPLOYMENT_TYPE_RULES = [
    (r"\b(?:intern|internship|summer\s+intern|trainee|co-?op)\b", "internship"),
    (r"\b(?:freelance|freelancer|self-?employed|independent\s+contractor)\b", "freelance"),
    (r"\b(?:contract|contractor|contract\s+basis|temp|temporary)\b", "contract"),
    (r"\b(?:part-?time)\b", "part_time"),
    (r"\b(?:apprentice|apprenticeship)\b", "apprenticeship"),
    (r"\b(?:research\s+assistant|research\s+fellow|researcher|post-?doc|graduate\s+researcher)\b", "research"),
    (r"\b(?:volunteer|volunteering)\b", "volunteer"),
    (r"\b(?:full-?time|permanent)\b", "full_time"),
]


def normalize_company(company: Optional[str]) -> Optional[str]:
    """
    Cleans and normalizes company name while strictly preserving original name.
    Does not invent company names.
    """
    if not company or not company.strip():
        return None

    cleaned = company.strip()
    # Strip common leading punctuation
    cleaned = re.sub(r"^[\s\-_•|:]+", "", cleaned)
    # Strip trailing punctuation
    cleaned = re.sub(r"[\s\-_•|:,]+$", "", cleaned)
    # Normalize multiple whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if not cleaned or len(cleaned) < 2:
        return None

    return cleaned


def normalize_job_title(title: Optional[str]) -> Optional[str]:
    """
    Normalizes job title formatting without upgrading or inferring seniority.
    """
    if not title or not title.strip():
        return None

    cleaned = title.strip()
    cleaned = re.sub(r"^[\s\-_•|:]+", "", cleaned)
    cleaned = re.sub(r"[\s\-_•|:,]+$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if not cleaned or len(cleaned) < 2:
        return None

    # Title casing if completely uppercase or lowercase
    if cleaned.isupper() or cleaned.islower():
        cleaned = cleaned.title()

    return cleaned


def detect_employment_type(
    job_title: Optional[str] = None,
    raw_text: Optional[str] = None,
    explicit_type: Optional[str] = None,
) -> str:
    """
    Detects employment type based on explicit evidence in job title or section text.
    Defaults to 'full_time' if employment is professional and no special modifier exists.
    """
    if explicit_type:
        clean_exp = explicit_type.lower().replace("-", "_").replace(" ", "_")
        valid_types = {
            "full_time", "part_time", "internship", "freelance",
            "contract", "apprenticeship", "research", "volunteer", "other"
        }
        if clean_exp in valid_types:
            return clean_exp

    text_to_search = f"{job_title or ''} {raw_text or ''}".lower()

    for pattern, emp_type in EMPLOYMENT_TYPE_RULES:
        if re.search(pattern, text_to_search, re.IGNORECASE):
            return emp_type

    return "full_time"


def extract_technologies_from_text(text: str) -> List[str]:
    """
    Identifies technologies mentioned in experience text and normalizes them.
    Preserves unique normalized mentions.
    """
    if not text or not text.strip():
        return []

    found = {}
    lower_text = f" {text.lower()} "

    # Sort keys by length descending to match multi-word terms first (e.g. spring boot before spring)
    sorted_keys = sorted(TECH_TAXONOMY.keys(), key=lambda k: len(k), reverse=True)

    for term in sorted_keys:
        # Match as word boundary (accounting for +, #, etc.)
        escaped_term = re.escape(term)
        pattern = rf"(?<![a-zA-Z0-9_]){escaped_term}(?![a-zA-Z0-9_])"
        if re.search(pattern, lower_text):
            canonical = TECH_TAXONOMY[term]
            found[canonical] = True

    return list(found.keys())
