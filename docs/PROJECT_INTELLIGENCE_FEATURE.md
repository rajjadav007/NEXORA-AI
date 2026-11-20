# Feature #18: Project Intelligence Engine

## 1. Feature Objective
The Project Intelligence Engine analyzes cleaned resume text to extract structured information about every candidate project mentioned in the resume. It understands project purpose, domain, architectural solutions, individual candidate contributions, team context, technologies, outcomes, and connects extracted technologies directly with Feature #17's canonical skill dictionary.

---

## 2. Architecture & Pipeline
```
Cleaned Resume Text
        |
        v
Section Detector & Chunker (`section_detector.py`)
- Detects project sections (Academic, Personal, Key, Hackathon, Open Source, etc.)
- Segments sections into isolated individual project blocks
        |
        v
Deterministic Extractor (`deterministic_extractor.py`)
- Extracts titles, dates, timeline (`is_ongoing`), team type, team size, candidate roles
- Extracts URLs (GitHub, demo, website, docs)
- Extracts quantifiable measurable outcomes (%, latencies, counts) and awards
- Scans raw technology mentions
        |
        v
Feature #17 Skill Linker (`skill_linker.py`)
- Maps extracted technologies to canonical skills using Feature #17 skill dictionary
- Assigns canonical ID, canonical name, and verified category
        |
        v
AI Semantic Extractor (`ai_extractor.py`)
- Local Ollama fallback (`qwen2.5:3b`) for narrative structuring
- Extracts problem statement, proposed architecture, candidate role, domain
        |
        v
Project Deduplicator (`deduplicator.py`)
- Consolidates project candidates mentioned across multiple sections
- Merges technologies, URLs, achievements, and text evidence
        |
        v
Evidence-Based Confidence Scorer (`confidence_scorer.py`)
- Computes structural confidence score [0.0 - 1.0] without relying on LLM self-reporting
        |
        v
Manual Edit Protection & Persistence (`service.py`)
- Protects user modifications during reprocessing
- Stores to PostgreSQL `projects` table (native JSONB in prod, JSON in SQLite tests)
        |
        v
Interactive Frontend Component (`ProjectsSection.jsx`)
- Summary analytics bar, category tabs, search filter, rich project cards
- Expandable architecture drawer, external links, review status confirmation
- Create/edit project modal and delete workflow
```

---

## 3. Supported Project Categories
1. **Academic Project** (`academic`): Coursework, university thesis, senior capstone.
2. **Personal Project** (`personal`): Self-developed side projects, hobby tools.
3. **Hackathon Project** (`hackathon`): MLH, Smart India Hackathon, competition submissions.
4. **Research Project** (`research`): Published papers (IEEE, arXiv), laboratory investigations.
5. **Open Source Project** (`open_source`): Public GitHub repositories, open-source package contributions.
6. **Internship Project** (`internship`): Work delivered during internship tenures.
7. **Professional / Work Project** (`professional`): Enterprise production systems.
8. **Freelance Project** (`freelance`): Client projects (e.g. Upwork, contract delivery).
9. **Other** (`other`): Unspecified or ambiguous project types.

---

## 4. Database Schema
Stored in PostgreSQL table `projects`:
- `id` (UUID, Primary Key)
- `resume_id` (UUID, Foreign Key to `resumes.id`, ON DELETE CASCADE)
- `user_id` (UUID, Foreign Key to `users.id`, Nullable)
- `project_title` (VARCHAR(255))
- `normalized_title` (VARCHAR(255), Index)
- `project_category` (VARCHAR(50), Index)
- `short_description` (TEXT)
- `detailed_description` (TEXT)
- `problem_statement` (TEXT)
- `proposed_solution` (TEXT)
- `domain` (VARCHAR(100), Index)
- `project_role` (VARCHAR(100))
- `team_type` (VARCHAR(30)) — `individual`, `team`, `unknown`
- `team_size` (INTEGER)
- `start_date` (VARCHAR(50))
- `end_date` (VARCHAR(50))
- `is_ongoing` (BOOLEAN)
- `technologies` (JSONB)
- `skills` (JSONB) — Feature #17 canonical skill linkages
- `responsibilities` (JSONB)
- `achievements` (JSONB)
- `measurable_outcomes` (JSONB)
- `project_links` (JSONB) — `github`, `demo`, `website`, `docs`
- `source_section` (VARCHAR(100))
- `source_evidence` (JSONB)
- `confidence` (FLOAT)
- `extraction_method` (VARCHAR(30))
- `review_status` (VARCHAR(30), Index) — `pending`, `confirmed`, `needs_review`
- `is_manually_edited` (BOOLEAN, Index)
- `manually_edited_fields` (JSONB)
- `created_at` / `updated_at` (TIMESTAMPTZ)

---

## 5. API Endpoints
All endpoints mounted at `/api/v1/resumes/{resume_id}/projects`:
- `POST /extract`: Extract projects from resume text (supports `reprocess` and `force_overwrite`).
- `GET /`: Retrieve all structured project records and summary analytics.
- `GET /summary`: Aggregate counts (categories, domains, unique technologies, repos, demos, pending).
- `GET /pending-reviews`: Filter projects pending user verification.
- `GET /{project_id}`: Single project detail record.
- `GET /{project_id}/skills`: Linked Feature #17 canonical skills.
- `POST /`: Manually add a project entry.
- `PATCH /{project_id}`: Update project fields manually (activates `is_manually_edited` protection).
- `POST /{project_id}/confirm`: Confirm project review status.
- `DELETE /{project_id}`: Remove project record.
- `POST /reprocess`: Reprocess extraction with manual edit preservation.

---

## 6. Verification & Test Coverage
- **Unit Tests (`backend/tests/services/test_project_intelligence.py`)**: 11 passed (1.51s).
- **API Tests (`backend/tests/test_projects_api.py`)**: 2 passed (2.21s).
- **Backend Full Regression**: 244 passed, 0 failures (9.02s).
- **Frontend Unit Tests (`frontend/tests/projects.test.mjs`)**: 12 passed.
- **Frontend Full Suite**: 55 passed, 0 failures (1.80s).
- **Frontend Production Build**: `vite build` completed cleanly in 3.79s without errors.
