# DEVELOPMENT_GUIDELINES.md

# Nexora AI: Development Guidelines

## 1. Purpose

This document defines the development standards and coding practices for Nexora AI.

The goal is to maintain clean, readable, secure, testable, and scalable code throughout the project.

Nexora AI uses:

- React.
- JavaScript.
- Vite.
- Tailwind CSS.
- Shadcn UI.
- Python.
- FastAPI.
- PostgreSQL.
- SQLAlchemy.
- Alembic.
- LangChain.
- LangGraph.
- Ollama.
- pgvector.

These guidelines apply to all developers, contributors, and AI coding assistants working on the project.

### Main Objectives

1. Maintain consistent code quality.
2. Use a modular project structure.
3. Follow clear naming conventions.
4. Avoid unnecessary code duplication.
5. Write reusable components and services.
6. Maintain API consistency.
7. Follow secure coding practices.
8. Write automated tests.
9. Use Git properly.
10. Keep documentation updated.

---

## 2. Core Development Principles

### 2.1 Keep Code Simple

Write code that is easy to understand and maintain.

Avoid unnecessary abstractions and complicated logic.

### 2.2 Single Responsibility

Every component, function, class, and service should have a clearly defined responsibility.

### 2.3 Reusability

Create reusable components and services when they solve repeated problems.

### 2.4 Maintainability

Organize code so future developers can understand and modify it easily.

### 2.5 Separation of Concerns

Keep frontend, backend, business logic, database operations, and AI workflows separate.

### 2.6 Security First

Validate inputs, enforce authorization, and protect user data.

### 2.7 Testability

Write code that can be tested independently.

### 2.8 Documentation

Document important architectural decisions, APIs, complex logic, and setup procedures.

---

## 3. Project Architecture Rules

Nexora AI will follow a modular monolith architecture.

The frontend and backend remain separate applications, while backend features are organized into independent modules.

### Architecture

```text
NEXORA AI
   |
   +-- FRONTEND
   |     |
   |     +-- React
   |     +-- JavaScript
   |     +-- Vite
   |     +-- Tailwind CSS
   |     +-- Shadcn UI
   |
   +-- BACKEND
   |     |
   |     +-- FastAPI
   |     +-- API Routes
   |     +-- Services
   |     +-- Repositories
   |     +-- Models
   |     +-- Schemas
   |
   +-- AI ENGINE
   |     |
   |     +-- LangChain
   |     +-- LangGraph
   |     +-- Ollama
   |     +-- Agents
   |     +-- Workflows
   |     +-- RAG
   |
   +-- DATA LAYER
         |
         +-- PostgreSQL
         +-- pgvector
         +-- File Storage
```

### Architecture Rules

- Keep frontend and backend independent.
- Do not place business logic inside React components.
- Do not place database queries directly inside API route handlers.
- Keep AI workflows separate from ordinary business services.
- Use shared schemas for consistent data validation where appropriate.
- Avoid introducing microservices during the MVP.
- Keep external integrations behind service interfaces.

---

# PART A: FRONTEND DEVELOPMENT

## 4. Frontend Technology Standards

| Technology | Responsibility |
|---|---|
| React | UI development |
| JavaScript | Application logic |
| Vite | Development and build |
| Tailwind CSS | Styling |
| Shadcn UI | Reusable UI components |
| React Router | Navigation |
| Axios or Fetch | API communication |
| Vitest | Unit testing |
| React Testing Library | Component testing |
| Playwright | End-to-end testing |

Use JavaScript throughout the frontend. Do not introduce TypeScript unless the project requirements are explicitly changed.

---

## 5. Frontend Folder Structure

Recommended structure:

