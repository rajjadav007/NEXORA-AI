# DATA_FLOW.md

# Nexora AI: Data Flow Architecture

## 1. Purpose

This document explains how data moves through Nexora AI, from user input to processing, AI analysis, database storage, and final results.

It defines:

- Frontend-to-backend communication.
- Backend-to-database communication.
- Resume processing flow.
- Job description processing flow.
- Resume-to-job matching flow.
- Skill gap analysis flow.
- Career roadmap generation flow.
- AI Copilot flow.
- Embedding and retrieval flow.
- Data validation and security.
- Error handling and background processing.

The goal is to maintain a clear, modular, and reliable data flow across the application.

---

## 2. System Components

Nexora AI uses five main data-processing layers.

| Layer | Technology | Responsibility |
|---|---|---|
| Presentation | React + JavaScript | Collect user input and display results |
| API | FastAPI | Validate requests and coordinate services |
| AI Engine | Ollama, LangChain, LangGraph | Process and generate AI outputs |
| Data | PostgreSQL + pgvector | Store application data and embeddings |
| File Storage | Local storage initially | Store uploaded resumes and documents |

### High-Level Data Flow

```text
                 USER
                  |
                  v
           REACT FRONTEND
                  |
                  v
             FASTAPI
                  |
          +-------+-------+
          |       |       |
          v       v       v
       SERVICES  AI     DATABASE
          |     ENGINE      |
          |       |         |
          |    OLLAMA       |
          |       |         |
          |   EMBEDDINGS    |
          |       |         |
          +-------+---------+
                  |
                  v
           PROCESSED DATA
                  |
                  v
            POSTGRESQL
                  |
                  v
           FASTAPI RESPONSE
                  |
                  v
           REACT FRONTEND
                  |
                  v
               USER
```

---

## 3. General Request Lifecycle

Every normal application request should follow a consistent lifecycle.

### Request Flow

```text
User Action
    |
    v
React Component
    |
    v
Frontend API Service
    |
    v
FastAPI Endpoint
    |
    v
Authentication Check
    |
    v
Request Validation
    |
    v
Business Service
    |
    +--------------------+
    |                    |
    v                    v
Database             AI Service
    |                    |
    +---------+----------+
              |
              v
       Result Validation
              |
              v
       Database Update
              |
              v
       API Response
              |
              v
       React UI Update
```

### Processing Responsibilities

| Component | Responsibility |
|---|---|
| React | Collect and display data |
| API Service | Send HTTP requests |
| FastAPI | Handle API requests |
| Authentication | Identify the current user |
| Validation | Check incoming data |
| Business Service | Execute application logic |
| AI Service | Run AI-related tasks |
| Database | Store and retrieve records |
| Response Layer | Return consistent results |

The frontend should never communicate directly with PostgreSQL or Ollama.

---

## 4. User Registration and Authentication Data Flow

**Related features:** 85–88

### Registration Flow

```text
User Registration Form
        |
        v
React Frontend
        |
        v
POST /api/v1/auth/register
        |
        v
FastAPI Validation
        |
        v
Password Hashing
        |
        v
Create User Record
        |
        v
PostgreSQL
        |
        v
Registration Response
        |
        v
React Frontend
```

### Login Flow

```text
Login Form
    |
    v
POST /api/v1/auth/login
    |
    v
Validate Credentials
    |
    v
Verify Password Hash
    |
    v
Create Authenticated Session
    |
    v
Return Secure Authentication Response
    |
    v
Frontend Auth State
```

### Data Storage

| Table | Data |
|---|---|
| users | Account information |
| user_profiles | Career and personal profile |
| password_reset_tokens | Password recovery information |

### Security Rules

- Store password hashes, never plain-text passwords.
- Use secure authentication mechanisms.
- Verify user identity on protected endpoints.
- Apply user-level data access restrictions.
- Never expose authentication secrets to the frontend.

The final authentication approach, such as secure cookie sessions or JWT, must be selected before implementation.

---

## 5. Resume Upload Data Flow

**Related features:** 7–12

This is the first major data-processing workflow.

### Complete Flow

```text
User Selects Resume
        |
        v
React File Upload
        |
        v
POST /api/v1/resumes
        |
        v
FastAPI File Validation
        |
        v
Check File Type and Size
        |
        v
Store Original File
        |
        v
Create Resume Record
        |
        v
Extract Resume Text
        |
        v
Clean Extracted Text
        |
        v
Save Extracted Content
        |
        v
Return Resume Preview
        |
        v
React Displays Preview
```

