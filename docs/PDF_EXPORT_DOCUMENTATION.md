# Nexora AI - PDF Report Export Documentation
**Phase 5 | Feature #32: PDF Report Export**

## 1. Overview
The PDF Report Export engine enables authenticated users to export their generated AI Resume Reports (Feature #31) as publication-grade, downloadable PDF documents. The document faithfully represents saved evaluations across Phase 3, Phase 4, and Phase 5 intelligence without modifying or regenerating report data.

---

## 2. Technical Architecture

- **Library**: ReportLab (`reportlab>=5.1.0`)
- **Canvas Implementation**: Two-pass `NumberedCanvas` (`reportlab.pdfgen.canvas.Canvas`)
  - Pass 1: Renders content flowables and tracks page states.
  - Pass 2: Computes total page count and draws running headers on pages 2+ and dynamic footers (`Page X of Y`) on all pages.
- **Page Layout**: International A4 (595.27 x 841.89 pt) with 40 pt margins (515.27 pt printable width).
- **Security & XML Escaping**: All user, file, and metric text is escaped through `xml.sax.saxutils.escape` to ensure safe XML parsing and prevent injection or layout syntax crashes.
- **Caching & Non-Regeneration**: The PDF generation engine reads directly from PostgreSQL `ResumeReport.report_data` and never invokes Ollama or updates database models.

---

## 3. PDF Page Structure (6-Page Standard)

| Page # | Page Title | Key Content & Components |
|---|---|---|
| **Page 1** | **Cover and Executive Overview** | Nexora AI branding, Resume filename, Generation date, Report ID, Overall Quality Score badge (`score/100`), Executive summary narrative, Key strengths vs. Attention areas 2-column table, Strategic direction box. |
| **Page 2** | **Resume Quality Assessment** | 4-Metric Score Card Grid (Overall Quality, ATS Compatibility, Readability, Content Completeness), Metric definitions table, Evaluator narrative assessment. |
| **Page 3** | **Skills Assessment & Distribution** | Categorized competencies table (Languages, AI/ML, Frameworks, Core Skills), Skill distribution observations narrative, Feature #29 8-category breakdown table. |
| **Page 4** | **Strengths & Weaknesses Analysis** | Genuine strengths table (Title, Section, Evidence, Impact), Identified weaknesses table (Issue, Section, Severity, Actionable Remedy). |
| **Page 5** | **Experience, Projects & Academic Evaluation** | Professional experience review table (Roles count, Metrics density, Responsibilities, Presentation), Project intelligence table (Projects count, Tech stack, Problems, Outcomes), Education & credentials table (Degrees, Presentation, Certifications). |
| **Page 6** | **ATS Assessment & Recommendations** | ATS score card & keyword coverage, Prioritized recommendations table (High, Medium, Low badges with actionable steps), Top 5 immediate strategic actions list, Final takeaway conclusion. |

---

## 4. API Specification

### Endpoint: Export Report as PDF
- **Path**: `GET /api/resumes/{resume_id}/reports/{report_id}/pdf`
- **Aliases**:
  - `GET /api/v1/resumes/{resume_id}/reports/{report_id}/pdf`
  - `GET /resumes/{resume_id}/reports/{report_id}/pdf`
- **Method**: `GET`
- **Access**: Owner Only (`verify_resume_access` enforcement)
- **Parameters**:
  - `resume_id` (Path, UUID): Unique resume identifier.
  - `report_id` (Path, UUID): Unique report identifier.
  - `X-User-Id` (Header, Optional): Authenticated user UUID.
- **Response Headers**:
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="Nexora_AI_Resume_Report_{filename}_{report_id[:8]}.pdf"`
  - `Content-Length: <byte_size>`
  - `Cache-Control: no-cache, no-store, must-revalidate`
- **Response Body**: Binary PDF stream.

---

## 5. Frontend Integration

- **Service**: `frontend/src/services/reportService.js` (`exportResumeReportPdf(resumeId, reportId)`)
- **Component**: `frontend/src/components/resume/ResumeReportView.jsx`
- **Features**:
  - Prominent "Download PDF" button in the header action bar alongside Regenerate Report.
  - Animated bouncing download icon during generation state.
  - Instant success feedback banner with filename and "Download Again" option.
  - Error alert with retry capability.
  - Can export any historical report selected from the history dropdown.

---

## 6. Verification & Quality Gates

- **Unit & Integration Tests**:
  - Backend (`backend/tests/test_pdf_report_export_api.py`): 5 / 5 passed (100%).
  - Frontend (`frontend/tests/reportService.test.mjs`): 10 / 10 passed (100%).
  - Full Phase 5 backend suite: 26 / 26 passed (100%).
  - Full frontend suite: 131 / 131 passed (100%).
  - Production build: `vite build` completed in 20.08s with 0 errors.