```text
frontend/
|
+-- public/
|
+-- src/
    |
    +-- assets/
    |
    +-- components/
    |   |
    |   +-- ui/
    |   +-- layout/
    |   +-- common/
    |   +-- dashboard/
    |
    +-- pages/
    |   |
    |   +-- auth/
    |   +-- dashboard/
    |   +-- resume/
    |   +-- jobs/
    |   +-- career/
    |   +-- copilot/
    |
    +-- features/
    |   |
    |   +-- resume/
    |   +-- matching/
    |   +-- skill-gap/
    |   +-- roadmap/
    |   +-- assessment/
    |
    +-- services/
    |   |
    |   +-- api.js
    |   +-- authService.js
    |   +-- resumeService.js
    |   +-- jobService.js
    |
    +-- hooks/
    |
    +-- context/
    |
    +-- utils/
    |
    +-- routes/
    |
    +-- styles/
    |
    +-- App.jsx
    +-- main.jsx
```

Organize files by feature when that makes ownership and maintenance clearer.

Do not create unnecessary folders for components that do not exist.

---

## 6. Frontend Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Components | PascalCase | ResumeCard.jsx |
| Pages | PascalCase | Dashboard.jsx |
| Hooks | camelCase with use | useAuth.js |
| Services | camelCase | resumeService.js |
| Utilities | camelCase | formatDate.js |
| Constants | UPPER_SNAKE_CASE | API_BASE_URL |
| CSS Classes | Tailwind utility classes | flex items-center |

### Component Naming

Use descriptive component names.

Good:

```jsx
function ResumeUpload() {
  return <div>Upload Resume</div>;
}

export default ResumeUpload;
```

Avoid:

```jsx
function RU() {
  return <div>Upload Resume</div>;
}
```

---

## 7. React Component Guidelines

### Rules

1. Keep components focused.
2. Avoid very large components.
3. Extract reusable UI into separate components.
4. Keep API calls in service files.
5. Use hooks for reusable stateful logic.
6. Handle loading states.
7. Handle error states.
8. Avoid unnecessary state.
9. Use meaningful variable names.
10. Keep accessibility in mind.

### Example

```jsx
function ResumeCard({ resume }) {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-semibold">
        {resume.fileName}
      </h3>

      <p className="text-sm text-gray-500">
        {resume.status}
      </p>
    </div>
  );
}

export default ResumeCard;
```

### Avoid

- Duplicating the same UI across pages.
- Writing large conditional expressions inside JSX.
- Putting all application logic in `App.jsx`.
- Mixing unrelated features in one component.
- Making direct database or AI service calls from the frontend.

---

## 8. Frontend API Communication

All backend communication should go through service modules.

Example:

`services/api.js`

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function apiRequest(
  endpoint,
  options = {}
) {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    throw new Error(
      error.detail || "Something went wrong"
    );
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}
```

This is a starting example. File uploads need a separate request configuration that does not manually set the multipart content type.

### API Rules

- Use a central API configuration.
- Avoid repeating API URLs.
- Handle errors consistently.
- Handle loading states.
- Use secure cookie authentication.
- Never store private server secrets in frontend code.
- Do not trust frontend authorization checks.

---

## 9. Frontend State Management

Use the simplest state management solution that meets the feature requirements.

### Recommended Approach

| Requirement | Solution |
|---|---|
| Local component state | useState |
| Shared authentication state | Context |
| Form state | Component state or form library |
| Server data | Fetch-based service or query library |
| Complex shared state | Introduce a dedicated state library only if needed |

Avoid introducing Redux or another state management library unless the application genuinely needs it.

---

# PART B: BACKEND DEVELOPMENT

## 10. Backend Technology Standards

| Technology | Responsibility |
|---|---|
| Python | Backend programming |
| FastAPI | API framework |
| Pydantic | Validation |
| SQLAlchemy | ORM |
| Alembic | Database migrations |
| PostgreSQL | Main database |
| pgvector | Vector search |
| Pytest | Backend testing |
| HTTPX | HTTP client and API tests |

Use Python 3.11 as the initial development baseline.

---

## 11. Backend Folder Structure

Recommended structure:

```text
backend/
|
+-- app/
|   |
|   +-- api/
|   |   |
|   |   +-- routes/
|   |   +-- dependencies.py
|   |
|   +-- core/
|   |   |
|   |   +-- config.py
|   |   +-- security.py
|   |   +-- exceptions.py
|   |
|   +-- models/
|   |
|   +-- schemas/
|   |
|   +-- services/
|   |
|   +-- repositories/
|   |
|   +-- agents/
|   |
|   +-- workflows/
|   |
|   +-- tools/
|   |
|   +-- ai/
|   |
|   +-- utils/
|   |
|   +-- main.py
|
+-- alembic/
|
+-- tests/
|
+-- requirements.txt
|
+-- .env.example
```

### Folder Responsibilities

| Folder | Responsibility |
|---|---|
| api | API routes |
| core | Configuration and security |
| models | SQLAlchemy database models |
| schemas | Pydantic schemas |
| services | Business logic |
| repositories | Database access |
| agents | Specialized AI agents |
| workflows | LangGraph workflows |
| tools | Restricted agent tools |
| ai | LLM, embeddings, prompts and retrieval |
| utils | Shared utilities |
| tests | Automated tests |

---

## 12. Backend Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Python Files | snake_case | resume_service.py |
| Functions | snake_case | analyze_resume() |
| Classes | PascalCase | ResumeService |
| Variables | snake_case | resume_id |
| Constants | UPPER_SNAKE_CASE | MAX_UPLOAD_SIZE |
| Database Tables | snake_case | resume_versions |
| Pydantic Schemas | PascalCase | ResumeCreate |

Use meaningful names that explain the purpose of the code.

---

## 13. FastAPI Route Guidelines

Keep API route handlers small.

Route handlers should:

1. Receive the request.
2. Validate input.
3. Authenticate the user.
4. Check authorization.
5. Call the appropriate service.
6. Return a consistent response.

### Example

```python
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"]
)


@router.get("/{resume_id}")
async def get_resume(
    resume_id: int,
    current_user=Depends(get_current_user)
):
    return await resume_service.get_resume(
        resume_id=resume_id,
        user_id=current_user.id
    )
```

This is illustrative. Import and dependency names should match the actual project implementation.

### API Rules

- Use appropriate HTTP methods.
- Use meaningful endpoint names.
- Validate path and query parameters.
- Enforce user ownership.
- Return appropriate HTTP status codes.
- Use consistent error responses.
- Avoid placing complex business logic in route handlers.
- Document important API behavior.

---

## 14. Service Layer Guidelines

The service layer contains business logic.

Examples:

- ResumeService.
- JobService.
- MatchingService.
- SkillGapService.
- RoadmapService.
- AssessmentService.
- ApplicationService.

### Responsibilities

- Execute business rules.
- Coordinate repositories.
- Validate business conditions.
- Call AI workflows when needed.
- Handle domain-level errors.

### Example

```python
class MatchingService:

    async def calculate_match(
        self,
        resume,
        job
    ):
        required_skills = job.required_skills

        candidate_skills = resume.skills

        return calculate_skill_match(
            required_skills,
            candidate_skills
        )
