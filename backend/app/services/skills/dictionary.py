"""
Canonical Skill Dictionary Manager
Phase 3 | Feature 17: Skill Normalization
Centralized, maintainable, versioned skill catalog with fast in-memory indexing and DB synchronization.
"""

import uuid
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.services.skills.formatter import create_lookup_key, normalize_skill_text
from app.models.skills import Skill, SkillAlias

logger = logging.getLogger(__name__)

DICTIONARY_VERSION = "1.0.0"

# Comprehensive structured seed taxonomy
SEED_CANONICAL_SKILLS: List[Dict[str, Any]] = [
    # --- Programming Languages ---
    {
        "name": "JavaScript",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["JS", "Javascript", "Java Script", "ES6", "ES7", "ECMAScript", "Vanilla JS"],
    },
    {
        "name": "TypeScript",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["TS", "Typescript", "Type Script"],
    },
    {
        "name": "Python",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Python3", "Python 3", "Py3"],
    },
    {
        "name": "Java",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Core Java", "Java 8", "Java 11", "Java 17", "Java 21", "J2EE"],
    },
    {
        "name": "C++",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["CPP", "Cplusplus", "C plus plus", "Modern C++"],
    },
    {
        "name": "C#",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["CSharp", "C Sharp", "C-Sharp"],
    },
    {
        "name": "C",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["C Language", "ANSI C"],
    },
    {
        "name": "Go",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Golang", "Go Language"],
    },
    {
        "name": "Rust",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Rustlang", "Rust-lang"],
    },
    {
        "name": "PHP",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["PHP7", "PHP8"],
    },
    {
        "name": "Ruby",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["RubyLang"],
    },
    {
        "name": "Swift",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Swift 5", "SwiftUI Language"],
    },
    {
        "name": "Kotlin",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Kotlin/JVM"],
    },
    {
        "name": "R",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["R Language", "R Programming", "R-Project"],
    },
    {
        "name": "SQL",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Structured Query Language", "ANSI SQL", "T-SQL", "PL/SQL"],
    },
    {
        "name": "HTML",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["HTML5", "Hypertext Markup Language"],
    },
    {
        "name": "CSS",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["CSS3", "Cascading Style Sheets"],
    },
    {
        "name": "Bash",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Shell", "Bash Scripting", "Shell Scripting", "Zsh", "Sh"],
    },
    {
        "name": "Scala",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Scala 3"],
    },
    {
        "name": "Dart",
        "category": "Programming Languages",
        "skill_type": "technical",
        "aliases": ["Dartlang"],
    },

    # --- Frameworks & Libraries ---
    {
        "name": "React",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["ReactJS", "React.js", "React JS"],
    },
    {
        "name": "React Native",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["ReactNative", "React-Native"],
    },
    {
        "name": "Next.js",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["NextJS", "Next", "Next js"],
    },
    {
        "name": "Vue.js",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Vue", "VueJS", "Vue 3", "Vue2"],
    },
    {
        "name": "Angular",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["AngularJS", "Angular 2+", "Angular 14"],
    },
    {
        "name": "Node.js",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["NodeJS", "Node", "Node js"],
    },
    {
        "name": "Express.js",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Express", "ExpressJS", "Express js"],
    },
    {
        "name": "FastAPI",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Fast API", "Fastapi"],
    },
    {
        "name": "Django",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Django REST Framework", "DRF"],
    },
    {
        "name": "Flask",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Flask API"],
    },
    {
        "name": "Spring Boot",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["SpringBoot", "Spring-Boot", "Spring Framework", "Spring"],
    },
    {
        "name": "PyTorch",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Torch", "Pytorch"],
    },
    {
        "name": "TensorFlow",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Tensorflow", "TF"],
    },
    {
        "name": "Keras",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["tf.keras"],
    },
    {
        "name": "scikit-learn",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Scikit Learn", "scikit learn", "sklearn", "Sklearn"],
    },
    {
        "name": "Pandas",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["pandas library"],
    },
    {
        "name": "NumPy",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Numpy", "numpy library"],
    },
    {
        "name": "LangChain",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Langchain", "Lang chain"],
    },
    {
        "name": "LangGraph",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Langgraph", "Lang graph"],
    },
    {
        "name": "Tailwind CSS",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Tailwind", "TailwindCSS"],
    },
    {
        "name": "Bootstrap",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Twitter Bootstrap", "Bootstrap 5"],
    },
    {
        "name": "Flutter",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": ["Flutter SDK"],
    },
    {
        "name": ".NET",
        "category": "Frameworks & Libraries",
        "skill_type": "technical",
        "aliases": [".NET Core", "DOTNET", "ASP.NET", "ASP.NET Core"],
    },

    # --- Databases ---
    {
        "name": "PostgreSQL",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["Postgres", "Postgre SQL", "Postgresql", "PGSQL", "Postgre"],
    },
    {
        "name": "MySQL",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["My SQL", "Mysql"],
    },
    {
        "name": "SQLite",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["Sqlite3", "SQLite3"],
    },
    {
        "name": "MongoDB",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["Mongo", "Mongodb"],
    },
    {
        "name": "Redis",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["Redis Cache"],
    },
    {
        "name": "Elasticsearch",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["Elastic Search", "Elastic", "ELK Stack"],
    },
    {
        "name": "pgvector",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["pg vector", "PGVector"],
    },
    {
        "name": "Pinecone",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["Pinecone DB"],
    },
    {
        "name": "ChromaDB",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["Chroma", "Chroma DB"],
    },
    {
        "name": "Qdrant",
        "category": "Databases",
        "skill_type": "technical",
        "aliases": ["Qdrant Vector DB"],
    },

    # --- Cloud & DevOps ---
    {
        "name": "Docker",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["Docker Container", "Dockerfiles", "Docker Compose"],
    },
    {
        "name": "Kubernetes",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["K8s", "k8s", "Kube", "K8S"],
    },
    {
        "name": "AWS",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["Amazon Web Services", "Amazon AWS", "AWS Cloud"],
    },
    {
        "name": "Azure",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["Microsoft Azure", "MS Azure"],
    },
    {
        "name": "Google Cloud",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["GCP", "Google Cloud Platform"],
    },
    {
        "name": "Linux",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["Ubuntu", "Debian", "CentOS", "RedHat", "Unix"],
    },
    {
        "name": "Terraform",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["TF", "HashiCorp Terraform"],
    },
    {
        "name": "CI/CD",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["Continuous Integration", "Continuous Delivery", "Continuous Deployment", "CI-CD"],
    },
    {
        "name": "Apache Kafka",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["Kafka"],
    },
    {
        "name": "RabbitMQ",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["Rabbit MQ"],
    },
    {
        "name": "Celery",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["Celery Worker"],
    },
    {
        "name": "REST APIs",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["REST", "RESTful", "REST API", "RESTful APIs", "RESTful Web Services"],
    },
    {
        "name": "GraphQL",
        "category": "Cloud & DevOps",
        "skill_type": "technical",
        "aliases": ["Graph QL"],
    },

    # --- Machine Learning & AI ---
    {
        "name": "Machine Learning",
        "category": "Machine Learning & AI",
        "skill_type": "technical",
        "aliases": ["ML"],
    },
    {
        "name": "Deep Learning",
        "category": "Machine Learning & AI",
        "skill_type": "technical",
        "aliases": ["DL"],
    },
    {
        "name": "Natural Language Processing",
        "category": "Machine Learning & AI",
        "skill_type": "technical",
        "aliases": ["NLP"],
    },
    {
        "name": "Large Language Models",
        "category": "Machine Learning & AI",
        "skill_type": "technical",
        "aliases": ["LLM", "LLMs"],
    },
    {
        "name": "Generative AI",
        "category": "Machine Learning & AI",
        "skill_type": "technical",
        "aliases": ["Gen AI", "GenAI", "Generative Artificial Intelligence"],
    },
    {
        "name": "Computer Vision",
        "category": "Machine Learning & AI",
        "skill_type": "technical",
        "aliases": ["CV", "OpenCV"],
    },
    {
        "name": "Retrieval-Augmented Generation",
        "category": "Machine Learning & AI",
        "skill_type": "technical",
        "aliases": ["RAG"],
    },
    {
        "name": "Ollama",
        "category": "Machine Learning & AI",
        "skill_type": "technical",
        "aliases": ["Ollama LLM"],
    },

    # --- Tools ---
    {
        "name": "Git",
        "category": "Tools",
        "skill_type": "tool",
        "aliases": ["Git CLI", "Version Control"],
    },
    {
        "name": "GitHub",
        "category": "Tools",
        "skill_type": "tool",
        "aliases": ["Github", "GH"],
    },
    {
        "name": "GitLab",
        "category": "Tools",
        "skill_type": "tool",
        "aliases": ["Gitlab"],
    },
    {
        "name": "Jira",
        "category": "Tools",
        "skill_type": "tool",
        "aliases": ["Atlassian Jira"],
    },
    {
        "name": "Postman",
        "category": "Tools",
        "skill_type": "tool",
        "aliases": ["Postman API"],
    },
    {
        "name": "Figma",
        "category": "Tools",
        "skill_type": "tool",
        "aliases": ["Figma UI"],
    },

    # --- Soft Skills ---
    {
        "name": "Leadership",
        "category": "Soft Skills",
        "skill_type": "soft",
        "aliases": ["Team Leadership", "Tech Leadership", "Leading Teams"],
    },
    {
        "name": "Communication",
        "category": "Soft Skills",
        "skill_type": "soft",
        "aliases": ["Oral Communication", "Written Communication", "Interpersonal Skills"],
    },
    {
        "name": "Problem Solving",
        "category": "Soft Skills",
        "skill_type": "soft",
        "aliases": ["Critical Thinking", "Troubleshooting", "Analytical Thinking"],
    },
    {
        "name": "Project Management",
        "category": "Soft Skills",
        "skill_type": "soft",
        "aliases": ["Agile", "Scrum", "Sprint Planning", "Kanban"],
    },
    {
        "name": "Collaboration",
        "category": "Soft Skills",
        "skill_type": "soft",
        "aliases": ["Teamwork", "Cross-functional Collaboration"],
    },
]