### Input Data

- Resume file.
- File name.
- File format.
- User ID from authenticated context.

### Processing

| Step | Component | Operation |
|---|---|---|
| 1 | React | Select file |
| 2 | FastAPI | Receive upload |
| 3 | Validation Service | Check format and size |
| 4 | File Storage | Store original document |
| 5 | PDF/DOCX Processor | Extract text |
| 6 | Text Cleaner | Normalize extracted content |
| 7 | Database Service | Store metadata and extracted content |
| 8 | React | Display preview |

### Output

- Resume ID.
- File information.
- Processing status.
- Extracted text preview.

### Important Rules

- Accept only supported file formats.
- Validate file contents, not just the extension.
- Generate unique server-side storage names.
- Keep original filenames as metadata.
- Store files outside public web directories.
- Restrict access to the resume owner.
- Handle scanned PDFs separately because OCR may be required.

---

## 6. Resume Intelligence Data Flow

**Related features:** 13–20

After the user confirms the resume preview, the system starts structured resume analysis.

### Complete Flow

```text
Confirmed Resume
       |
       v
Load Extracted Text
       |
       v
Section Detection
       |
       v
LLM + NLP Processing
       |
       v
Extract Structured Information
       |
       +----------------------+
       |          |           |
       v          v           v
   Education  Experience    Skills
       |          |           |
       +----------+-----------+
                  |
                  v
            Projects
                  |
                  v
            Certifications
                  |
                  v
          Pydantic Validation
                  |
                  v
          Skill Normalization
                  |
                  v
          Save Structured Data
                  |
                  v
          Resume Intelligence
```

### Extracted Information

| Category | Extracted Data |
|---|---|
| Personal | Name, email, phone, links |
| Education | Degree, institution, dates |
| Experience | Role, company, duration |
| Skills | Technical and soft skills |
| Projects | Name, description, technologies |
| Certifications | Name, issuer, date |
| Structure | Resume sections and organization |

### AI Responsibilities

- Ollama: Understand resume content.
- LangChain: Manage prompts and structured model interaction.
- spaCy: Support NLP processing.
- Python: Validate and normalize information.
- Pydantic: Validate structured output.

### Storage

Store extracted information in the relevant PostgreSQL tables.

Do not store every extracted field only as a large JSON object if it needs to be searched, filtered, or analyzed independently.

---

## 7. Resume Quality Analysis Data Flow

**Related features:** 21–27

### Flow

```text
Structured Resume Data
          |
          v
Resume Analysis Service
          |
          +----------------------+
          |          |           |
          v          v           v
      Structure   Content     Achievement
       Checks     Analysis     Analysis
          |          |           |
          +----------+-----------+
                     |
                     v
              Scoring Engine
                     |
                     v
             LLM Recommendations
                     |
                     v
              Result Validation
                     |
                     v
             Save Analysis Report
                     |
                     v
              Display Dashboard
```

### Analysis Categories

- Resume quality score.
- Strengths.
- Weaknesses.
- ATS compatibility.
- Grammar and clarity.
- Achievement quality.
- Improvement recommendations.

### Scoring Responsibilities

Python should calculate rule-based scores.

The LLM should provide language-based explanations and suggestions.

This separation helps maintain consistent scoring.

---

## 8. Resume Report Data Flow

**Related features:** 28–32

### Flow

```text
Resume Analysis Results
          |
          v
Analytics Service
          |
          +------------------+
          |                  |
          v                  v
    Skill Distribution   Score History
          |                  |
          +--------+---------+
                   |
                   v
            Report Generator
                   |
                   v
             PDF Export
                   |
                   v
            User Downloads
```

### Data Used

- Resume scores.
- Skill categories.
- Strengths.
- Weaknesses.
- Improvement recommendations.
- Previous analysis records.

The dashboard should retrieve stored analysis results instead of running the entire AI pipeline every time the user opens the page.

---

## 9. Job Description Analyzer Data Flow

**Related features:** 33–38

### Input Methods

1. User pastes a job description.
2. User submits a job description URL.

### Flow

```text
Job Description Input
          |
          v
FastAPI Endpoint
          |
          v
Input Validation
          |
          v
Text Extraction
          |
          v
LLM Requirement Extraction
          |
          v
Skill Normalization
          |
          v
Validate Requirements
          |
          v
Store Job Description
          |
          v
Generate Analysis Report
          |
          v
Display Results
```