```

Keep deterministic business logic outside LLM prompts.

---

## 15. Repository Layer Guidelines

Repositories handle database access.

### Responsibilities

- Retrieve records.
- Insert records.
- Update records.
- Delete records.
- Handle database queries.

### Rules

- Keep database queries separate from API routes.
- Use SQLAlchemy.
- Use parameterized queries.
- Apply user ownership filters.
- Avoid unnecessary database calls.
- Handle transactions correctly.
- Do not return unauthorized records.

Do not allow an AI model to execute unrestricted database queries.

---

## 16. Error Handling Standards

Use consistent error handling across the backend.

### Recommended HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 204 | Successful request with no response body |
| 400 | Invalid request |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Resource not found |
| 409 | Resource conflict |
| 413 | Request too large |
| 422 | Validation error |
| 429 | Too many requests |
| 500 | Internal server error |
| 503 | Service unavailable |

### Rules

- Never expose internal stack traces.
- Log useful diagnostic information.
- Return user-friendly errors.
- Use consistent error structures.
- Handle database and AI failures separately.
- Avoid swallowing unexpected exceptions.

---

# PART C: DATABASE DEVELOPMENT

## 17. Database Standards

**Database:** PostgreSQL.

**ORM:** SQLAlchemy.

**Migration Tool:** Alembic.

### Database Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Tables | snake_case, plural | resumes |
| Columns | snake_case | created_at |
| Primary Keys | id | id |
| Foreign Keys | referenced_table_id | user_id |
| Indexes | ix_table_column | ix_resumes_user_id |
| Unique Constraints | uq_table_column | uq_users_email |

### Database Rules

- Use primary keys.
- Define foreign keys.
- Add appropriate indexes.
- Use timestamps where useful.
- Define deletion behavior explicitly.
- Avoid unnecessary duplicate information.
- Use database constraints for important invariants.
- Protect user ownership relationships.

---

## 18. Database Migration Guidelines

Use Alembic for schema changes.

### Migration Workflow

```text
CHANGE DATABASE MODEL
         |
         v
GENERATE MIGRATION
         |
         v
REVIEW MIGRATION FILE
         |
         v
RUN MIGRATION LOCALLY
         |
         v
TEST DATABASE CHANGES
         |
         v
COMMIT MIGRATION
         |
         v
APPLY IN DEPLOYMENT
```

### Commands

Create a migration:

```bash
alembic revision --autogenerate -m "add resume table"
```

Apply migrations:

```bash
alembic upgrade head
```

View current migration:

```bash
alembic current
```

### Rules

- Review generated migrations manually.
- Never edit production schema manually as the normal workflow.
- Test migrations on a separate database.
- Do not delete migration history.
- Consider backward compatibility.
- Define data migration behavior when changing existing records.

---

# PART D: AI DEVELOPMENT

## 19. AI Technology Standards

| Technology | Responsibility |
|---|---|
| Ollama | Local model runtime |
| LangChain | Model and tool integration |
| LangGraph | Workflow orchestration |
| Pydantic | Structured output validation |
| Sentence Transformers | Embeddings |
| pgvector | Vector search |

### AI Development Principles

1. Use AI only when it adds value.
2. Prefer deterministic logic for calculations.
3. Validate model outputs.
4. Keep prompts separate from application logic.
5. Restrict tool permissions.
6. Use structured schemas.
7. Test model outputs.
8. Avoid unnecessary LLM calls.
9. Track model and prompt versions.
10. Handle model failures gracefully.

---

## 20. Agent Development Guidelines

Every agent must have:

- A clear responsibility.
- Defined input.
- Defined output.
- Approved tools.
- Permission boundaries.
- Error handling.
- Evaluation tests.

### Agent Structure

```text
AGENT
 |
 +-- INPUT SCHEMA
 |
 +-- PROMPT
 |
 +-- APPROVED TOOLS
 |
 +-- MODEL EXECUTION
 |
 +-- OUTPUT VALIDATION
 |
 +-- RESULT
```

### Rules

- Do not create agents for simple calculations.
- Do not give unrestricted database access.
- Do not give unrestricted filesystem access.
- Do not allow arbitrary shell execution.
- Verify user ownership before retrieving data.
- Require approval for sensitive external actions.
- Keep agent execution traceable.

---

## 21. LangGraph Workflow Guidelines

Use LangGraph for multi-step workflows.

Examples:

- Resume Analysis Workflow.
- Job Analysis Workflow.
- Job Matching Workflow.
- Skill Gap Workflow.
- Career Roadmap Workflow.
- Interview Workflow.
- Career Copilot Workflow.

### Workflow Rules

- Define state schemas.
- Keep nodes focused.
- Validate state updates.
- Use conditional edges carefully.
- Set retry limits.
- Handle failures.
- Persist required workflow state.
- Avoid infinite loops.
- Test every node independently.
- Prevent duplicate side effects.

Use LangGraph for coordination, not as a replacement for normal backend business logic.

---

## 22. Prompt Engineering Guidelines

Store prompts separately from Python business logic.

Suggested structure:

```text
backend/
  app/
    ai/
      prompts/
        resume_analysis.txt
        resume_quality.txt
        job_analysis.txt
        matching_explanation.txt
        skill_gap.txt
        roadmap_generation.txt
        interview_feedback.txt
        copilot.txt
