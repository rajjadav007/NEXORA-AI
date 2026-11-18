# Nexora AI
# Technology Stack

**Document:** TECH_STACK.md  
**Project:** Nexora AI  
**Version:** 1.0  
**Status:** Proposed  
**Development Approach:** Free and Open-Source First  
**AI Approach:** Local AI Models

---

# 1. Technology Stack Overview

Nexora AI will use a modular technology stack consisting of frontend, backend, database, AI engine, document processing, and deployment layers.

The architecture separates application logic from AI processing so that individual components can be developed, tested, and upgraded independently.

## 1.1 Complete Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend Framework | React.js | Build the user interface |
| Programming Language | JavaScript | Frontend development |
| Build Tool | Vite | Frontend development and bundling |
| Styling | Tailwind CSS | Application styling |
| UI Components | Shadcn UI | Reusable interface components |
| Routing | React Router | Frontend navigation |
| API Client | Axios | Communicate with backend |
| Backend Language | Python | Backend and AI development |
| Backend Framework | FastAPI | REST API development |
| Data Validation | Pydantic | Validate API data |
| ORM | SQLAlchemy | Database operations |
| Database | PostgreSQL | Store structured application data |
| Database Migration | Alembic | Manage schema changes |
| AI Model Runtime | Ollama | Run local language models |
| AI Framework | LangChain | Model and retrieval integration |
| Agent Orchestration | LangGraph | Manage multi-step AI workflows |
| Embedding Models | Sentence Transformers | Convert text into vectors |
| Vector Search | pgvector | Store and search embeddings in PostgreSQL |
| Document Processing | PyMuPDF | Extract PDF text |
| DOCX Processing | python-docx | Extract DOCX content |
| Backend Testing | Pytest | Test backend functionality |
| Frontend Testing | Vitest | Test frontend functionality |
| UI Testing | React Testing Library | Test React components |
| Version Control | Git | Track code changes |
| Repository Hosting | GitHub | Store source code |
| Containerization | Docker | Package application services |
| Local Development | Windows | Development environment |

---

# 2. Frontend Technology Stack

## 2.1 React.js

**Purpose:** Build the Nexora AI frontend.

Responsibilities:

- Build reusable UI components.
- Create dashboard pages.
- Manage application state.
- Display AI-generated reports.
- Build forms and interactive interfaces.
- Connect with backend APIs.

Why React:
- Component-based architecture.
- Large ecosystem.
- Reusable components.
- Suitable for dashboard applications.
- Strong community support.

Official Documentation: https://react.dev/

## 2.2 JavaScript

**Purpose:** Main programming language for frontend development.

Responsibilities:

- Application logic.
- API communication.
- Component interactions.
- Data transformation.
- Form handling.

Project decision:

Use JavaScript instead of TypeScript for the initial implementation.

## 2.3 Vite

**Purpose:** Frontend development server and build tool.

Responsibilities:

- Start the development server.
- Bundle frontend code.
- Manage development builds.
- Optimize production assets.

Why Vite:
- Fast development startup.
- Simple configuration.
- React support.
- Efficient production builds.

Official Documentation: https://vite.dev/

## 2.4 Tailwind CSS

**Purpose:** Style the application.

Responsibilities:

- Responsive layouts.
- Spacing and typography.
- Colors and backgrounds.
- Component styling.
- Responsive dashboard design.

Official Documentation: https://tailwindcss.com/

## 2.5 Shadcn UI

**Purpose:** Provide reusable interface components.

Components may include:

- Buttons.
- Cards.
- Dialogs.
- Dropdowns.
- Tables.
- Forms.
- Tabs.
- Progress bars.
- Tooltips.
- Sidebar components.

Why Shadcn UI:
- Customizable components.
- Works with React.
- Integrates with Tailwind CSS.
- Suitable for dashboard interfaces.

Official Documentation: https://ui.shadcn.com/

## 2.6 React Router

**Purpose:** Manage frontend navigation.