### Extracted Information

- Job title.
- Company name.
- Required skills.
- Preferred skills.
- Experience requirements.
- Education requirements.
- Job responsibilities.

### URL Import Rules

- Validate submitted URLs.
- Restrict requests to safe public destinations.
- Block private network and local addresses.
- Handle redirects safely.
- Apply request timeouts and response size limits.
- Respect website access rules.
- Do not bypass authentication or access controls.

If a page cannot be accessed, allow the user to paste the job description manually.

---

## 10. Employer Intelligence Data Flow

**Related features:** 39–45

### Flow

```text
Company Search
      |
      v
Company Research Service
      |
      v
Retrieve Public Sources
      |
      v
Extract Company Information
      |
      v
Identify Hiring Requirements
      |
      v
Analyze Skill Demand
      |
      v
Identify Fresher Opportunities
      |
      v
Validate and Store Sources
      |
      v
Generate Employer Report
      |
      v
Display Results
```

### Data Sources

Possible sources include:

- Official company websites.
- Official career pages.
- Public job listings.
- Public company documentation.

### Data Storage

Store:

- Company information.
- Source URLs.
- Retrieved content metadata.
- Retrieval timestamps.
- Extracted requirements.
- Employer analysis reports.

Clearly distinguish source-backed facts from AI-generated conclusions.

---

## 11. Job Discovery Data Flow

**Related features:** 46–51

### Flow

```text
User Search
     |
     v
Search Filters
     |
     v
Job Discovery Service
     |
     v
Job Data Sources
     |
     v
Normalize Job Records
     |
     v
Apply Filters
     |
     v
Return Job Results
     |
     v
Display Job Cards
     |
     v
User Saves Job
     |
     v
PostgreSQL
```

### Search Filters

- Job title.
- Role.
- Location.
- Experience.
- Employment type.
- Skills.

### Job Storage

Store relevant job information and source metadata.

Avoid creating duplicate job records when the same listing is discovered multiple times.

Use source identifiers and normalized URLs where available.

---

## 12. Resume-to-Job Matching Data Flow

**Related features:** 52–57

This workflow connects resume intelligence with employer requirements.

### Complete Flow

```text
              Resume Data
                   |
                   v
             Load Resume
                   |
                   |
              Job Data
                   |
                   v
              Load Job
                   |
                   v
            Normalize Skills
                   |
                   v
        +----------+----------+
        |          |          |
        v          v          v
     Required  Preferred  Semantic
      Skills    Skills    Matching
        |          |          |
        +----------+----------+
                   |
                   v
           Experience Check
                   |
                   v
            Education Check
                   |
                   v
           Project Relevance
                   |
                   v
            Scoring Engine
                   |
                   v
             Match Score
                   |
                   v
           LLM Explanation
                   |
                   v
            Save Match Data
                   |
                   v
            Display Results
```

### Input Data

From resume:

- Skills.
- Experience.
- Education.
- Projects.
- Certifications.

From job:

- Required skills.
- Preferred skills.
- Experience requirements.
- Education requirements.
- Responsibilities.

### Matching Techniques

| Technique | Purpose |
|---|---|
| Exact Matching | Identify identical skills |
| Alias Matching | Match known skill variations |
| Fuzzy Matching | Handle minor text differences |
| Semantic Matching | Identify related concepts |
| Rule-Based Scoring | Calculate match components |
| LLM Explanation | Explain the result |

### Output

- Overall match score.
- Matching skills.
- Missing skills.
- Experience comparison.
- Education comparison.
- Project relevance.
- Match explanation.

The match score should be calculated by Python, not invented by the LLM.

---

## 13. Skill Gap Intelligence Data Flow

**Related features:** 58–62

### Flow

```text
Resume Skills
      |
      v
Normalize Skills
      |
      |
Job Requirements
      |
      v
Normalize Requirements
      |
      v
Compare Skill Sets
      |
      +----------------------+
      |          |           |
      v          v           v
   Matched    Missing    Transferable
   Skills     Skills      Skills
      |          |           |
      +----------+-----------+
                 |
                 v
          Priority Analysis
                 |
                 v
          Skill Gap Report
                 |
                 v
          Save Gap Results
                 |
                 v
          Display Dashboard
```

