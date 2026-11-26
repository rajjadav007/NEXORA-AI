# Feature 37: Mandatory & Preferred Skills Classification

## Overview

Phase 6, Feature #37 adds evidence-based skill classification on top of Feature #36 (Job Requirement Extraction) and the original job description.

## Classification Tiers & Priority Rules

| Classification | Priority Score | Priority Level | Meaning |
| --- | --- | --- | --- |
| `Mandatory` | 80–100 | `High` | Explicitly required by the employer |
| `Preferred` | 40–79 | `Medium` | Improves candidate fit, not compulsory |
| `Optional` | 1–39 | `Low` | Explicitly optional or additional |
| `Unspecified` | `null` | `Low` | Mentioned without clear importance or ambiguous |

- **Proficiency Levels**: `Beginner`, `Intermediate`, `Advanced`, `Expert`, `Unspecified` (never invented when absent from text).
- **Normalization & Deduplication**: Uses the existing Feature #17 `skill_dictionary` and `normalize_skill_text` / `create_lookup_key` helpers, preserving `original_name` when an alias maps to a canonical skill. Conflicting statements resolve deterministically (`explicit` over `inferred`, `Mandatory > Preferred > Optional > Unspecified`).
- **Summary Validation**: `classification_summary` counts are always recomputed and validated against the `skills` array.

## Backend Architecture

- **Model**: `JobSkillClassification` (`job_skill_classifications` table) in `backend/app/models/job_skill_classification.py`
- **Migration**: `backend/alembic/versions/2026_11_26_1915-i5d6e7f8a9b0_create_job_skill_classifications_table.py`
- **Schemas**: `backend/app/schemas/job_skill_classification.py`
- **Service & AI Classifier**:
  - `backend/app/services/job_skill_classification/ai_classifier.py` (`SkillClassificationAIExtractor` using `ChatOllama` and `settings.OLLAMA_MODEL`)
  - `backend/app/services/job_skill_classification/service.py` (`JobSkillClassificationService`, reuses `job_requirement_extraction_service` and caches by `content_hash`)
- **API Endpoints**:
  - `POST /api/v1/job-descriptions/{job_description_id}/skills-classification?force_recalculate=false`
  - `GET /api/v1/job-descriptions/{job_description_id}/skills-classification`

## Frontend

- **Service**: `classifyJobSkills` and `getJobSkillsClassification` in `frontend/src/services/jobDescriptionService.js`
- **Dashboard Component**: `frontend/src/components/jobs/SkillClassificationSection.jsx`
- **Page Integration**: `frontend/src/pages/JobsPage.jsx`
