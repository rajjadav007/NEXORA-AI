# Phase 5: Resume Intelligence Report

Phase 5 delivers visual analytics, reporting, and export capabilities based on Phase 3 and Phase 4 intelligence data.

## Features Overview

| Feature ID | Feature Name | Description | Status |
|---|---|---|---|
| Feature #28 | Resume Analytics Dashboard | Aggregated visual metrics, summary cards, scoring distribution, and synthesized insights | **Completed** |
| Feature #29 | Skill Distribution | Visualizing extracted skills and category weighting | **Completed** |
| Feature #30 | Resume Improvement Tracker | Tracking version-over-version score improvement, tasks, and history | **Completed** |
| Feature #31 | AI Resume Report | Comprehensive text report generation | **Completed** |
| Feature #32 | PDF Report Export | Client- and server-side PDF document generation | Planned |

## Feature #28: Resume Analytics Dashboard Architecture

### 1. Data Aggregation & Reusability
- Queries existing database tables directly (`resumes`, `resume_quality_scores`, `resume_strength_analyses`, `resume_weakness_analyses`, `resume_ats_analyses`, `resume_grammar_analyses`, `resume_achievement_analyses`, `resume_recommendation_analyses`).
- Does NOT execute duplicate Ollama LLM requests when data is already persisted.
- Displays genuine analysis values; unanalyzed sections clearly indicate `"Not Evaluated"` rather than inventing synthetic metrics.

### 2. API Endpoints
- `GET /api/v1/resumes/{resume_id}/analytics/dashboard`
- Alias: `GET /api/resumes/{resume_id}/analytics/dashboard`
- Short alias: `GET /api/v1/resumes/{resume_id}/analytics`

### 3. Frontend Dashboard (`ResumeAnalyticsDashboard.jsx`)
- Header with file details, last analyzed timestamp, coverage badge, and multi-resume selector dropdown.
- 4 Summary Cards: Overall Quality Score, ATS Compatibility Score, Readability Score, Content Completeness Score.
- Visual Analytics:
  - 8-Category Quality Performance Bars.
  - Multi-feature score comparison distribution.
  - Strengths vs Weaknesses ratio meter & category breakdown.
- Synthesized Insights:
  - Key strengths with evidence quotes.
  - Important weaknesses with recommended improvements.
  - Prioritized actionable improvement steps.
  - Quick module summary cards.
- States:
  - Loading skeleton with pulse animations.
  - Empty dashboard state with call-to-action when analyses are pending.
  - Error state with retry handler.

---

## Feature #29: Skill Distribution Architecture

### 1. 8 Canonical Skill Domains
Skills extracted from resumes are categorized deterministically into:
1. `Programming Languages`
2. `AI and Machine Learning`
3. `Data Science and Analytics`
4. `Frameworks and Libraries`
5. `Databases`
6. `Cloud and DevOps`
7. `Development Tools`
8. `Other Skills`

### 2. API Endpoints
- `GET /api/v1/resumes/{resume_id}/analytics/skills`
- Alias: `GET /api/resumes/{resume_id}/analytics/skills`

### 3. Data Processing & Safeguards
- Reuses existing `resume_skills` records without executing redundant LLM calls.
- Enforces user authentication and resume ownership (`verify_resume_access`).
- Preserves original casing and canonical skill names.
- Deduplicates skills across and within categories case-insensitively.
- Omits unpopulated categories from the primary output array to reflect genuine resume contents.
- Computes summary metrics: `total_skills`, `total_categories`, `most_populated_category`, and `uncategorized_skills`.

### 4. Frontend Component (`SkillDistributionSection.jsx`)
- **Summary Metrics**: Total skills, active categories, top category with count and percentage share, and uncategorized skills.
- **Interactive Visual Charts**:
  - Pure SVG Donut Chart with slice hovering, stroke animation, center total and category readout, and color-coded legend.
  - Horizontal Bar Chart for category proportion comparison.
  - View switcher: Both Views / Donut / Bar.
- **Search & Filtering**:
  - Real-time text search filtering across skill names.
  - Category filter pills with count indicators.
  - Expand All / Collapse All controls.
  - Friendly empty state for queries with no matching skills.
- **Category Cards**:
  - Individual cards for each populated domain with domain icons, count badges, and expandable pill tags.
- Integrated seamlessly into `ResumeAnalyticsDashboard.jsx`.

---

## Feature #30: Resume Improvement Tracker Architecture

### 1. Overview & Data Model
Tracks quality changes, recommendation progress, and version-over-version evolution:
- **Snapshots (`resume_analysis_snapshots`)**: Stores historical scores (overall quality, ATS, readability, category scores, strengths/weaknesses counts) associated with resume versions. Never overwritten on subsequent analyses.
- **Tasks (`resume_improvement_tasks`)**: Actionable improvement tasks created from Phase 4 recommendations, with section categorization, priority (`High`, `Medium`, `Low`), and status (`Pending`, `In Progress`, `Completed`). Completion timestamps and status changes are persisted in PostgreSQL.
- **Timeline (`resume_timeline_events`)**: Chronological audit trail of milestone events (`RESUME_UPLOADED`, `RESUME_ANALYZED`, `TASK_CREATED`, `TASK_COMPLETED`, `TASK_REOPENED`, `VERSION_UPLOADED`, `VERSION_ANALYZED`) using real timestamps.