### Priority Factors

- Required or preferred status.
- Importance to the target role.
- Existing related skills.
- Skill assessment evidence.
- Relevance to the user's career goal.

The priority algorithm should be deterministic and explainable.

---

## 14. Career Readiness Data Flow

**Related features:** 63–66

### Flow

```text
Selected Career Goal
          |
          v
Load Role Requirements
          |
          v
Load User Skills
          |
          v
Load Experience and Projects
          |
          v
Load Assessment Evidence
          |
          v
Readiness Scoring Engine
          |
          v
Calculate Readiness
          |
          v
Save Readiness Snapshot
          |
          v
Display Progress
```

### Readiness Factors

- Skill coverage.
- Experience relevance.
- Project relevance.
- Education requirements.
- Assessment evidence.

The score should reflect the selected target role and the data available at calculation time.

Store historical snapshots so progress can be compared consistently.

---

## 15. Personalized Career Roadmap Data Flow

**Related features:** 67–72

### Flow

```text
User Career Goal
        |
        v
Load Career Profile
        |
        v
Load Skill Gap Results
        |
        v
Identify Priority Skills
        |
        v
Retrieve Learning Resources
        |
        v
Recommend Practical Projects
        |
        v
LLM Roadmap Generation
        |
        v
Validate Roadmap
        |
        v
Save Roadmap
        |
        v
Display Roadmap
        |
        v
Track User Progress
```

### AI Responsibilities

- Python: Prioritize skills.
- Embeddings: Retrieve related resources.
- Ollama: Generate structured recommendations.
- LangGraph: Coordinate dependent steps.
- PostgreSQL: Store roadmap and progress.

### Output

- Career goal.
- Learning stages.
- Priority skills.
- Recommended resources.
- Project suggestions.
- Progress status.

Recommendations should include relevant sources whenever external learning resources are suggested.

---

## 16. Skill Assessment Data Flow

**Related features:** 73–77

### Flow

```text
User Selects Skill
        |
        v
Assessment Configuration
        |
        v
LLM Question Generation
        |
        v
Validate Questions
        |
        v
Display Assessment
        |
        v
User Submits Answers
        |
        v
Evaluation Service
        |
        +---------------------+
        |                     |
        v                     v
    Rule-Based            LLM-Based
    Evaluation            Feedback
        |                     |
        +----------+----------+
                   |
                   v
             Calculate Score
                   |
                   v
              Save Attempt
                   |
                   v
          Update Skill Evidence
                   |
                   v
           Display Feedback
```

### Important Rules

- Save assessment attempts.
- Validate generated questions.
- Keep evaluation criteria consistent.
- Do not treat an AI-generated score as verified professional certification.
- Use isolated execution for practical coding challenges.

---

## 17. AI Career Copilot Data Flow

**Related features:** 78–84

The Career Copilot combines user context, retrieval, and LLM generation.

### Complete Flow

```text
User Message
     |
     v
FastAPI Chat Endpoint
     |
     v
Authentication and Validation
     |
     v
Conversation Context
     |
     v
Intent Detection
     |
     v
Select Relevant Workflow
     |
     +-----------------------------+
     |              |              |
     v              v              v
 Resume Context  Job Context   Career Context
     |              |              |
     +--------------+--------------+
                    |
                    v
              Context Retrieval
                    |
                    v
               LangGraph
                    |
                    v
                Ollama
                    |
                    v
             Response Validation
                    |
                    v
              Save Message
                    |
                    v
             Return Response
                    |
                    v
              React Chat UI
```

### Possible Copilot Intents

- Resume analysis.
- Job recommendations.
- Skill gap questions.
- Career planning.
- Interview preparation.
- Internship discovery.
- Application preparation.

### Context Management

The Copilot should retrieve only relevant information.

For example:

- Resume questions require resume context.
- Job questions require job context.
- Roadmap questions require career goal and skill gap context.

Do not send the entire user database or every previous conversation into every LLM request.

---

## 18. Embedding and RAG Data Flow

Embeddings help Nexora AI find semantically related information.

### Document Ingestion Flow

```text
Knowledge Source
      |
      v
Extract Text
      |
      v
Clean Text
      |
      v
Split into Chunks
      |
      v
Generate Embeddings
      |
      v
Store in pgvector
      |
      v
Save Source Metadata
```

### Retrieval Flow