Example application routes:

- `/dashboard`
- `/resume`
- `/resume/analysis`
- `/jobs`
- `/companies`
- `/matching`
- `/skill-gaps`
- `/career-readiness`
- `/roadmap`
- `/assessments`
- `/copilot`
- `/applications`
- `/settings`

Official Documentation: https://reactrouter.com/

## 2.7 Axios

**Purpose:** Handle frontend-to-backend HTTP communication.

Responsibilities:

- Send API requests.
- Handle API responses.
- Manage request errors.
- Configure authentication headers.
- Centralize API communication.

Official Documentation: https://axios-http.com/

---

# 3. Backend Technology Stack

## 3.1 Python

**Purpose:** Main backend and AI programming language.

Responsibilities:

- Backend business logic.
- Resume processing.
- AI integrations.
- Job matching.
- Skill analysis.
- Data processing.
- Assessment evaluation.

Why Python:
- Strong AI and machine learning ecosystem.
- Easy integration with NLP libraries.
- Good support for document processing.
- Compatible with FastAPI and LangChain.

Official Documentation: https://www.python.org/

## 3.2 FastAPI

**Purpose:** Build backend REST APIs.

Responsibilities:

- API endpoints.
- Request handling.
- Response generation.
- Authentication integration.
- Data validation.
- API documentation.

Why FastAPI:
- High-performance API framework.
- Python type validation support.
- Automatic API documentation.
- Async support.
- Easy integration with AI libraries.

Official Documentation: https://fastapi.tiangolo.com/

## 3.3 Pydantic

**Purpose:** Validate and structure incoming and outgoing data.

Responsibilities:

- Request validation.
- Response validation.
- Structured AI output validation.
- Data serialization.
- Configuration management.

Official Documentation: https://docs.pydantic.dev/

## 3.4 SQLAlchemy

**Purpose:** Connect backend services with PostgreSQL.

Responsibilities:

- Database models.
- Database queries.
- Relationships.
- Transactions.
- Data persistence.

Official Documentation: https://www.sqlalchemy.org/

## 3.5 Alembic

**Purpose:** Manage database schema changes.

Responsibilities:

- Create database migrations.
- Update existing tables.
- Track schema versions.
- Apply and reverse migrations.

Official Documentation: https://alembic.sqlalchemy.org/

---

# 4. Database Technology Stack

## 4.1 PostgreSQL

**Purpose:** Main relational database.

Nexora AI will use PostgreSQL to store structured application information.

Expected data:

- Users.
- User profiles.
- Resumes.
- Resume versions.
- Extracted resume information.
- Education records.
- Experience records.
- Skills.
- Projects.
- Certifications.
- Job descriptions.
- Companies.
- Job listings.
- Matching results.
- Skill gaps.
- Career readiness results.
- Learning roadmaps.
- Assessments.
- Application tracking.
- AI conversation metadata.

Why PostgreSQL:
- Relational database support.
- Reliable data storage.
- Strong query capabilities.
- Suitable for structured application data.
- Supports JSON data types.
- Supports vector search through pgvector.

Official Documentation: https://www.postgresql.org/

## 4.2 pgvector

**Purpose:** Store and search vector embeddings inside PostgreSQL.

Potential use cases:

- Resume semantic search.
- Job description similarity.
- Skill similarity.
- Learning resource retrieval.
- Career knowledge retrieval.

Why pgvector:
- Integrates with PostgreSQL.
- Avoids introducing a separate vector database initially.
- Supports vector similarity search.
- Suitable for an initial development environment.

Official Repository: https://github.com/pgvector/pgvector

**Decision:** Use PostgreSQL with pgvector for the initial implementation. Evaluate a separate vector database only if scale or performance requires it.

---

# 5. AI and Machine Learning Stack

## 5.1 Ollama

**Purpose:** Run local language models without depending on paid model APIs.

Responsibilities:

- Run local LLMs.
- Generate structured outputs.
- Analyze resume content.
- Understand job descriptions.
- Generate recommendations.
- Support career copilot conversations.

Why Ollama:
- Local model execution.
- No per-request API charges.
- Simple model management.
- Supports multiple open models.

Official Website: https://ollama.com/

## 5.2 Initial Local Model Strategy

The initial model selection will prioritize models that can run within the available hardware.

| Model | Potential Use | Priority |
|---|---|---|
| Qwen2.5 3B Instruct | General AI tasks and structured extraction | Initial candidate |
| Qwen2.5 7B Instruct | Better reasoning and analysis | Secondary candidate |
| Llama 3.2 3B | General conversation and assistant tasks | Alternative |
| EmbeddingGemma | Text embeddings and semantic retrieval | Initial candidate |

Model availability and compatibility must be checked before installation.

**Hardware consideration:**

The development machine has:

- 24 GB RAM.
- NVIDIA RTX 2040 GPU.
- 4 GB GPU VRAM.

A quantized 3B model is a reasonable starting point. A 7B model may require CPU and system RAM offloading, depending on quantization and context size.

The application must not assume that the full model will fit in GPU memory.

Official Ollama Model Library: https://ollama.com/library

## 5.3 LangChain

**Purpose:** Connect language models with application tools and retrieval systems.

Responsibilities:

- Model integration.
- Prompt templates.
- Output parsing.
- Embedding integration.
- Document processing workflows.
- Retrieval pipelines.

Potential use cases:

- Resume analysis.
- Job description analysis.
- Skill extraction.
- Career recommendation generation.
- AI copilot.

Official Documentation: https://docs.langchain.com/

## 5.4 LangGraph

**Purpose:** Build stateful, multi-step AI workflows.

Responsibilities:

- Define AI workflow steps.
- Manage workflow state.
- Connect multiple AI operations.
- Handle conditional execution.
- Support retries and validation.
- Manage human review steps.

Potential Nexora AI workflows:

**Resume Analysis Workflow**

1. Receive resume text.
2. Extract resume information.
3. Validate extracted fields.
4. Analyze resume quality.
5. Generate recommendations.
6. Save analysis results.

**Job Matching Workflow**

1. Load candidate profile.
2. Load job requirements.
3. Normalize skills.
4. Compare candidate and job data.
5. Calculate matching score.
6. Generate match explanation.

**Career Roadmap Workflow**

1. Load career goal.
2. Retrieve candidate skills.
3. Identify skill gaps.
4. Prioritize missing skills.
5. Recommend learning resources.
6. Generate roadmap.
7. Validate roadmap output.

Official Documentation: https://docs.langchain.com/oss/python/langgraph/overview

**Decision:** Use LangGraph only where workflows need multiple connected steps, state, branching, or human review. Simple operations should remain ordinary backend services.

---

# 6. Embedding and Vector Search Stack

## 6.1 Sentence Transformers

**Purpose:** Convert text into numerical embeddings.

Potential use cases:

- Resume similarity.
- Job description similarity.
- Skill similarity.
- Semantic search.
- Learning resource retrieval.

Official Documentation: https://sbert.net/

## 6.2 EmbeddingGemma

**Purpose:** Initial candidate for local text embedding generation.

Potential use cases:

- Convert resume sections into embeddings.
- Convert job descriptions into embeddings.
- Retrieve relevant career information.
- Support semantic matching.

The selected embedding model must be evaluated for language support, embedding dimensions, speed, and retrieval quality.

## 6.3 pgvector

**Purpose:** Store and retrieve embeddings in PostgreSQL.

Example retrieval flow:

1. Convert a resume section into an embedding.
2. Store the embedding in PostgreSQL.
3. Convert a job requirement into an embedding.
4. Search for similar resume sections.
5. Return relevant matches.
6. Use the retrieved content in the analysis.

---

# 7. Document Processing Stack

## 7.1 PyMuPDF

