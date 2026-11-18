# TESTING_STRATEGY.md

# Nexora AI: Testing Strategy

## 1. Purpose

This document defines the testing strategy for Nexora AI.

The goal is to ensure that every feature, API, AI agent, workflow, and database operation works correctly, securely, and reliably.

Nexora AI includes:

- React frontend.
- FastAPI backend.
- PostgreSQL database.
- Ollama local LLM.
- LangChain and LangGraph.
- RAG and vector search.
- Resume and job analysis.
- Career intelligence workflows.

Testing must cover both traditional software functionality and AI-generated results.

### Main Objectives

1. Detect bugs before deployment.
2. Verify frontend functionality.
3. Validate backend APIs.
4. Ensure database consistency.
5. Test AI agent outputs.
6. Verify LangGraph workflows.
7. Evaluate RAG retrieval quality.
8. Protect user data.
9. Measure performance.
10. Maintain application reliability.

---

## 2. Testing Principles

### 2.1 Test Early

Write tests while developing features instead of waiting until the entire application is complete.

### 2.2 Test Individual Components

Each service, function, component, and agent should be tested independently.

### 2.3 Test Complete Workflows

Verify that connected modules work together correctly.

### 2.4 Use Deterministic Tests

Use fixed inputs and expected outputs for normal application logic.

### 2.5 Isolate AI Testing

LLM outputs can vary. Test their structure, factual grounding, and quality separately from deterministic business logic.

### 2.6 Protect Real User Data

Use synthetic test accounts and test resumes. Never use real personal information in ordinary test fixtures.

### 2.7 Automate Repeated Tests

Run automated tests whenever code changes.

---

## 3. Testing Levels

Nexora AI will use five main testing levels.

| Level | Purpose | Example |
|---|---|---|
| Unit Testing | Test individual functions | Skill matching calculation |
| Integration Testing | Test connected components | FastAPI with PostgreSQL |
| Workflow Testing | Test complete AI workflows | Resume analysis workflow |
| End-to-End Testing | Test complete user journeys | Upload resume to view report |
| Acceptance Testing | Verify business requirements | Career roadmap meets user needs |

### Testing Flow

```text
             CODE DEVELOPMENT
                    |
                    v
               UNIT TESTS
                    |
                    v
            INTEGRATION TESTS
                    |
                    v
             WORKFLOW TESTS
                    |
                    v
              E2E TESTS
                    |
                    v
           ACCEPTANCE TESTS
                    |
                    v
              DEPLOYMENT
```

A deployment should not proceed when critical tests fail.

---

# PART A: FRONTEND TESTING

## 4. Frontend Testing Strategy

**Technology:** React, JavaScript, Vite.

### Testing Tools

| Tool | Purpose |
|---|---|
| Vitest | Unit and component tests |
| React Testing Library | React component testing |
| MSW | Mock API requests |
| Playwright | Browser end-to-end testing |

### 4.1 Component Testing

Test individual React components.

Examples:

- Button.
- Input.
- Modal.
- Sidebar.
- Navigation.
- Resume upload component.
- Dashboard cards.
- Job cards.
- Match score component.
- Skill gap visualization.
- Roadmap component.

### Example Test Cases

| Component | Test |
|---|---|
| Login Form | Validate required fields |
| Resume Upload | Accept supported file types |
| Resume Upload | Reject unsupported files |
| Dashboard | Display user information |
| Job Card | Display job details |
| Match Score | Display calculated score |
| Roadmap | Display roadmap stages |
| Copilot Chat | Display user and assistant messages |

### 4.2 Form Testing

Test:

- Required field validation.
- Invalid email.
- Empty input.
- Password validation.
- File type validation.
- File size validation.
- Form submission.
- API error messages.
- Loading states.

### 4.3 API Integration Testing

Use MSW to mock backend responses.

Verify:

- Correct API endpoint.
- Request parameters.
- Request payload.
- Loading state.
- Success response.
- Error response.
- Unauthorized response.
- Empty response.

### 4.4 Responsive UI Testing

Test the application on:

- Desktop.
- Laptop.
- Tablet.
- Mobile.

Verify:

- Navigation behavior.
- Sidebar responsiveness.
- Card layouts.
- Tables.
- Forms.
- Dialogs.
- Dashboard charts.

### 4.5 Accessibility Testing