```text
User Query
     |
     v
Generate Query Embedding
     |
     v
Vector Similarity Search
     |
     v
Retrieve Relevant Chunks
     |
     v
Apply Metadata Filters
     |
     v
Build Context
     |
     v
Send to Local LLM
     |
     v
Generate Grounded Response
     |
     v
Return Sources
```

### Stored Data

| Data | Purpose |
|---|---|
| Document ID | Identify source document |
| Chunk ID | Identify text segment |
| Chunk Text | Store searchable content |
| Embedding | Store vector representation |
| Source URL | Identify original source |
| Model Name | Track embedding model |
| Created At | Track indexing time |

### Important Rules

- Use the same embedding model for indexing and retrieval.
- Keep embedding dimensions consistent.
- Rebuild embeddings after an incompatible model change.
- Filter private user data by authenticated user ID.
- Preserve source references for grounded answers.

---

## 19. File Storage Data Flow

Initially, Nexora AI can use local file storage during development.

### Upload Flow

```text
User Upload
    |
    v
FastAPI Validation
    |
    v
Generate Unique File Name
    |
    v
Store Original File
    |
    v
Save File Metadata
    |
    v
Link File to User and Resume
```

### Storage Structure

```text
storage/
    |
    +-- resumes/
    |   +-- user_001/
    |       +-- resume_001.pdf
    |
    +-- reports/
    |   +-- user_001/
    |
    +-- temp/
```

The directory structure is illustrative. Production storage should use non-guessable identifiers and enforce access controls.

### Storage Rules

- Keep files outside public directories.
- Use generated storage identifiers.
- Store file metadata in PostgreSQL.
- Check user ownership before access.
- Restrict file size and file type.
- Remove temporary files after processing.
- Define retention and deletion policies.

---

## 20. Background Processing Data Flow

Some operations may take longer than a normal HTTP request.

Examples:

- Resume analysis.
- Large document processing.
- Employer research.
- Embedding generation.
- Career report generation.
- Bulk job analysis.

### Background Workflow

```text
User Starts Task
       |
       v
FastAPI Request
       |
       v
Create Task Record
       |
       v
Queue Background Work
       |
       v
Return Task ID
       |
       v
Worker Processes Task
       |
       v
Update Task Status
       |
       v
Save Results
       |
       v
Frontend Checks Status
       |
       v
Display Completed Result
```

### Task Status

Use consistent states:

- Pending.
- Processing.
- Completed.
- Failed.
- Cancelled.

### Initial Development

Start with FastAPI background tasks only for simple, lightweight operations.

For longer or resource-intensive jobs, introduce a proper task queue and worker architecture.

Possible future technologies:

- Redis.
- Celery.
- Dedicated worker processes.

Do not assume that FastAPI background tasks provide durable job execution after a server restart.

---

## 21. API Data Flow Standards

All frontend communication should happen through versioned API endpoints.

Example base path:

```text
/api/v1/
```

### Example Endpoints

| Operation | Method | Endpoint |
|---|---|---|
| Upload Resume | POST | `/resumes` |
| Get Resume | GET | `/resumes/{resume_id}` |
| Analyze Resume | POST | `/resumes/{resume_id}/analyze` |
| Get Resume Report | GET | `/resumes/{resume_id}/report` |
| Analyze Job | POST | `/jobs/analyze` |
| Search Jobs | GET | `/jobs` |
| Match Job | POST | `/matches` |
| Get Skill Gaps | GET | `/skill-gaps` |
| Generate Roadmap | POST | `/roadmaps/generate` |
| Copilot Message | POST | `/copilot/messages` |

### Response Format

Successful response:

```json
{
  "success": true,
  "message": "Resume analysis completed",
  "data": {
    "resume_id": "resume_123",
    "status": "completed"
  }
}
```

Error response:

```json
{
  "success": false,
  "message": "Unable to process resume",
  "error": {
    "code": "RESUME_PROCESSING_FAILED"
  }
}
```

The actual API schemas should be maintained centrally and aligned with API_DOCUMENTATION.md.

---

## 22. Database Data Flow

PostgreSQL acts as the central application database.

### Main Data Relationships

```text
Users
  |
  +---- User Profiles
  |
  +---- Resumes
  |       |
  |       +---- Resume Versions
  |       |
  |       +---- Resume Analysis
  |       |
  |       +---- Extracted Skills
  |
  +---- Job Matches
  |
  +---- Skill Gaps
  |
  +---- Career Goals
  |       |
  |       +---- Roadmaps
  |
  +---- Assessments
  |
  +---- Applications
  |
  +---- Conversations
          |
          +---- Messages
```