```

### Prompt Rules

- Clearly define the task.
- Specify expected output.
- Use structured response formats.
- Provide relevant context only.
- Include rules against inventing facts.
- Treat external content as untrusted.
- Avoid placing secrets in prompts.
- Version important prompt changes.
- Test prompts against fixed evaluation cases.

---

## 23. Model Management Guidelines

Initial model candidate:

`qwen2.5:3b`

### Rules

- Keep model configuration centralized.
- Avoid hardcoding model names throughout the codebase.
- Reuse configured model clients where practical.
- Monitor resource usage.
- Measure response time.
- Validate output quality.
- Handle unavailable models.
- Document model changes.

The initial development hardware has 24 GB RAM and 4 GB GPU VRAM. Test model performance on the actual machine before increasing model size.

---

# PART E: API AND INTEGRATION DEVELOPMENT

## 24. API Design Guidelines

Use REST APIs for frontend-backend communication.

### API Rules

- Use plural resource names.
- Use consistent endpoint structures.
- Use appropriate HTTP methods.
- Validate request and response data.
- Use pagination for large collections.
- Apply authentication to protected routes.
- Document endpoints.
- Version APIs when a breaking change requires it.

### Example API Structure

```text
/api/v1/
    |
    +-- auth/
    |
    +-- users/
    |
    +-- resumes/
    |
    +-- resume-analysis/
    |
    +-- jobs/
    |
    +-- companies/
    |
    +-- matching/
    |
    +-- skills/
    |
    +-- roadmaps/
    |
    +-- assessments/
    |
    +-- copilot/
    |
    +-- applications/
```

Keep API documentation aligned with the actual implemented endpoints.

---

## 25. External Integration Guidelines

Nexora AI may connect with:

- GitHub.
- Job listing providers.
- Email services.
- AI inference providers.
- Object storage.
- Monitoring tools.

### Rules

- Use dedicated integration services.
- Store credentials securely.
- Set timeouts.
- Handle API rate limits.
- Validate external responses.
- Retry transient failures carefully.
- Avoid depending on undocumented endpoints.
- Respect provider terms and access restrictions.
- Keep integrations replaceable.

---

# PART F: CODE QUALITY AND TESTING

## 26. Code Quality Standards

Code should be:

- Readable.
- Consistent.
- Modular.
- Testable.
- Secure.
- Documented where necessary.

### Python Tools

| Tool | Purpose |
|---|---|
| Ruff | Linting and formatting |
| Pytest | Testing |
| Coverage.py | Test coverage |
| Mypy | Optional static type checking |

Use Python type hints for important functions and service interfaces.

### JavaScript Tools

| Tool | Purpose |
|---|---|
| ESLint | Linting |
| Prettier | Formatting |
| Vitest | Testing |
| React Testing Library | Component testing |
| Playwright | E2E testing |

### Rules

- Avoid unused imports.
- Avoid dead code.
- Avoid unexplained constants.
- Avoid deeply nested logic.
- Use meaningful function names.
- Keep functions focused.
- Avoid unnecessary dependencies.

---

## 27. Testing Guidelines

Every feature should include suitable tests.

### Testing Levels

| Type | Purpose |
|---|---|
| Unit | Individual function testing |
| Integration | Connected module testing |
| API | Endpoint testing |
| Workflow | LangGraph execution testing |
| AI Evaluation | Model output quality |
| RAG | Retrieval quality |
| Security | Authorization and privacy |
| E2E | Complete user journeys |

### Rules

- Write tests alongside features.
- Test normal cases.
- Test invalid inputs.
- Test failure conditions.
- Mock external dependencies where appropriate.
- Use separate test databases.
- Never use production user data in routine tests.
- Run relevant regression tests after changes.

Refer to `TESTING_STRATEGY.md` for the complete testing approach.

---

# PART G: GIT AND COLLABORATION

## 28. Git Workflow

Use Git and GitHub for source control.

### Branch Strategy

```text
main
 |
 +-- develop
       |
       +-- feature/resume-upload
       |
       +-- feature/job-matching
       |
       +-- fix/auth-session
       |
       +-- docs/development-guidelines