Verify:

- Keyboard navigation.
- Form labels.
- Button names.
- Focus visibility.
- Color contrast.
- Screen-reader-friendly content.
- Accessible error messages.

---

# PART B: BACKEND TESTING

## 5. Backend Testing Strategy

**Technology:** Python, FastAPI.

### Testing Tools

| Tool | Purpose |
|---|---|
| Pytest | Test framework |
| HTTPX | API testing |
| FastAPI TestClient | API endpoint testing |
| pytest-asyncio | Async testing |
| Coverage.py | Test coverage |
| Factory Boy | Test data creation, if needed |

### 5.1 API Testing

Test every implemented API endpoint.

| Module | Test Cases |
|---|---|
| Authentication | Registration, login, logout |
| User Profile | Create, read, update |
| Resume | Upload, retrieve, delete |
| Resume Analysis | Start, retrieve, validate results |
| Job Description | Submit and analyze |
| Employer Intelligence | Research and retrieve reports |
| Job Discovery | Search and filter |
| Job Matching | Calculate and retrieve match |
| Skill Gap | Detect and compare skills |
| Career Readiness | Calculate and retrieve score |
| Career Roadmap | Generate and update |
| Assessments | Generate and submit |
| Career Copilot | Send message and retrieve response |
| Applications | Create and update application |

Only test endpoints that have been implemented. Future endpoints should be added to the test plan when their phases begin.

### 5.2 API Validation Testing

Verify:

- Valid request.
- Missing required fields.
- Invalid data types.
- Incorrect IDs.
- Invalid file uploads.
- Unauthorized access.
- Forbidden access.
- Missing resources.
- Duplicate requests.
- Unexpected server errors.

### 5.3 Service Testing

Test backend business services independently of HTTP endpoints.

Examples:

- Resume parsing service.
- Skill normalization service.
- Job filtering service.
- Match scoring service.
- Readiness calculation service.
- Roadmap persistence service.
- Application management service.

### 5.4 Error Handling Testing

Verify that:

- Errors return consistent response structures.
- Internal stack traces are not exposed.
- Database failures are handled.
- LLM failures are handled.
- External service timeouts are handled.
- Invalid input is rejected safely.

---

# PART C: DATABASE TESTING

## 6. Database Testing Strategy

**Technology:** PostgreSQL and pgvector.

### Testing Objectives

- Verify database connections.
- Verify table structures.
- Verify relationships.
- Verify constraints.
- Verify migrations.
- Verify user data isolation.
- Verify transaction behavior.
- Verify vector search.

### 6.1 Schema Testing

Test the main database entities.

| Entity | Test |
|---|---|
| Users | User creation and uniqueness |
| User Profiles | User relationship |
| Resumes | Resume ownership |
| Resume Versions | Version relationships |
| Resume Skills | Skill references |
| Companies | Company records |
| Jobs | Job records |
| Job Skills | Job-skill relationships |
| Match Results | Resume-job relationships |
| Skill Gaps | User and skill relationships |
| Roadmaps | User and goal relationships |
| Assessments | Assessment records |
| Applications | Application ownership |
| Conversations | User conversation ownership |
| Messages | Conversation relationships |
| Embeddings | Vector storage and retrieval |

### 6.2 Relationship Testing

Verify:

- Foreign key constraints.
- One-to-many relationships.
- Many-to-many relationships.
- Unique constraints.
- Required fields.
- Deletion behavior.

### 6.3 Migration Testing

Use Alembic to manage schema changes.

Test:

1. Create an empty test database.
2. Apply all migrations.
3. Verify the schema.
4. Insert test records.
5. Test the next migration.
6. Verify migration consistency.

Never use a production database for migration tests.

### 6.4 Transaction Testing

Verify that:

- Successful transactions are committed.
- Failed transactions are rolled back.
- Partial updates do not leave inconsistent data.
- Duplicate operations are handled correctly.

### 6.5 Vector Database Testing

For pgvector, verify:

- Embedding insertion.
- Embedding dimensions.
- Similarity search.
- Metadata filtering.
- User-specific retrieval.
- Empty search results.

Use the same embedding model and dimensions in both ingestion and retrieval.

---

# PART D: AI MODEL TESTING

## 7. AI Testing Strategy

AI testing is different from traditional software testing.

