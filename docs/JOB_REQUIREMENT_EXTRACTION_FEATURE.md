# Feature #36: Job Requirement Extraction

## Overview
Extracts structured employer requirements from saved job descriptions (Features #33–#35) using the configured local Ollama model (`qwen2.5:3b` via LangChain `ChatOllama` structured output).

## Extracted Categories
- **Technical Skills**: `Programming Language`, `AI & Machine Learning`, `Framework & Library`, `Tool & Platform`, `Database`, plus custom skills.
- **Educational Requirements**: `minimum_level`, `required_degree`, `preferred_degree`, `required_fields`, `required_certifications`, `preferred_certifications`.
- **Experience Requirements**: `minimum_years`, `maximum_years`, `professional_experience`, `internship_experience`, `project_experience`, `fresher_eligible`, `domain_experience`, `requirements`.
- **Soft Skills**, **Domain Knowledge**, **Other Requirements**.
- **Classification**: Every requirement carries `importance` (`Mandatory`, `Preferred`, `Optional`, `Unspecified`), `evidence`, `confidence`, and `source_type` (`explicit` | `inferred`).

## API Endpoints
- `POST /api/v1/job-descriptions/{job_description_id}/requirements-analysis?force_recalculate=false`
  - Auth via `X-User-Id` / `user_id` and ownership check.
  - Returns cached `JobRequirementAnalysis` when `content_hash` matches and `force_recalculate` is `false`.
  - Syncs `mandatory_skills`, `preferred_skills`, `education_required`, and `requirements` onto `job_descriptions`.
  - Maps Ollama connection/timeout failures to HTTP `503` and malformed AI outputs to HTTP `502`.
- `GET /api/v1/job-descriptions/{job_description_id}/requirements-analysis`
  - Returns persisted requirement analysis or HTTP `404` if not yet analyzed.

## Database
- Table `job_requirement_analyses` (Alembic revision `h4c5d6e7f8a9`), 1-to-1 with `job_descriptions` via unique `job_description_id` foreign key (`ON DELETE CASCADE`).
