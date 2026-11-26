# Feature 38: Job Description Report

## Overview

Phase 6, Feature #38 aggregates Features #33–#37 into a comprehensive, versioned Job Description Analysis Report.

## Report Sections

1. **Overview**: Title, company, location, employment type, work arrangement, seniority, experience summary, industry, summary.
2. **Role Analysis**: Standardized role, department, category, seniority, role summary, responsibilities, industry (from Feature #35).
3. **Technical Requirements**: Programming Languages, AI & Machine Learning, Frameworks & Libraries, Tools & Platforms, Databases, Cloud Technologies, Other Technical Skills (from Feature #36).
4. **Skill Classification**: Mandatory, Preferred, Optional, and Unspecified skills with priority scores, priority levels, expected proficiency, and evidence (from Feature #37).
5. **Education & Experience**: Required/preferred degrees, fields, certifications, min/max years, fresher/internship/project eligibility (from Feature #36).
6. **Soft Skills & Responsibilities**: Extracted soft skills and key responsibilities.
7. **Complexity Analysis**: AI-estimated complexity (`Beginner`, `Intermediate`, `Advanced`, `Expert`) with explanation and non-official disclaimer.
8. **Eligibility Criteria**: Evidence-based general role eligibility summary (non-candidate-specific).
9. **AI Job Insights**: Concise insights generated via a single `ChatOllama` call (`settings.OLLAMA_MODEL`).

## Prerequisite Enforcement & Versioning

- **Prerequisites**: Requires Feature #35, Feature #36, and Feature #37 to be completed. Missing prerequisites return `422 Unprocessable Entity` listing the exact missing feature(s).
- **Versioning**: Initial report is `1.0`; regenerating (`?regenerate=true`) increments `version_number` and `report_version` (`2.0`, `3.0`, etc.).

## Backend & Frontend

- **Model**: `JobDescriptionReport` (`job_description_reports`) in `backend/app/models/job_description_report.py`
- **Migration**: `backend/alembic/versions/2026_11_26_1930-j6e7f8a9b0c1_create_job_description_reports_table.py`
- **API Endpoints**:
  - `POST /api/v1/job-descriptions/{job_description_id}/report?regenerate=false`
  - `GET /api/v1/job-descriptions/{job_description_id}/report`
- **Frontend**: `frontend/src/pages/JobDescriptionReportPage.jsx` at `/jobs/report` and `/jobs/:jobId/report`.