A normal Python function should produce predictable results for the same input.

An LLM may produce different wording or slightly different outputs for the same prompt.

Therefore, AI testing should evaluate:

- Output structure.
- Factual correctness.
- Relevance.
- Completeness.
- Grounding.
- Consistency.
- Safety.
- Response time.

### 7.1 Model Testing

Initial local model candidate:

`qwen2.5:3b`

Test the model for:

- Resume information extraction.
- Job requirement extraction.
- Skill identification.
- Career explanations.
- Roadmap generation.
- Interview feedback.

### 7.2 Model Evaluation Dataset

Create a fixed dataset of test examples.

| Dataset | Test Content |
|---|---|
| Resume Dataset | Different resume formats |
| Job Dataset | Different job descriptions |
| Skills Dataset | Technical and transferable skills |
| Career Dataset | Different target roles |
| Interview Dataset | Questions and expected evaluation criteria |
| Roadmap Dataset | Skill gaps and learning goals |

Use synthetic or properly licensed data. Avoid uploading private resumes to external evaluation services without authorization.

### 7.3 AI Evaluation Metrics

| Metric | Purpose |
|---|---|
| Extraction Accuracy | Correct information extraction |
| Precision | How many identified items are correct |
| Recall | How many relevant items were identified |
| F1 Score | Balance between precision and recall |
| Relevance | Whether output answers the task |
| Groundedness | Whether claims are supported by input or retrieved evidence |
| Consistency | Whether similar inputs receive similar results |
| Latency | Time taken to generate output |

Not every metric applies to every agent. Select metrics based on the task.

### 7.4 Structured Output Testing

All important agent outputs should use Pydantic schemas.

Example:

```python
from pydantic import BaseModel
from typing import Optional


class SkillExtraction(BaseModel):
    skills: list[str]
    experience_level: Optional[str] = None
    confidence: Optional[float] = None
```

Test:

- Valid output.
- Missing fields.
- Incorrect field types.
- Empty values.
- Unexpected values.
- Invalid JSON.
- Out-of-range confidence values.

The application should handle invalid model output without crashing.

### 7.5 Hallucination Testing

Create test cases where information is missing.

Example:

Input:

```text
Resume does not mention cloud computing.
```

Expected behavior:

```text
Cloud computing experience is not specified.
```

The AI should not invent experience or qualifications.

### 7.6 Prompt Testing

Test:

- Clear instructions.
- Ambiguous instructions.
- Missing information.
- Very long input.
- Malicious instructions inside uploaded documents.
- Conflicting information.
- Unsupported claims.

Store important prompt versions so that changes can be evaluated against the same test dataset.

---

# PART E: AI AGENT TESTING

## 8. Agent Testing Strategy

Each agent must have independent tests.

| Agent | Main Testing Focus |
|---|---|
| Resume Intelligence | Extraction correctness |
| Resume Quality | Improvement relevance |
| Job Description | Requirement extraction |
| Employer Intelligence | Source reliability |
| Job Matching | Match calculation and explanation |
| Skill Gap | Missing skill detection |
| Career Readiness | Score consistency |
| Career Roadmap | Roadmap relevance |
| Skill Assessment | Question quality and evaluation |
| Interview | Feedback quality |
| GitHub Analysis | Evidence-based analysis |
| Internship Recommendation | Opportunity relevance |
| Application Preparation | Draft accuracy |
| Career Copilot | Intent routing |

### 8.1 Agent Unit Tests

Test each agent's:

- Input validation.
- Prompt construction.
- Tool selection.
- Output parsing.
- Error handling.
- Permission checks.

Mock the LLM when testing deterministic behavior.

### 8.2 Agent Integration Tests

Verify that agents correctly interact with:

- Ollama.
- PostgreSQL.
- pgvector.
- LangChain.
- Backend services.
- Approved external integrations.

### 8.3 Agent Quality Tests

Evaluate whether the agent:

- Performs the correct task.
- Uses the correct information.
- Avoids unsupported claims.
- Returns valid structured output.
- Explains recommendations.
- Handles missing information.

### 8.4 Tool Permission Tests

Verify that an agent cannot:

- Read another user's private resume.
- Access unauthorized repositories.
- Modify records outside its scope.
- Execute unrestricted SQL.
- Run arbitrary shell commands.
- Submit applications without approval.

---