**Purpose:** Extract text from PDF resumes.

Responsibilities:

- Read PDF files.
- Extract text.
- Access page information.
- Handle supported document structures.

Official Documentation: https://pymupdf.readthedocs.io/

## 7.2 python-docx

**Purpose:** Extract content from DOCX resumes.

Responsibilities:

- Read paragraphs.
- Extract tables.
- Process document text.
- Access document structure.

Official Documentation: https://python-docx.readthedocs.io/

## 7.3 Document Processing Flow

**Resume Upload → File Validation → PDF/DOCX Extraction → Text Cleaning → Structured Extraction → AI Analysis → Database Storage**

The system should preserve the original document and record processing errors where extraction fails.

Scanned PDFs may require an OCR component in a later implementation. OCR is not assumed to be available in the initial text-extraction pipeline.

---

# 8. Testing Stack

## 8.1 Pytest

**Purpose:** Test backend services and APIs.

Testing areas:

- API endpoints.
- Database operations.
- Resume processing.
- AI output validation.
- Job matching.
- Skill gap analysis.
- Authentication and permissions.

Official Documentation: https://docs.pytest.org/

## 8.2 Vitest

**Purpose:** Test frontend JavaScript logic and components.

Testing areas:

- Utility functions.
- React components.
- API service functions.
- State and interaction logic.

Official Documentation: https://vitest.dev/

## 8.3 React Testing Library

**Purpose:** Test React components from the user's perspective.

Testing areas:

- Form interactions.
- Navigation.
- Dashboard components.
- Loading and error states.
- User workflows.

Official Documentation: https://testing-library.com/docs/react-testing-library/intro/

---

# 9. Development and Version Control Tools

| Tool | Purpose |
|---|---|
| Visual Studio Code | Code editor |
| Git | Version control |
| GitHub | Repository hosting |
| Postman | API testing |
| Docker | Containerization |
| Ollama | Local AI model runtime |
| PostgreSQL | Local database |
| pgAdmin | Database management interface |
| Python Virtual Environment | Backend dependency isolation |
| npm | Frontend package management |

Official Resources:

- VS Code: https://code.visualstudio.com/
- Git: https://git-scm.com/
- GitHub: https://github.com/
- Postman: https://www.postman.com/
- Docker: https://www.docker.com/
- pgAdmin: https://www.pgadmin.org/

---

# 10. Proposed Application Architecture

The application will contain four main layers.

## 10.1 Frontend Layer

**Technology:** React + JavaScript + Vite

Responsibilities:

- User interface.
- Dashboard.
- Resume upload.
- Job search.
- Analysis reports.
- Career roadmap.
- AI copilot interface.

## 10.2 Backend Layer

**Technology:** Python + FastAPI

Responsibilities:

- API endpoints.
- Authentication integration.
- Business logic.
- Database operations.
- File management.
- Communication with the AI engine.

## 10.3 AI Engine Layer

**Technology:** Ollama + LangChain + LangGraph

Responsibilities:

- Resume intelligence.
- Job description analysis.
- Skill extraction.
- Semantic matching.
- Career recommendations.
- AI copilot.
- Multi-step AI workflows.

## 10.4 Database Layer

**Technology:** PostgreSQL + pgvector

Responsibilities:

- User information.
- Resume data.
- Job data.
- Company data.
- Analysis results.
- Skill information.
- Roadmaps.
- Assessment results.
- Embeddings.

---

# 11. Proposed Project Directory Structure

```text
Nexora-AI/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── context/
│   │   ├── utils/
│   │   ├── routes/
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── middleware/
│   │   └── main.py
│   ├── tests/
│   ├── alembic/
│   └── requirements.txt
│
├── ai-engine/
│   ├── models/
│   ├── prompts/
│   ├── chains/
│   ├── graphs/
│   ├── embeddings/
│   ├── retrieval/
│   ├── agents/
│   ├── workflows/
│   └── utils/
│
├── database/
│   ├── migrations/
│   ├── schemas/
│   └── seed/
│
├── docs/
│
├── scripts/
│
├── tests/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

The directory structure may evolve as modules become more complex. Avoid creating unnecessary empty directories before their implementation is required.

---

# 12. Environment Configuration

The application must use environment variables for configuration.

Example backend configuration:

```env
APP_NAME=Nexora AI
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/nexora_ai

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