class SkillDictionary:
    """In-memory fast lookup dictionary backed by optional DB synchronization."""

    def __init__(self):
        self.version: str = DICTIONARY_VERSION
        # Map: canonical_name -> dict representation
        self._canonical_catalog: Dict[str, Dict[str, Any]] = {}
        # Map: normalized_key -> canonical_name
        self._key_to_canonical: Dict[str, str] = {}
        # Map: normalized_alias_key -> canonical_name
        self._alias_to_canonical: Dict[str, str] = {}
        # Load seed catalog
        self._load_seed_catalog()

    def _load_seed_catalog(self) -> None:
        """Populates in-memory lookup structures from seed dictionary."""
        for entry in SEED_CANONICAL_SKILLS:
            canonical_name = entry["name"]
            category = entry["category"]
            skill_type = entry.get("skill_type", "technical")
            aliases = entry.get("aliases", [])

            self._canonical_catalog[canonical_name] = {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, canonical_name.lower())),
                "name": canonical_name,
                "category": category,
                "skill_type": skill_type,
                "aliases": list(aliases),
                "version": self.version,
                "is_active": True,
            }

            canonical_key = create_lookup_key(canonical_name)
            self._key_to_canonical[canonical_key] = canonical_name

            for alias in aliases:
                alias_key = create_lookup_key(alias)
                if alias_key:
                    # Prevent conflicting mappings
                    self._alias_to_canonical[alias_key] = canonical_name

    def sync_from_db(self, db: Session) -> None:
        """Synchronizes and enriches the in-memory dictionary with custom DB skills and aliases."""
        try:
            db_skills = db.execute(select(Skill).where(Skill.is_active == True)).scalars().all()
            for s in db_skills:
                canonical_name = s.name
                if canonical_name not in self._canonical_catalog:
                    self._canonical_catalog[canonical_name] = {
                        "id": str(s.id),
                        "name": canonical_name,
                        "category": s.category,
                        "skill_type": s.skill_type,
                        "aliases": [a.alias for a in s.aliases if a.is_active],
                        "version": s.version,
                        "is_active": s.is_active,
                    }
                    self._key_to_canonical[create_lookup_key(canonical_name)] = canonical_name

            db_aliases = db.execute(select(SkillAlias).where(SkillAlias.is_active == True)).scalars().all()
            for a in db_aliases:
                alias_key = a.normalized_alias or create_lookup_key(a.alias)
                if a.skill and a.skill.name:
                    self._alias_to_canonical[alias_key] = a.skill.name
        except Exception as exc:
            logger.warning("Could not sync skill dictionary from database: %s", exc)

    def lookup(self, raw_skill_name: str) -> Optional[Tuple[Dict[str, Any], str, float]]:
        """
        Looks up a skill name in canonical and alias catalogs.
        Returns: Tuple of (canonical_entry, match_method, confidence) or None.
        match_method: 'exact_match', 'alias_match', or 'format_normalization'.
        """
        if not raw_skill_name:
            return None

        clean_text = normalize_skill_text(raw_skill_name)
        lookup_key = create_lookup_key(clean_text)

        if not lookup_key:
            return None

        # 1. Exact match by canonical name
        for canon_name, spec in self._canonical_catalog.items():
            if clean_text == canon_name:
                return spec, "exact_match", 1.0

        # 2. Match canonical by normalized key (format normalization)
        if lookup_key in self._key_to_canonical:
            canon_name = self._key_to_canonical[lookup_key]
            spec = self._canonical_catalog[canon_name]
            return spec, "format_normalization", 0.98

        # 3. Match via registered aliases
        if lookup_key in self._alias_to_canonical:
            canon_name = self._alias_to_canonical[lookup_key]
            spec = self._canonical_catalog[canon_name]
            return spec, "alias_match", 0.95

        return None

    def add_alias(
        self,
        canonical_name: str,
        new_alias: str,
        category: Optional[str] = None,
        skill_type: str = "technical",
        db: Optional[Session] = None,
    ) -> Tuple[bool, str]:
        """
        Adds a new alias to a canonical skill.
        Prevents conflicting assignments to other existing canonical skills.
        """
        clean_alias = normalize_skill_text(new_alias)
        alias_key = create_lookup_key(clean_alias)

        if not alias_key or not canonical_name:
            return False, "Invalid alias or canonical name."

        # Check conflicting mapping
        if alias_key in self._alias_to_canonical and self._alias_to_canonical[alias_key] != canonical_name:
            existing = self._alias_to_canonical[alias_key]
            return False, f"Alias '{new_alias}' is already mapped to canonical skill '{existing}'."

        if alias_key in self._key_to_canonical and self._key_to_canonical[alias_key] != canonical_name:
            existing = self._key_to_canonical[alias_key]
            return False, f"Alias '{new_alias}' conflicts with existing canonical skill '{existing}'."

        # Ensure canonical skill exists in catalog
        if canonical_name not in self._canonical_catalog:
            self._canonical_catalog[canonical_name] = {
                "id": str(uuid.uuid4()),
                "name": canonical_name,
                "category": category or "Other",
                "skill_type": skill_type,
                "aliases": [clean_alias],
                "version": self.version,
                "is_active": True,
            }
            self._key_to_canonical[create_lookup_key(canonical_name)] = canonical_name
        else:
            if clean_alias not in self._canonical_catalog[canonical_name]["aliases"]:
                self._canonical_catalog[canonical_name]["aliases"].append(clean_alias)

        self._alias_to_canonical[alias_key] = canonical_name

        # Persist to DB if session provided
        if db:
            try:
                skill_obj = db.execute(select(Skill).where(Skill.name == canonical_name)).scalar_one_or_none()
                if not skill_obj:
                    skill_obj = Skill(
                        id=uuid.uuid4(),
                        name=canonical_name,
                        normalized_name=create_lookup_key(canonical_name),
                        category=category or "Other",
                        skill_type=skill_type,
                        version=self.version,
                        is_active=True,
                    )
                    db.add(skill_obj)
                    db.flush()

                # Add alias record
                alias_obj = db.execute(
                    select(SkillAlias).where(
                        SkillAlias.skill_id == skill_obj.id,
                        SkillAlias.normalized_alias == alias_key,
                    )
                ).scalar_one_or_none()
                if not alias_obj:
                    alias_obj = SkillAlias(
                        id=uuid.uuid4(),
                        skill_id=skill_obj.id,
                        alias=clean_alias,
                        normalized_alias=alias_key,
                        is_active=True,
                    )
                    db.add(alias_obj)
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error("Failed to persist alias to database: %s", exc)
                return False, f"Database error: {str(exc)}"

        return True, f"Alias '{clean_alias}' mapped to '{canonical_name}' successfully."

    def list_canonical_skills(self) -> List[Dict[str, Any]]:
        """Returns all canonical skills currently registered."""
        return list(self._canonical_catalog.values())


# Global dictionary instance
skill_dictionary = SkillDictionary()