# PART F: LANGGRAPH WORKFLOW TESTING

## 9. LangGraph Testing Strategy

LangGraph controls the execution of multi-step AI workflows.

Testing should verify that nodes, state transitions, routing, and error handling work correctly.

### 9.1 Node Testing

Test every workflow node separately.

Example resume workflow:

| Node | Test |
|---|---|
| Load Resume | Correct resume retrieved |
| Extract Text | Text extraction succeeds |
| Analyze Sections | Correct sections identified |
| Extract Skills | Skills extracted |
| Normalize Skills | Skill names standardized |
| Validate Output | Schema validation works |
| Save Results | Correct records stored |

### 9.2 Conditional Routing Tests

Verify that the graph selects the correct path.

Example:

```text
                USER REQUEST
                     |
                     v
                 INTENT NODE
                     |
          +----------+----------+
          |          |          |
          v          v          v
        Resume      Job       Career
       Workflow   Workflow   Workflow
```

Test:

- Resume analysis request.
- Job search request.
- Career roadmap request.
- Unsupported request.
- Ambiguous request.

### 9.3 State Testing

Verify:

- Initial state.
- State updates.
- Required fields.
- State persistence.
- Invalid state handling.
- User ID consistency.

### 9.4 Retry Testing

Simulate:

- Invalid model output.
- Ollama timeout.
- Tool failure.
- Database failure.
- Missing information.

Verify retry limits and fallback behavior.

### 9.5 Checkpoint Testing

If workflow checkpointing is enabled, test:

- Saving workflow state.
- Resuming an interrupted workflow.
- Preventing duplicate writes.
- Access isolation between users.
- Expired or invalid workflow state.

### 9.6 Human Approval Testing

For sensitive operations, verify that execution pauses until the user approves.

Example:

```text
Generate Application Draft
          |
          v
    User Reviews Draft
          |
          v
   Approval Required
          |
     +----+----+
     |         |
     v         v
  Approved   Rejected
     |         |
     v         v
 Continue    Stop
```

The system should not treat a generated draft as permission to submit an application.

---

# PART G: RAG TESTING

## 10. RAG Testing Strategy

RAG combines information retrieval with LLM generation.

Nexora AI will initially use PostgreSQL and pgvector.

### 10.1 Document Ingestion Testing

Test:

- Document upload.
- Text extraction.
- Text cleaning.
- Chunk generation.
- Metadata extraction.
- Embedding generation.
- Vector storage.

### 10.2 Chunking Testing

Evaluate multiple chunking strategies:

1. Fixed-size chunking.
2. Recursive chunking.
3. Semantic chunking.
4. Section-based chunking.
5. Parent-child chunking.

Compare:

- Context preservation.
- Retrieval relevance.
- Duplicate information.
- Processing time.
- Storage requirements.

### 10.3 Retrieval Testing

Test:

- Relevant query.
- Unrelated query.
- Partial query.
- Ambiguous query.
- No-result query.
- User-specific query.

### 10.4 Retrieval Metrics

| Metric | Purpose |
|---|---|
| Precision@K | Relevant results among retrieved items |
| Recall@K | Relevant items successfully retrieved |
| MRR | Ranking of the first relevant result |
| nDCG@K | Quality of ranked retrieval results |

### 10.5 Generation Testing

Verify:

- Answers use retrieved information.
- Claims are supported by sources.
- Missing information is acknowledged.
- Irrelevant context is ignored.
- Source references are preserved.

### 10.6 RAG Security Testing

Test:

- User-specific metadata filtering.
- Unauthorized document access.
- Malicious document instructions.
- Prompt injection.
- Sensitive information leakage.

Retrieval filters must be enforced by the backend, not by an LLM instruction alone.

---

# PART H: SECURITY TESTING

## 11. Security Testing Strategy

Security testing is essential because Nexora AI stores personal resumes and career information.

### 11.1 Authentication Testing

Verify:

- Registration.
- Login.
- Logout.
- Password recovery.
- Invalid credentials.
- Expired sessions.
- Unauthorized requests.

### 11.2 Authorization Testing

Verify:

- Users can access their own records.
- Users cannot access other users' records.
- Protected endpoints reject unauthorized requests.
- Agent tools respect ownership rules.

### 11.3 File Upload Security

Test:

- Unsupported extensions.
- Oversized files.
- Corrupted documents.
- Malicious filenames.
- Invalid document contents.
- Suspicious file payloads.

Validate file contents rather than trusting only the filename or MIME type.

### 11.4 API Security

Test:

- SQL injection.
- Cross-site scripting.
- Cross-site request forgery where applicable.
- Rate limiting.
- Input validation.
- Authentication bypass.
- Sensitive data exposure.

### 11.5 AI Security

Test:

- Prompt injection.
- Tool misuse.
- Unauthorized retrieval.
- Data leakage.
- Malicious repository content.
- Malicious job description content.
- Unsafe code execution.

### 11.6 Privacy Testing

Verify:

- Resume access is restricted.
- User data is isolated.
- Logs do not expose sensitive information.
- Deletion requests are handled correctly.
- Backups follow the retention policy.

---

# PART I: PERFORMANCE TESTING

## 12. Performance Testing Strategy

Measure application performance before production deployment.

### Testing Tools

| Tool | Purpose |
|---|---|
| Locust | Backend load testing |
| k6 | API performance testing |
| Pytest Benchmark | Python benchmarking |
| Browser DevTools | Frontend performance |
| PostgreSQL EXPLAIN ANALYZE | Query performance |

### 12.1 Frontend Performance

Measure:

- Initial page load.
- Route navigation.
- Dashboard rendering.
- Large resume preview.
- Chat rendering.
- Mobile responsiveness.

### 12.2 Backend Performance

Measure:

- API response time.
- Database query time.
- File upload time.
- Resume extraction time.
- Concurrent request handling.

### 12.3 AI Performance

Measure:

- Model loading time.
- First-token latency.
- Total generation time.
- Tokens per second.
- Memory usage.
- GPU and CPU utilization.

### 12.4 Load Testing

Test:

- Single user.
- Multiple concurrent users.
- Multiple resume uploads.
- Concurrent job searches.
- Multiple AI requests.

Start with small loads and increase gradually.

Do not assume local Ollama performance represents public production performance.

### 12.5 Initial Performance Targets

These are provisional engineering targets, not measured guarantees.

| Operation | Initial Target |
|---|---|
| Simple API Read | Under 500 ms |
| Database Query | Under 200 ms |
| Dashboard Initial Load | Under 3 seconds |
| Skill Matching Calculation | Under 1 second |
| Resume Processing | Under 30 seconds |
| AI Workflow | Measured per model and task |

LLM workflows may take longer depending on model size, prompt length, hardware, and concurrent requests.

---

# PART J: END-TO-END TESTING

## 13. End-to-End Testing Strategy

Use Playwright to test complete user journeys in a real browser.

### 13.1 Authentication Flow

```text
Open Application
      |
      v
Register Account
      |
      v
Login
      |
      v
Open Dashboard
      |
      v
Verify User Profile
```

### 13.2 Resume Analysis Flow

```text
Login
  |
  v
Upload Resume
  |
  v
Validate File
  |
  v
Extract Resume Text
  |
  v
Analyze Resume
  |
  v
Generate Report
  |
  v
View Dashboard
```

### 13.3 Job Matching Flow

```text
Login
  |
  v
Select Resume
  |
  v
Enter Job Description
  |
  v
Analyze Job
  |
  v
Run Matching
  |
  v
View Match Score
  |
  v
View Skill Gaps
```

### 13.4 Career Roadmap Flow

```text
Login
  |
  v
Select Career Goal
  |
  v
Analyze Current Skills
  |
  v
Identify Skill Gaps
  |
  v
Generate Roadmap
  |
  v
View Learning Stages
  |
  v
Update Progress
```

### 13.5 Career Copilot Flow

```text
Login
  |
  v
Open Career Copilot
  |
  v
Send Message
  |
  v
Identify Intent
  |
  v
Execute Correct Workflow
  |
  v
Generate Response
  |
  v
Display Result
```

---

# PART K: TEST DATA AND ENVIRONMENTS

## 14. Test Data Management

Use controlled test datasets.

### Test Data Categories

| Dataset | Purpose |
|---|---|
| Valid Resumes | Normal resume processing |
| Invalid Resumes | File validation |
| Incomplete Resumes | Missing information |
| Job Descriptions | Requirement extraction |
| Skill Taxonomy | Skill normalization |
| Company Records | Employer intelligence |
| Interview Questions | Interview evaluation |
| Assessment Answers | Assessment evaluation |
| RAG Documents | Retrieval testing |