### Database Responsibilities

- Store user information.
- Store resume metadata and analysis.
- Store structured skills and experience.
- Store job and company information.
- Store match results.
- Store readiness scores.
- Store career roadmaps.
- Store assessment history.
- Store applications and conversations.
- Store embeddings and retrieval metadata.

### Data Consistency

Use database transactions for operations that require multiple related records to be created or updated together.

---

## 23. Data Security and Privacy Flow

All user data must be protected throughout its lifecycle.

### Security Flow

```text
Incoming Request
      |
      v
Authentication
      |
      v
Identify User
      |
      v
Authorize Operation
      |
      v
Validate User Ownership
      |
      v
Process Data
      |
      v
Store with User Relationship
      |
      v
Return Authorized Result
```

### Security Rules

- Authenticate protected API requests.
- Enforce user-level authorization.
- Use parameterized database operations.
- Validate uploaded documents.
- Restrict access to private files.
- Keep passwords hashed.
- Protect authentication tokens.
- Apply rate limiting.
- Avoid logging sensitive resume information.
- Define user data deletion procedures.
- Protect local AI services from untrusted external access.

### Important Principle

Authentication alone is not enough.

Every operation involving private user data must verify that the requested record belongs to the authenticated user.

---

## 24. Error Handling Data Flow

Failures can occur in:

- Frontend requests.
- File uploads.
- PDF extraction.
- DOCX extraction.
- Database operations.
- Ollama requests.
- Embedding generation.
- External job sources.
- Background workers.

### Error Flow

```text
Operation Starts
      |
      v
Error Occurs
      |
      v
Catch Exception
      |
      v
Log Safe Error Details
      |
      v
Update Task Status
      |
      v
Return Standard Error
      |
      v
Display Recovery Action
```

### Error Handling Rules

- Use meaningful error codes.
- Avoid exposing stack traces to users.
- Keep logs free of private document content.
- Retry only operations that are safe to repeat.
- Handle model timeouts.
- Preserve completed results when later steps fail.
- Avoid duplicate records when retrying requests.

---

## 25. Data Flow Monitoring

Track important system activity.

### Backend Metrics

- API response time.
- Database query time.
- AI model response time.
- Resume processing duration.
- Background task duration.
- Failed operations.
- Embedding generation time.

### AI Metrics

- Model name.
- Model version or tag.
- Input and output token counts, where available.
- Inference duration.
- Structured output validation failures.
- Retrieval quality.
- Model memory consumption.

Do not log full prompts or private user documents by default.

---

## 26. Data Flow by Development Phase

| Phase | Main Data Flow |
|---|---|
| 1 | Frontend, backend, and database foundation |
| 2 | Resume upload, storage, and text extraction |
| 3 | Resume text to structured intelligence |
| 4 | Resume data to quality analysis |
| 5 | Analysis data to reports and analytics |
| 6 | Job description to structured requirements |
| 7 | Company sources to employer intelligence |
| 8 | Search request to job discovery results |
| 9 | Resume and job data to match results |
| 10 | Resume skills and job skills to skill gaps |
| 11 | Career profile to readiness score |
| 12 | Career goal and skill gaps to roadmap |
| 13 | Assessment input to skill evidence |
| 14 | User message and context to Copilot response |
| 15 | Authentication, authorization, security, and deployment |

---

## 27. Final Data Flow Principles

Nexora AI should follow these principles:

1. React communicates with FastAPI through APIs.
2. FastAPI coordinates business services.
3. PostgreSQL stores structured application data.
4. Local storage holds uploaded files during initial development.
5. Ollama handles local LLM inference.
6. Embeddings support semantic retrieval.
7. LangChain manages reusable AI components.
8. LangGraph coordinates multi-step workflows.
9. Python calculates scores that require deterministic logic.
10. LLM outputs are validated before storage.
11. Every private data operation checks user ownership.
12. Long-running tasks use background processing.
13. AI reports should retain supporting source information.
14. Errors and processing states should be visible and recoverable.
15. Data flow should remain modular and testable.

**Final Goal:** Create a reliable data pipeline that connects user profiles, resumes, job opportunities, employer requirements, AI analysis, and career development into one unified Nexora AI platform.