```

### Branch Rules

| Branch | Purpose |
|---|---|
| main | Stable code |
| develop | Integration branch |
| feature/* | New functionality |
| fix/* | Bug fixes |
| docs/* | Documentation updates |
| refactor/* | Code restructuring |

For solo development, a simpler workflow using `main` and short-lived feature branches is also acceptable.

---

## 29. Commit Message Standards

Use clear commit messages.

Recommended format:

```text
type: short description
```

### Commit Types

| Type | Purpose |
|---|---|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation |
| refactor | Code restructuring |
| test | Test updates |
| style | Formatting |
| chore | Maintenance |
| perf | Performance improvement |
| security | Security improvement |

### Examples

```bash
git commit -m "feat: add resume upload"
git commit -m "fix: validate resume file size"
git commit -m "docs: add API documentation"
git commit -m "test: add resume parsing tests"
git commit -m "security: restrict resume access"
```

Keep commit messages in English.

---

## 30. Pull Request Guidelines

Before merging code:

- Review the changes.
- Run relevant tests.
- Check for secrets.
- Check for unnecessary dependencies.
- Update documentation.
- Review database migrations.
- Verify user permissions.
- Check frontend responsiveness.

### Pull Request Template

```text
## Summary

Describe the changes.

## Features

List implemented functionality.

## Testing

List tests performed.

## Security

Mention security-related changes.

## Screenshots

Add UI screenshots if relevant.

## Documentation

Mention updated documentation.
```

Even when working alone, use pull requests for larger changes when practical.

---

# PART H: ENVIRONMENT AND CONFIGURATION

## 31. Environment Management

Maintain separate development, test, and production environments.

| Environment | Purpose |
|---|---|
| Development | Feature development |
| Test | Automated tests |
| Staging | Pre-production testing |
| Production | Real users |

### Configuration Rules

- Use environment variables.
- Keep secrets out of Git.
- Use `.env.example`.
- Separate development and production databases.
- Never run destructive tests against production.
- Keep configuration centralized.

### Example `.env.example`

```env
APP_ENV=development
DEBUG=true

DATABASE_URL=

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

FRONTEND_URL=http://localhost:5173