### Test Data Rules

- Use synthetic personal information.
- Do not commit secrets.
- Avoid production user data.
- Keep fixtures version-controlled where appropriate.
- Reset test data between isolated test runs.
- Use stable test IDs where practical.

## 15. Testing Environments

Maintain separate environments.

| Environment | Purpose |
|---|---|
| Local | Developer testing |
| Test | Automated testing |
| Staging | Pre-production validation |
| Production | Real users |

### Environment Rules

- Use separate database credentials.
- Never point automated tests at production.
- Use mock services when external integrations are unavailable.
- Keep test configuration separate from production configuration.
- Do not commit `.env` files containing secrets.

---

# PART L: PROJECT STRUCTURE

## 16. Recommended Testing Folder Structure

```text
nexora-ai/
|
+-- frontend/
|   |
|   +-- src/
|   |
|   +-- tests/
|       |
|       +-- components/
|       +-- pages/
|       +-- services/
|       +-- integration/
|       +-- e2e/
|
+-- backend/
    |
    +-- app/
    |
    +-- tests/
        |
        +-- unit/
        |   |
        |   +-- services/
        |   +-- agents/
        |   +-- tools/
        |
        +-- integration/
        |   |
        |   +-- api/
        |   +-- database/
        |   +-- ollama/
        |
        +-- workflows/
        |
        +-- rag/
        |
        +-- security/
        |
        +-- performance/
        |
        +-- fixtures/
```

Keep tests close to the modules they validate when that makes maintenance easier.

---

## 17. Example Backend Test

Example: Testing a deterministic skill matching function.

```python
def calculate_skill_match(
    required_skills: list[str],
    candidate_skills: list[str]
) -> float:

    if not required_skills:
        return 0.0

    required = {
        skill.lower().strip()
        for skill in required_skills
    }

    candidate = {
        skill.lower().strip()
        for skill in candidate_skills
    }

    matched = required.intersection(candidate)

    return round(
        len(matched) / len(required) * 100,
        2
    )
```

Test:

```python
def test_calculate_skill_match():

    required = [
        "Python",
        "SQL",
        "Machine Learning"
    ]

    candidate = [
        "Python",
        "SQL"
    ]

    result = calculate_skill_match(
        required,
        candidate
    )

    assert result == 66.67
```

This is a simple exact-name matching example. Production matching should also account for normalized aliases and explicitly defined skill equivalencies.

---

## 18. Example Frontend Test

Example: Testing a React component with Vitest and React Testing Library.

```jsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

function WelcomeCard({ name }) {
  return <h1>Welcome, {name}</h1>;
}

describe("WelcomeCard", () => {
  it("displays the user name", () => {
    render(<WelcomeCard name="Alex" />);

    expect(
      screen.getByText("Welcome, Alex")
    ).toBeInTheDocument();
  });
});
```

This verifies that the component renders the expected content.

---

## 19. Test Automation and CI

Use GitHub Actions to automate tests.

### CI Workflow

```text
Developer Pushes Code
         |
         v
    GitHub Actions
         |
    +----+-----+
    |          |
    v          v
Frontend    Backend
 Tests       Tests
    |          |
    +----+-----+
         |
         v
    Check Results
         |
    +----+-----+
    |          |
    v          v
  Passed     Failed
    |          |
    v          v
 Continue   Fix Issues
```

### Recommended CI Checks

1. Install dependencies.
2. Check frontend build.
3. Run frontend unit tests.
4. Run backend unit tests.
5. Run backend integration tests.
6. Run linting.
7. Check migration consistency.
8. Generate test coverage reports.

Use mocked Ollama responses in standard CI tests to keep execution fast and reliable.

Run separate local AI integration tests when the Ollama model is available.

---

## 20. Test Coverage Strategy

Coverage helps identify untested code, but it does not prove software quality.

### Initial Coverage Targets

| Area | Target |
|---|---:|
| Python Business Logic | 85% |
| API Services | 80% |
| Database Repositories | 80% |
| Frontend Components | 75% |
| AI Workflow Logic | 80% |
| Critical Security Logic | 100% of defined cases |

