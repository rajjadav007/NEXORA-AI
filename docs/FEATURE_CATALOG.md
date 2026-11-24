# Nexora AI - Feature Catalog

This document tracks implemented features across stages and phases of Nexora AI.

## Stage 1: Resume Processing Engine

### Phase 1: Foundation & Infrastructure (Features 1–4)
- Feature #1: User Management & Authentication (Completed)
- Feature #2: Database Schema & Migrations (Completed)
- Feature #3: File Upload Validation & Storage (Completed)
- Feature #4: System Health & Observability (Completed)

### Phase 2: Resume Extraction & Cleaning (Features 5–10)
- Feature #5: Resume Text Extraction (Completed)
- Feature #6: Resume Permanent Storage & Versioning (Completed)
- Feature #7: Text Normalization & Cleaning (Completed)
- Feature #8: Format Conversion & Parsing (Completed)
- Feature #9: Section Identification & Segmentation (Completed)
- Feature #10: Contact Information Extraction (Completed)

### Phase 3: Resume Intelligence (Features 11–20)
- Feature #11: Work Experience Extraction (Completed)
- Feature #12: Education Details Extraction (Completed)
- Feature #13: Skills Extraction & Standardization (Completed)
- Feature #14: Project Extraction & Evaluation (Completed)
- Feature #15: Certifications & Licenses Extraction (Completed)
- Feature #16: Publications & Research Extraction (Completed)
- Feature #17: Skill Normalization Engine (Completed)
- Feature #18: Project Intelligence Engine (Completed)
- Feature #19: Certifications & Achievements Engine (Completed)
- Feature #20: Career Progression Analysis (Completed)

### Phase 4: Resume Quality Analysis (Features 21–27)
- Feature #21: Resume Quality Score Engine (Completed)
- Feature #22: Resume Strength Analysis (Completed)
- Feature #23: Resume Weakness Analysis (Completed)
- Feature #24: ATS Compatibility Analysis (Completed)
- Feature #25: Grammar & Clarity Analysis (Completed)
- Feature #26: Achievement & Impact Analysis (Completed)
- Feature #27: Resume Improvement Recommendation Engine (Completed)

### Phase 5: Resume Intelligence Report (Features 28–32)
- **Feature #28: Resume Analytics Dashboard (Completed)**
  - Aggregates existing Phase 4 analyses without redundant AI calls or fake data.
  - Summary metrics: Overall Quality, ATS Compatibility, Readability, Content Completeness.
  - Visual Analytics: Quality category breakdown, cross-analysis distribution, strengths vs weaknesses ratio.
  - Synthesized insights: Key strengths, weaknesses, priority improvement actions, feature summaries.
  - Multi-resume switcher and responsive desktop/tablet/mobile design.
- **Feature #29: Skill Distribution (Completed)**
  - Organizes and categorizes extracted skills into 8 canonical technical domains: Programming Languages, AI and Machine Learning, Data Science and Analytics, Frameworks and Libraries, Databases, Cloud and DevOps, Development Tools, and Other Skills.
  - Endpoint `GET /api/resumes/{resume_id}/analytics/skills` (and `/api/v1/...`) with full auth guard, deterministic classification, deduplication, and aggregate summaries.
  - Interactive SVG Donut chart, Category Comparison Bar chart, real-time search filtering, category pills, and collapsible category cards.
  - Seamlessly integrated into Feature #28 Resume Analytics Dashboard.
- **Feature #30: Resume Improvement Tracker (Completed)**
  - Stores and retrieves chronological resume analysis snapshots without overwriting historical evaluations.
  - Compares version-over-version scores (Overall Quality, ATS Compatibility, Readability, and category breakdowns) with explicit improvement, decline, or unchanged indicators.
  - Actionable improvement task management with priority indicators (High, Medium, Low), status tracking (Pending, In Progress, Completed), real-time status updates, filtering, and completion dates persisted in PostgreSQL.
  - Progress metrics calculating overall task completion percentage `(Completed Tasks / Total Tasks) × 100`, clearly distinguishing task progress from actual score changes.
  - Chronological improvement timeline tracking key milestones (resume uploaded, analyzed, tasks created, tasks completed, new versions analyzed) with real timestamps.
  - Side-by-side resume version comparison detailing upload/analysis dates, textual changes (words/lines/characters), added/removed/retained skills, and score deltas.
  - REST endpoints under `/api/resumes/{resume_id}/improvements` (overview, history, tasks, patch task status, compare versions) with authenticated user & resume ownership enforcement.
  - Responsive frontend tracker integrated into the Resume Analytics Dashboard and available via dedicated route `/resume/improvements`.
- **Feature #31: AI Resume Report (Completed)**
  - Local Ollama-powered comprehensive evaluation system generating structured, 11-section personalized assessments.
  - Sections covered: Executive Summary, Resume Quality Assessment, Skills Assessment (8 domains), Experience Assessment, Education Assessment, Projects Assessment, Prioritized Strengths, Weakness Analysis, ATS Assessment, Improvement Recommendations, and Final Assessment.
  - Reuses existing Phase 3 (intelligence), Phase 4 (quality scores, strengths, weaknesses, ATS, grammar, recommendations), and Phase 5 evaluations without redundant AI calls or document re-parsing.
  - Robust local Ollama integration using Gemma 4 12B with connection timeout handling, graceful 503 error responses, and deterministic baseline fallback.
  - Persisted in PostgreSQL `resume_reports` table preserving historical reports, model metadata, and generation runtimes.
  - REST endpoints under `/api/resumes/{resume_id}/reports` (generate, history, latest, get by id) with authenticated user & resume ownership enforcement.
  - Clean, responsive React frontend report interface with executive summary cards, detailed section breakdowns, report history picker, and regeneration capabilities.
- Feature #32: PDF Report Export (Pending)