SECRET_KEY=replace_with_a_secure_random_value
```

Example frontend configuration:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Important rules:

- Never commit real secrets to GitHub.
- Keep `.env` out of version control.
- Maintain `.env.example` with placeholder values.
- Use separate configurations for development and production.
- Validate required environment variables during application startup.

---

# 13. Free and Open-Source Development Strategy

The initial development should avoid paid services wherever practical.

| Requirement | Initial Choice | Cost Approach |
|---|---|---|
| Frontend | React + Vite | Free |
| UI | Tailwind + Shadcn UI | Free |
| Backend | FastAPI | Free |
| Database | PostgreSQL | Free locally |
| AI Models | Ollama | Free local execution |
| AI Workflows | LangChain + LangGraph | Open-source |
| Embeddings | Local embedding model | Free local execution |
| Vector Search | pgvector | Open-source |
| Document Processing | PyMuPDF + python-docx | Free libraries |
| Version Control | Git | Free |
| Repository | GitHub | Free plan |
| Local Testing | Pytest + Vitest | Free |

**Important:** Free local development does not automatically mean free public hosting. Public deployment, storage, database hosting, and GPU inference may have usage limits or charges. Deployment choices must be verified separately before launch.

---

# 14. Technology Selection Principles

Every technology selected for Nexora AI should follow these principles:

1. Prefer free and open-source tools.
2. Prefer local execution for AI models.
3. Keep hardware requirements practical.
4. Avoid unnecessary infrastructure complexity.
5. Choose technologies with active documentation and community support.
6. Keep frontend, backend, AI, and database modules independent.
7. Use modular integrations so components can be replaced later.
8. Evaluate performance before adding new infrastructure.
9. Avoid adding a new framework without a clear requirement.
10. Document important technology changes.

---

# 15. Initial Technology Setup Priority

Install and configure technologies in this order.

| Order | Technology | Setup Priority |
|---:|---|---|
| 1 | Python | Required |
| 2 | Node.js and npm | Required |
| 3 | Git | Required |
| 4 | VS Code | Required |
| 5 | PostgreSQL | Required |
| 6 | React + Vite | Required |
| 7 | FastAPI | Required |
| 8 | Tailwind CSS | Required |
| 9 | Shadcn UI | Required |
| 10 | Ollama | Required for local AI |
| 11 | LangChain | AI development |
| 12 | LangGraph | Multi-step AI workflows |
| 13 | pgvector | Semantic search |
| 14 | Docker | Optional initially |
| 15 | Testing tools | Introduce with feature development |

Do not install every AI library at the beginning. Add dependencies when their corresponding phase requires them.

---

# 16. Final Technology Stack Decision

The initial technology stack for Nexora AI is:

**Frontend:** React + JavaScript + Vite + Tailwind CSS + Shadcn UI

**Backend:** Python + FastAPI + Pydantic + SQLAlchemy

**Database:** PostgreSQL + pgvector + Alembic

**AI Engine:** Ollama + LangChain + LangGraph

**Embeddings:** Sentence Transformers / EmbeddingGemma, subject to evaluation

**Document Processing:** PyMuPDF + python-docx

**Testing:** Pytest + Vitest + React Testing Library

**Development Tools:** VS Code + Git + GitHub + Postman

**Containerization:** Docker, introduced when needed

This stack provides a modular foundation for developing Nexora AI as a local-first AI career intelligence platform, with the option to move selected components to hosted infrastructure when required.

**Technology decisions should be reviewed during development, but changes must be documented and must not unnecessarily increase project complexity.**