These are targets, not guarantees. Critical behavior must also have meaningful assertions and edge-case tests.

Do not optimize for coverage numbers by writing low-value tests.

---

# PART M: TESTING BY DEVELOPMENT PHASE

## 21. Phase-Wise Testing Plan

Testing should follow the existing 15-phase, 100-feature roadmap.

| Phase | Module | Main Testing |
|---|---|---|
| 1 | Project Foundation | Frontend, backend, database setup |
| 2 | Resume Upload & Processing | File validation and extraction |
| 3 | Resume Intelligence | Extraction and schema validation |
| 4 | Resume Quality Analysis | Scoring and recommendation quality |
| 5 | Resume Intelligence Report | Analytics and PDF export |
| 6 | Job Description Analyzer | Requirement extraction |
| 7 | Employer Intelligence | Source validation |
| 8 | Job Discovery | Search and filtering |
| 9 | Job Matching Engine | Matching accuracy |
| 10 | Skill Gap Intelligence | Missing and transferable skills |
| 11 | Career Readiness Score | Scoring consistency |
| 12 | Personalized Career Roadmap | Roadmap relevance |
| 13 | Skill Assessment & Verification | Question and evaluation quality |
| 14 | AI Career Copilot | Routing and agent workflows |
| 15 | Authentication, Security & Deployment | Security, performance, E2E, deployment |

Testing is continuous. Earlier phases should be retested when later changes affect them.

---

## 22. Bug Management

Every identified bug should be recorded.

### Bug Report Structure

```text
Bug ID:
Title:
Module:
Environment:
Steps to Reproduce:
Expected Result:
Actual Result:
Severity:
Priority:
Status:
Evidence:
```

### Bug Severity

| Severity | Description |
|---|---|
| Critical | Data breach, data loss, or application-wide failure |
| High | Important feature unavailable |
| Medium | Feature works incorrectly in some cases |
| Low | Minor UI or usability issue |

### Bug Fix Workflow

```text
Bug Identified
      |
      v
Create Bug Report
      |
      v
Reproduce Issue
      |
      v
Identify Root Cause
      |
      v
Implement Fix
      |
      v
Run Related Tests
      |
      v
Regression Testing
      |
      v
Close Bug
```

---

## 23. Release Readiness Checklist

Before deploying a release, verify:

### Frontend

- [ ] Main pages render correctly.
- [ ] Forms validate inputs.
- [ ] API errors display correctly.
- [ ] Responsive layouts work.
- [ ] Accessibility checks pass.

### Backend

- [ ] API tests pass.
- [ ] Validation works.
- [ ] Error handling works.
- [ ] Authentication and authorization work.
- [ ] Rate limiting is configured where needed.

### Database

- [ ] Migrations apply successfully.
- [ ] Relationships work.
- [ ] User isolation is verified.
- [ ] Backups and restoration are tested.

### AI

- [ ] Model integration works.
- [ ] Structured outputs validate.
- [ ] Hallucination tests pass.
- [ ] Agent permissions are restricted.
- [ ] LangGraph workflows complete correctly.
- [ ] RAG retrieval tests pass.

### Security

- [ ] Secrets are protected.
- [ ] File uploads are validated.
- [ ] Private data is isolated.
- [ ] Prompt injection tests are performed.
- [ ] Sensitive actions require approval.

### Deployment

- [ ] Production build succeeds.
- [ ] Environment variables are configured.
- [ ] Logging and monitoring work.
- [ ] Critical tests pass.
- [ ] Rollback plan is available.

---

## 24. Final Testing Strategy

Nexora AI will use a layered testing approach.

| Testing Area | Main Tool |
|---|---|
| Frontend | Vitest, React Testing Library |
| Frontend API Mocking | MSW |
| Browser E2E | Playwright |
| Backend | Pytest |
| API | HTTPX |
| Database | PostgreSQL test database |
| Migrations | Alembic |
| AI Models | Fixed evaluation datasets |
| Agent Workflows | LangGraph tests |
| RAG | Retrieval evaluation |
| Security | Automated and manual security tests |
| Performance | Locust, k6 |
| CI | GitHub Actions |

### Final Principle

**A successful AI feature is not just one that produces an answer. It must produce a valid, relevant, secure, explainable, and testable result.**

Nexora AI should be tested as both a traditional software application and an AI-powered career intelligence platform.