### 2. API Endpoints
- `GET /api/v1/resumes/{resume_id}/improvements` (and alias `GET /api/resumes/{resume_id}/improvements`): Complete tracker overview.
- `GET /api/v1/resumes/{resume_id}/improvements/history` (and alias `GET /api/resumes/{resume_id}/improvements/history`): Chronological snapshot history.
- `GET /api/v1/resumes/{resume_id}/improvements/tasks` (and alias `GET /api/resumes/{resume_id}/improvements/tasks`): Filterable tasks with progress metrics.
- `PATCH /api/v1/resumes/{resume_id}/improvements/tasks/{task_id}` (and alias `PATCH /api/resumes/{resume_id}/improvements/tasks/{task_id}`): Update task status and priority.
- `GET /api/v1/resumes/{resume_id}/improvements/compare` (and alias `GET /api/resumes/{resume_id}/improvements/compare`): Side-by-side version comparison.

### 3. Progress Formula
$$\text{Task Completion Percentage} = \left(\frac{\text{Completed Tasks}}{\text{Total Tasks}}\right) \times 100$$
Task progress is clearly distinguished from score improvements (score deltas).

### 4. Version Comparison
- Metadata: Version numbers, upload timestamps, analysis timestamps.
- Text statistics: Word count differences, character differences, line count differences.
- Skills detected: Added skills, removed skills, retained skills.
- Score deltas: Quality, ATS, and readability score comparisons.
- Factual text change summary (avoids claiming quality improvements based only on score differences).

### 5. Frontend Components
- `ResumeImprovementTracker.jsx`: Embedded in `ResumeAnalyticsDashboard.jsx`.
- `ResumeImprovementsPage.jsx`: Dedicated route `/resume/improvements` and `/resume/:resumeId/improvements`.
- `improvementService.js`: Frontend API client methods.

---

## Feature #31: AI Resume Report Architecture

### 1. Overview & Data Model
Provides an AI-powered, multi-dimensional assessment of candidate resumes, synthesizing Phase 3 (intelligence), Phase 4 (quality scores, strengths, weaknesses, ATS, grammar, recommendations), and Phase 5 evaluations.

- **Reports Table (`resume_reports`)**:
  - `id`: UUID Primary Key
  - `resume_id`: UUID Foreign Key (`resumes.id`, `CASCADE`)
  - `user_id`: UUID Foreign Key (`users.id`, `SET NULL`)
  - `model_name`: Configured local LLM model (e.g. `gemma4:12b`)
  - `status`: `COMPLETED` / `FAILED`
  - `report_data`: Complete 11-section structured JSON payload
  - `executive_summary`: Narrative executive summary text
  - `generation_duration_seconds`: Execution duration in seconds
  - `created_at` / `updated_at`: Real timestamps

### 2. Report Sections Structure
1. **Executive Summary**: Overall profile assessment, primary strengths, key weaknesses, general improvement direction.
2. **Resume Quality Assessment**: Overall quality score, ATS compatibility, readability, content completeness with clear explanations.
3. **Skills Assessment**: Technical skills, AI/ML skills, programming languages, frameworks and tools, distribution observations.
4. **Experience Assessment**: Responsibilities, achievements, quantifiable impact, professional presentation.
5. **Education Assessment**: Degrees reviewed, academic presentation, relevant certifications.
6. **Projects Assessment**: Technical depth, problem clarity, implementation rigor, outcomes.
7. **Resume Strengths**: Evidence-backed, prioritized list of genuine strengths.
8. **Weakness Analysis**: Evidence-grounded issues with severity levels and recommendations.
9. **ATS Assessment**: Available ATS score, parser safety summary, formatting flags, section completeness.
10. **Improvement Recommendations**: Prioritized recommendations (High, Medium, Low) with suggested next actions.
11. **Final Strategic Assessment**: Overall conclusion, top five immediate actions, strategic priorities.

### 3. AI Safety & Local Model Integration
- **Local Ollama Integration**: Powered by local `gemma4:12b` via LangChain `ChatOllama`.
- **Zero Paid APIs**: Operates locally without external cloud dependencies.
- **Prompt Injection Defense**: Treats candidate resume text strictly as untrusted data input, preventing instruction hijacking.
- **Factual Integrity**: Never hallucinates credentials, projects, or metrics not present in database records.
- **Graceful Error Recovery**: Translates Ollama connection/timeout failures into `503 Service Unavailable`, with deterministic synthesis fallback.

### 4. API Endpoints
- `POST /api/v1/resumes/{resume_id}/reports/generate` (and alias `POST /api/resumes/{resume_id}/reports/generate`): Generates or retrieves report.
- `GET /api/v1/resumes/{resume_id}/reports` (and alias `GET /api/resumes/{resume_id}/reports`): Chronological report history.
- `GET /api/v1/resumes/{resume_id}/reports/latest` (and alias `GET /api/resumes/{resume_id}/reports/latest`): Latest report.
- `GET /api/v1/resumes/{resume_id}/reports/{report_id}` (and alias `GET /api/resumes/{resume_id}/reports/{report_id}`): Specific report by ID.

### 5. Frontend Components
- `ResumeReportView.jsx`: Responsive multi-card report presentation component.
- `ResumeReportPage.jsx`: Dedicated route `/resume/report` and `/resume/:resumeId/report`.
- `reportService.js`: API service methods with comprehensive error handling.



