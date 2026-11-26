# Feature #35: Job Role Extraction

## Overview
Extracts structured role intelligence from saved job descriptions (Features #33 and #34) using the configured local Ollama model (`qwen2.5:3b` via LangChain `ChatOllama` structured output).

## Extracted Fields
- `job_title`, `standardized_role` (canonical taxonomy + custom role support), `department`, `category`
- `seniority` (`Internship`, `Entry Level`, `Fresher`, `Junior`, `Mid-Level`, `Senior`, `Lead`, `Manager`, `Director`, `Unknown`)
- `experience_level` (`minimum_years`, `maximum_years`, `description`)
- `employment_type`, `work_arrangement` (`Remote`, `Hybrid`, `On-site`, `Unknown`), `industry`
- `responsibilities`, `role_summary`, `confidence_score`
- Provenance metadata: `explicit_facts`, `inferred_fields`, `model_used`, `cached`

## API Endpoints
- `POST /api/v1/job-descriptions/{job_description_id}/role-analysis?force_recalculate=false`
  - Authenticates via `X-User-Id` / `user_id` and verifies ownership.
  - Returns cached `JobRoleAnalysis` when `content_hash` matches and `force_recalculate` is `false`.
  - Maps Ollama connection/timeout failures to HTTP `503` and malformed AI outputs to HTTP `502`.
- `GET /api/v1/job-descriptions/{job_description_id}/role-analysis`
  - Returns persisted role analysis or HTTP `404` if not yet analyzed.

## Database
- Table `job_role_analyses` (Alembic revision `g3b4c5d6e7f8`), 1-to-1 with `job_descriptions` via unique `job_description_id` foreign key (`ON DELETE CASCADE`).
- Updates `job_descriptions.analysis_status` (`COMPLETED` / `FAILED`).
