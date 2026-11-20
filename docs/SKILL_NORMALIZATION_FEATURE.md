# Feature #17: Skill Normalization Engine

## 1. Feature Objective
The Skill Normalization Engine standardizes candidate technical and professional skill names extracted from resumes. It maps aliases, abbreviations, alternative spellings, case variations, and formatting variations into a clean, canonical skill profile. It preserves all original names, section provenances, and source evidence text snippets without merging distinct technologies merely because their names are similar.

---

## 2. Architecture & Pipeline
```
Raw / Extracted Skills (Resume Text or JSON)
        |
        v
Layer 1: Text & Formatting Normalization (Whitespace, Casing, Unicode, Symbols)
        |
        v
Layer 2: Canonical & Alias Dictionary Lookup (Hash-indexed lookup, Version 1.0.0)
        |
        v
Layer 3: Contextual Disambiguation Engine (Ambiguous tokens: R, Go, C, Word)
        |
        v
Layer 4: False Merge Guard Verification (Hardcoded negative guardrails)
        |
        v
Layer 5: Local Ollama Semantic Suggestion (Ambiguous / Unknown edge cases)
        |
        v
Layer 6: Duplicate Detection & Evidence Consolidation (Merge duplicate mentions across sections)
        |
        v
Database Persistence (PostgreSQL resume_skills, skills, skill_aliases)
```

---

## 3. Canonical Skill Schema & Dictionary
Centralized catalog with seed definitions for over 200 software, AI, data, and soft skills across categories:
- **Programming Languages**: JavaScript, TypeScript, Python, Java, C++, C#, Go, Rust, PHP, Ruby, Swift, Kotlin, R, SQL, HTML, CSS, Bash, Scala, Dart.
- **Frameworks & Libraries**: React, React Native, Next.js, Vue.js, Angular, Node.js, Express.js, FastAPI, Django, Flask, Spring Boot, PyTorch, TensorFlow, Keras, scikit-learn, Pandas, NumPy, LangChain, LangGraph, Tailwind CSS, Bootstrap, Flutter, .NET.
- **Databases**: PostgreSQL, MySQL, SQLite, MongoDB, Redis, Elasticsearch, pgvector, Pinecone, ChromaDB, Qdrant.
- **Cloud & DevOps**: Docker, Kubernetes, AWS, Azure, Google Cloud, Linux, Terraform, CI/CD, Apache Kafka, RabbitMQ, Celery, REST APIs, GraphQL.
- **Machine Learning & AI**: Machine Learning, Deep Learning, Natural Language Processing, Large Language Models, Generative AI, Computer Vision, RAG, Ollama.
- **Tools**: Git, GitHub, GitLab, Jira, Postman, Figma.
- **Soft Skills**: Leadership, Communication, Problem Solving, Project Management, Collaboration.

---

## 4. False Merge Prevention Matrix
Strictly enforces technological boundaries:
- `Java` != `JavaScript`
- `React` != `React Native`
- `Python` != `PyTorch`
- `AWS` != `Azure`
- `SQL` != `PostgreSQL`
- `Git` != `GitHub`
- `LangChain` != `LangGraph`
- `Machine Learning` != `Deep Learning`
- `HTML` != `HTML5`

---

## 5. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/resumes/{resume_id}/skills/extract` | POST | Extracts and normalizes skills from resume text |
| `/api/v1/resumes/{resume_id}/skills/normalize` | POST | Normalizes direct list of raw skill strings |
| `/api/v1/resumes/{resume_id}/skills` | GET | Retrieves normalized skills and summary |
| `/api/v1/resumes/{resume_id}/skills/reprocess` | POST | Reprocesses while protecting manual user edits |
| `/api/v1/resumes/{resume_id}/skills/summary` | GET | Returns normalization metrics and category distribution |
| `/api/v1/resumes/{resume_id}/skills/pending-reviews` | GET | Returns ambiguous skills awaiting human confirmation |
| `/api/v1/resumes/{resume_id}/skills/{skill_id}/confirm` | POST | Confirms proposed canonical mapping |
| `/api/v1/resumes/{resume_id}/skills/{skill_id}/reject` | POST | Rejects mapping, reverting to raw original name |
| `/api/v1/resumes/{resume_id}/skills/{skill_id}` | PATCH | Manually updates canonical name or category |
| `/api/v1/resumes/{resume_id}/skills/{skill_id}` | DELETE | Deletes skill from profile |
| `/api/v1/skills/dictionary` | GET | Retrieves global canonical dictionary |
| `/api/v1/skills/dictionary/alias` | POST | Adds new alias to dictionary, rejecting conflicts |

---

## 6. Database Changes
Alembic migration `2026_11_20_1800-e8f9a0b1c2d3_create_skills_tables.py` introduces:
- `skills`: Canonical catalog (`id`, `name`, `normalized_name`, `category`, `skill_type`, `version`, `is_active`).
- `skill_aliases`: Alternative aliases and abbreviations mapped to canonical skills (`id`, `skill_id`, `alias`, `normalized_alias`).
- `resume_skills`: Resume-specific normalized skills (`id`, `resume_id`, `user_id`, `skill_id`, `original_name`, `canonical_name`, `category`, `skill_type`, `normalization_method`, `confidence_score`, `normalization_status`, `source_sections`, `source_evidence`, `aliases_detected`, `occurrence_count`, `is_manually_edited`, `manually_edited_fields`, `dictionary_version`).

---

## 7. Testing Instructions
- Backend tests: `pytest backend/tests/services/test_skill_normalization.py backend/tests/test_skills_api.py`
- Full backend suite: `pytest backend/tests`
- Frontend tests: `npm test --prefix frontend`
- Production build: `npm run build --prefix frontend`

---

## 8. Known Limitations
- Extremely obscure proprietary tools with fewer than 2 letters (e.g., custom single-character code names other than R/C) are treated as unknown and preserved as original name with `pending_review` status.
- Mention frequency (`occurrence_count`) reflects evidence density across resume sections, not candidate proficiency level.