SECRET_KEY=
```

This file should contain placeholders, never real credentials.

---

# PART I: DOCUMENTATION STANDARDS

## 32. Documentation Guidelines

Maintain documentation as the project evolves.

### Required Documents

```text
docs/
|
+-- PROJECT_OVERVIEW.md
+-- FEATURE_CATALOG.md
+-- DEVELOPMENT_ROADMAP.md
+-- TECH_STACK.md
+-- SYSTEM_ARCHITECTURE.md
+-- DATABASE_SCHEMA.md
+-- API_DOCUMENTATION.md
+-- AI_MODEL_STRATEGY.md
+-- UI_UX_GUIDELINES.md
+-- ENVIRONMENT_SETUP.md
+-- DATA_FLOW.md
+-- LANGCHAIN_LANGGRAPH.md
+-- RAG_ARCHITECTURE.md
+-- AI_AGENT_WORKFLOWS.md
+-- TESTING_STRATEGY.md
+-- DEPLOYMENT_GUIDE.md
+-- AUTHENTICATION_SECURITY.md
+-- PRIVACY_DATA_HANDLING.md
+-- DEVELOPMENT_GUIDELINES.md
```

### Documentation Rules

- Write in English.
- Use clear headings.
- Include examples where useful.
- Keep diagrams updated.
- Document architectural decisions.
- Update API documentation when endpoints change.
- Update database documentation when schema changes.
- Avoid documenting functionality that does not exist as completed functionality.

---

# PART J: AI CODING ASSISTANT GUIDELINES

## 33. Rules for AI Coding Assistants

AI coding assistants may help build Nexora AI, but their changes must follow project architecture and development rules.

### Before Writing Code

The assistant should:

1. Read the relevant documentation.
2. Understand the existing project structure.
3. Identify related modules.
4. Check current implementation.
5. Understand dependencies.
6. Identify affected tests.
7. Propose a focused implementation.

### During Development

The assistant should:

- Follow existing naming conventions.
- Reuse existing services.
- Avoid duplicate functionality.
- Keep frontend and backend separate.
- Validate API contracts.
- Add suitable tests.
- Handle errors.
- Respect authentication and privacy.
- Avoid unnecessary dependency changes.

### After Development

The assistant should:

1. Summarize changed files.
2. Explain implemented behavior.
3. List tests executed.
4. Report tests that failed.
5. Mention configuration changes.
6. Identify incomplete functionality.
7. Update relevant documentation.

### Strict Rules

- Do not rewrite the entire application for a small feature.
- Do not remove working functionality without approval.
- Do not invent API endpoints.
- Do not change the database schema without reviewing migrations.
- Do not hardcode secrets.
- Do not bypass authentication.
- Do not give AI agents unrestricted access.
- Do not claim tests passed unless they were executed successfully.
- Do not mark unfinished features as complete.

---

## 34. Feature Development Workflow

Every feature should follow the same implementation process.

```text
FEATURE REQUIREMENT
        |
        v
READ DOCUMENTATION
        |
        v
UNDERSTAND ARCHITECTURE
        |
        v
PLAN IMPLEMENTATION
        |
        v
DESIGN DATA FLOW
        |
        v
IMPLEMENT BACKEND
        |
        v
IMPLEMENT FRONTEND
        |
        v
WRITE TESTS
        |
        v
SECURITY REVIEW
        |
        v
UPDATE DOCUMENTATION
        |
        v
REVIEW AND COMMIT
```

Not every feature needs both frontend and backend changes. Implement only the layers required by its actual scope.

---

## 35. Definition of Done

A feature is complete only when the required work is implemented and verified.

### Feature Completion Checklist

- [ ] Requirement understood.
- [ ] Architecture followed.
- [ ] Code implemented.
- [ ] Input validation added.
- [ ] Authentication and authorization checked.
- [ ] Error handling implemented.
- [ ] Relevant tests written.
- [ ] Tests executed successfully.
- [ ] UI behavior verified where applicable.
- [ ] Documentation updated.
- [ ] No secrets committed.
- [ ] Code reviewed.

A feature should not be marked complete merely because the UI exists or an AI model returns an answer.

---

## 36. Final Development Principles

1. Use JavaScript for the frontend.
2. Use Python and FastAPI for the backend.
3. Use PostgreSQL as the main database.
4. Use SQLAlchemy and Alembic for database management.
5. Use LangChain for AI integrations.
6. Use LangGraph for multi-step AI workflows.
7. Use Ollama for local model development.
8. Keep deterministic business logic outside LLM prompts.
9. Enforce user data isolation.
10. Validate all inputs and outputs.
11. Write tests for every important feature.
12. Use Git for version control.
13. Keep project documentation updated.
14. Build modularly without premature complexity.
15. Prioritize security, reliability, and maintainability.

## 37. Final Development Principle

**Write code that is easy to understand, test, maintain, and extend. Build Nexora AI one verified feature at a time, without sacrificing security or architecture quality.**