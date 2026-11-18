# DEPLOYMENT_GUIDE.md

# Nexora AI: Deployment Guide

## 1. Purpose

This document explains how to deploy Nexora AI from local development to a publicly accessible application.

It covers:

- Local development setup.
- Frontend deployment.
- Backend deployment.
- PostgreSQL deployment.
- pgvector configuration.
- Ollama model hosting.
- Environment variables.
- Docker configuration.
- CI/CD.
- Production security.
- Monitoring and logging.
- Free deployment limitations.

The initial goal is to develop Nexora AI using free and open-source tools.

Paid infrastructure should only be considered when the application has real users and a validated need for additional resources.

---

## 2. Deployment Architecture

Nexora AI uses a modular architecture with separate frontend, backend, database, and AI components.

### Local Development Architecture

```text
                 DEVELOPER
                     |
                     v
              REACT + VITE
                PORT 5173
                     |
                     v
                FASTAPI
                PORT 8000
                     |
          +----------+----------+
          |          |          |
          v          v          v
      POSTGRESQL   OLLAMA    LANGGRAPH
       PORT 5432   PORT 11434  WORKFLOWS
          |          |
          v          v
       PGVECTOR    LOCAL LLM
```

### Public Deployment Architecture

```text
                   USERS
                     |
                     v
                FRONTEND
               HTTPS HOST
                     |
                     v
                FASTAPI
              BACKEND HOST
                     |
          +----------+----------+
          |          |          |
          v          v          v
      DATABASE    AI SERVICE   FILE STORAGE
     PostgreSQL    HOSTED OR    PRIVATE
      + pgvector    REMOTE      STORAGE
```

The public frontend and backend communicate through HTTPS APIs.

The database must not be directly exposed to public users.

---

## 3. Deployment Strategy

Use three deployment stages.

| Stage | Environment | Goal |
|---|---|---|
| Stage 1 | Local Development | Build and test all features |
| Stage 2 | Public Demo | Make the application accessible online |
| Stage 3 | Production | Support real users securely and reliably |

### Stage 1: Local Development

Run the following locally:

- React frontend.
- FastAPI backend.
- PostgreSQL.
- pgvector.
- Ollama.
- LangChain.
- LangGraph.

This is the primary development environment.

### Stage 2: Public Demo

Deploy:

- React frontend to a static hosting provider.
- FastAPI backend to a free or low-cost hosting provider.
- PostgreSQL to a hosted database provider.
- File storage to private object storage if needed.

For AI inference, choose one of these approaches:

1. Keep Ollama on the local development machine for local demonstrations.
2. Use a separately hosted AI inference service.
3. Deploy a smaller model on suitable infrastructure.

A local Ollama instance is not automatically accessible to the public internet.

### Stage 3: Production

Introduce:

- Dedicated application hosting.
- Managed PostgreSQL.
- Private file storage.
- Reliable AI inference infrastructure.
- Monitoring.
- Backups.
- Automated deployments.
- Rate limiting.
- Security monitoring.

---

## 4. Technology and Hosting Options

The following providers are candidates. Free tiers, limits, and availability can change, so verify current terms before deployment.

### 4.1 Frontend Hosting

| Provider | Purpose | Free Option |
|---|---|---|
| Vercel | React frontend | Available with limits |
| Netlify | Static frontend | Available with limits |
| Cloudflare Pages | Static frontend | Available with limits |
| GitHub Pages | Static websites | Available with limitations |

**Initial recommendation:** Vercel or Cloudflare Pages.

### 4.2 Backend Hosting

| Provider | Purpose | Free Option |
|---|---|---|
| Render | FastAPI hosting | Limited free options, subject to availability |
| Hugging Face Spaces | AI application demos | Free CPU resources with limitations |
| Railway | Backend hosting | Check current trial and pricing |
| Fly.io | Application hosting | Check current pricing and credits |

Free backend services may sleep, have limited RAM, restrict execution time, or impose monthly usage limits.

**Important:** Do not assume that every provider offers permanent free backend hosting.

### 4.3 Database Hosting

| Provider | Purpose |
|---|---|
| Neon | Hosted PostgreSQL |
| Supabase | PostgreSQL and additional services |
| Self-hosted PostgreSQL | Full local control |

Check pgvector availability, storage limits, connection limits, backups, and free-tier restrictions before choosing a provider.

**Initial recommendation:** Neon or Supabase, after confirming the required pgvector support and limits.

### 4.4 AI Model Hosting

| Option | Purpose |
|---|---|
| Local Ollama | Local development |
| Self-hosted Ollama | Dedicated machine inference |
| Hugging Face Inference | Hosted model inference, subject to plan limits |
| Other hosted inference providers | Remote AI inference |

For the initial project, use local Ollama.

Do not make the public backend depend on a personal laptop that may be switched off or disconnected.

---

## 5. Local Development Deployment

### 5.1 Required Software

Install:

- Node.js.
- Python 3.11.
- PostgreSQL.
- Ollama.
- Git.
- VS Code.

Optional:

- Docker Desktop.
- Postman.
- pgAdmin.

### 5.2 Project Structure

```text
nexora-ai/
|
+-- frontend/
|   |
|   +-- src/
|   +-- public/
|   +-- package.json
|   +-- vite.config.js
|
+-- backend/
|   |
|   +-- app/
|   +-- tests/
|   +-- requirements.txt
|   +-- main.py
|
+-- docs/
|
+-- .gitignore
+-- README.md
```

### 5.3 Start Frontend

```bash
cd frontend

npm install

npm run dev
```

Default development address:

```text
http://localhost:5173
```

### 5.4 Start Backend

```bash
cd backend

python -m venv venv
```

Windows activation:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend address:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

### 5.5 Start PostgreSQL

Start your local PostgreSQL service and verify that the database is available.

Example connection:

```text
postgresql://username:password@localhost:5432/nexora_db
```

If using Docker for PostgreSQL, do not run another PostgreSQL instance on the same host port.

### 5.6 Start Ollama

Install Ollama and pull the initial model candidate:

```bash
ollama pull qwen2.5:3b
```

Run the model:

```bash
ollama run qwen2.5:3b
```

Ollama's default local API address:

```text
http://localhost:11434
```

Test the local API:

```bash
curl http://localhost:11434/api/tags
```

Use the model only after verifying that it runs reliably on your available RAM and GPU.

---

## 6. Docker Deployment

Docker can make the development environment more consistent.

For the initial project, containerize PostgreSQL and optionally the backend.

Ollama can remain installed directly on the host machine.

### 6.1 Example Docker Compose

Create:

`docker-compose.yml`

```yaml
services:
  db:
    image: pgvector/pgvector:pg17
    container_name: nexora-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: nexora_db
      POSTGRES_USER: nexora_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nexora_user -d nexora_db"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

This example uses a PostgreSQL 17 pgvector image. Verify the selected image tag and compatibility before using it.

### 6.2 Start Database

```bash
docker compose up -d
```

Check running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs db
```

Stop containers:

```bash
docker compose down
```

Stopping containers does not remove the named database volume.

### 6.3 Enable pgvector

Connect to the database and execute:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Verify:

```sql
SELECT extname
FROM pg_extension
WHERE extname = 'vector';
```

Never expose the database port publicly in a production deployment.

---

## 7. Environment Configuration

Use environment variables for configuration.

Never hardcode credentials or secrets in source code.

### 7.1 Backend Environment

Create:

`backend/.env`

```env
APP_NAME=Nexora AI
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql://nexora_user:your_password@localhost:5432/nexora_db

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

FRONTEND_URL=http://localhost:5173

SECRET_KEY=replace_with_a_secure_random_secret

MAX_UPLOAD_SIZE_MB=10
```

These are example development values. Generate secure secrets and configure production values separately.

### 7.2 Frontend Environment

Create:

`frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Vite exposes variables prefixed with `VITE_` to frontend code.

Never place database passwords, private API keys, or server secrets in frontend environment variables.

### 7.3 Production Environment

Production configuration should include:

```env
APP_ENV=production
DEBUG=false

DATABASE_URL=your_production_database_url

OLLAMA_BASE_URL=your_ai_service_url
OLLAMA_MODEL=your_selected_model

FRONTEND_URL=https://your-frontend-domain.com

SECRET_KEY=your_production_secret
```

Only set an AI service URL that is actually deployed and protected.

Do not use a public unauthenticated Ollama endpoint.

### 7.4 Git Ignore

Add the following to `.gitignore`:

```gitignore
.env
.env.*
!.env.example

venv/
.venv/
__pycache__/
*.pyc

node_modules/
dist/

.pytest_cache/
.coverage
htmlcov/

uploads/
storage/

*.log
```

Review the rules before committing so required example configuration and source files remain tracked.

---

## 8. Frontend Deployment

### Option A: Vercel

1. Push the project to GitHub.
2. Open Vercel.
3. Import the GitHub repository.
4. Select the frontend directory as the project root.
5. Configure the build command.
6. Configure the output directory.
7. Add the production API URL.
8. Deploy.

Typical Vite settings:

| Setting | Value |
|---|---|
| Framework | Vite |
| Root Directory | frontend |
| Build Command | npm run build |
| Output Directory | dist |

Add:

```env
VITE_API_BASE_URL=https://your-backend-domain.com/api
```

After deployment, verify:

- Homepage loads.
- Navigation works.
- API calls reach the backend.
- Authentication works.
- Resume upload works.
- Dashboard data loads.

### Option B: Cloudflare Pages

1. Connect GitHub.
2. Select the frontend project.
3. Configure the frontend root.
4. Set the build command to `npm run build`.
5. Set the output directory to `dist`.
6. Configure environment variables.
7. Deploy.

Check SPA routing and fallback behavior for direct page refreshes.

---

## 9. Backend Deployment

FastAPI must be hosted on infrastructure that supports Python application processes.

### 9.1 Production Server

Use Uvicorn or an appropriate ASGI server configuration.

Example:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

For a provider with a different port configuration, follow its deployment requirements.

### 9.2 Backend Deployment Steps

1. Push backend code to GitHub.
2. Create a backend service.
3. Select Python as the runtime.
4. Configure the backend root directory.
5. Install requirements.
6. Configure environment variables.
7. Configure the startup command.
8. Connect PostgreSQL.
9. Deploy.
10. Test the health endpoint.

### 9.3 Requirements

Your backend must:

- Use production configuration.
- Disable debug mode.
- Validate all incoming data.
- Use secure authentication.
- Configure CORS.
- Use database migrations.
- Handle model timeouts.
- Return consistent API errors.
- Avoid exposing internal stack traces.

### 9.4 CORS Configuration

Example:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Replace the example domain with the actual deployed frontend domain.

Do not use unrestricted CORS in production.

---

## 10. PostgreSQL Deployment

The database stores:

- User accounts.
- User profiles.
- Resumes.
- Resume analysis.
- Skills.
- Companies.
- Jobs.
- Match results.
- Skill gaps.
- Career roadmaps.
- Assessments.
- Conversations.
- Applications.
- Embeddings.

### 10.1 Hosted Database Setup

1. Create a PostgreSQL database.
2. Check pgvector support.
3. Copy the connection string.
4. Store it in backend environment variables.
5. Configure database access.
6. Run Alembic migrations.
7. Verify database connectivity.

### 10.2 Enable pgvector

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 10.3 Database Migration

Run:

```bash
alembic upgrade head
```

Verify the migration state:

```bash
alembic current
```

### 10.4 Production Database Rules

- Use a private or restricted connection.
- Use strong credentials.
- Enable backups.
- Limit database permissions.
- Avoid public database access.
- Use connection pooling where appropriate.
- Monitor database usage.
- Test restoration procedures.

Do not rely on a free-tier database as the only copy of important production data.

---

## 11. Ollama and AI Deployment

This is one of the most important parts of Nexora AI deployment.

### 11.1 Local AI Development

During development:

```text
FastAPI
   |
   v
Ollama
   |
   v
Local Qwen Model
```

Backend configuration:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

This works when FastAPI and Ollama run on the same machine.

### 11.2 Public Deployment Limitation

When FastAPI is deployed to a cloud provider, `localhost` refers to the backend container or server.

It does not refer to your personal Lenovo laptop.

Therefore:

```text
PUBLIC BACKEND
      |
      v
localhost:11434
```

will not connect to Ollama running on your laptop.

### 11.3 Available Deployment Approaches

| Approach | Description | Recommendation |
|---|---|---|
| Local Ollama | Run the complete app locally | Best for development |
| Remote Ollama | Run Ollama on a dedicated server | Suitable with sufficient resources |
| Hosted Inference | Connect to an external model provider | Suitable for public demos |
| Smaller Hosted Model | Deploy a model on suitable hosting | Depends on available resources |

### 11.4 Recommended Initial Strategy

Use local Ollama for development and testing.

For a public demo, deploy the backend with an explicitly configured hosted inference provider or another reachable AI service.

If no suitable free inference service is available, deploy the non-AI application features first and keep AI functionality available locally.

Do not expose your personal Ollama API directly to the public internet without a secure access layer.

### 11.5 AI Service Abstraction

Create an AI service interface so the application can switch between local and hosted inference.

Example:

```python
class AIService:

    def generate(self, prompt: str):
        raise NotImplementedError
```

Implement separate providers:

```text
AIService
    |
    +-- OllamaService
    |
    +-- HostedInferenceService
```

This prevents the application from depending on one model provider.

---

## 12. File Storage Deployment

Nexora AI processes uploaded resumes.

Production file storage should not depend on temporary server storage.

### 12.1 Development

Use local storage:

```text
backend/
  uploads/
    resumes/
```

### 12.2 Production

Use private object storage.

Possible options include:

- Cloudflare R2.
- Supabase Storage.
- Other S3-compatible storage providers.

Check pricing, free-tier allowances, request limits, and data retention rules.

### 12.3 File Storage Security

- Store files privately.
- Validate uploaded files.
- Restrict file size.
- Generate safe storage keys.
- Do not trust user-supplied filenames.
- Use signed URLs when appropriate.
- Restrict access to file owners.
- Define retention and deletion policies.
- Never expose uploaded resume directories publicly.

---

## 13. Domain and HTTPS

A production application should use HTTPS.

Example:

```text
https://nexora.example.com
```

Possible domain setup:

```text
Frontend:
https://nexora.example.com

Backend:
https://api.nexora.example.com
```

Configure:

- DNS records.
- HTTPS certificates.
- Frontend API URL.
- Backend CORS.
- Secure cookie settings, if using cookie-based authentication.

A custom domain is optional for the initial public demo.

---

## 14. CI/CD Deployment

Use GitHub Actions to automate testing and deployment.

### 14.1 CI/CD Workflow

```text
Developer Pushes Code
         |
         v
      GitHub
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
    Build Checks
         |
         v
   Tests Passed?
         |
    +----+----+
    |         |
    v         v
   Yes       No
    |         |
    v         v
 Deploy     Stop
```

### 14.2 Recommended Checks

Frontend:

```bash
npm ci
npm run build
npm run test
```

Backend:

```bash
pip install -r requirements.txt
pytest
```

Run linting and migration checks as part of the workflow.

### 14.3 Deployment Automation

Configure hosting providers to deploy from the main branch only after successful checks.

Protect production secrets in the hosting provider's secret manager.

Never place production credentials directly in GitHub workflow files.

---

## 15. Monitoring and Logging

Production deployment requires visibility into application behavior.

### 15.1 Application Logging

Record:

- API request failures.
- Authentication failures.
- Database errors.
- AI model errors.
- Workflow failures.
- Processing duration.
- Background task failures.

### 15.2 Monitoring Tools

Possible options:

| Tool | Purpose |
|---|---|
| Python Logging | Application logs |
| Sentry | Error monitoring |
| OpenTelemetry | Tracing and metrics |
| Provider Logs | Hosting diagnostics |
| PostgreSQL Monitoring | Database health |

Check free-tier limits before selecting monitoring services.

### 15.3 AI Monitoring

Measure:

- Model response time.
- Token generation speed.
- Model availability.
- Invalid output frequency.
- Workflow failure rate.
- Resource usage.

Avoid logging full resumes, private prompts, passwords, or sensitive user information.

---

## 16. Production Security Checklist

### Application Security

- [ ] Debug mode disabled.
- [ ] HTTPS enabled.
- [ ] Secure secrets configured.
- [ ] CORS restricted.
- [ ] Input validation enabled.
- [ ] Rate limiting configured.
- [ ] Authentication enabled.
- [ ] Authorization enforced.

### Database Security

- [ ] Database access restricted.
- [ ] Strong credentials configured.
- [ ] User data isolation tested.
- [ ] Backups configured.
- [ ] Restore procedure tested.
- [ ] Database permissions restricted.

### AI Security

- [ ] Agent tools restricted.
- [ ] Prompt injection protections implemented.
- [ ] RAG access filters enforced.
- [ ] Sensitive data minimized.
- [ ] Model endpoint protected.
- [ ] External actions require user approval.

### File Security

- [ ] File type validation enabled.
- [ ] File size limits configured.
- [ ] Files stored privately.
- [ ] Ownership checks enforced.
- [ ] Deletion policy implemented.

---

## 17. Free Deployment Plan

The initial goal is to keep costs at zero where possible.

### Suggested Architecture

| Component | Initial Option |
|---|---|
| Frontend | Vercel or Cloudflare Pages |
| Backend | Available free Python hosting |
| Database | Neon or Supabase free tier |
| Vector Search | pgvector |
| AI Development | Local Ollama |
| File Storage | Local during development, eligible free object storage for demo |
| Source Control | GitHub |
| CI/CD | GitHub Actions |
| Monitoring | Provider logs and eligible free monitoring tools |

### Important Limitations

Free hosting can have:

- Sleep or inactivity limits.
- Monthly compute limits.
- Storage limits.
- Database connection limits.
- Request limits.
- Restricted background processing.
- Limited GPU availability.
- No guaranteed uptime.

A completely free public deployment with a reliable, continuously available local LLM is not guaranteed.

For the initial public demo, keep the application lightweight and deploy only the features that the selected infrastructure can support.

---

## 18. Deployment Troubleshooting

| Problem | Possible Cause | Solution |
|---|---|---|
| Frontend cannot connect to API | Incorrect API URL | Check environment variables |
| CORS error | Backend origin not configured | Update CORS settings |
| Database connection fails | Incorrect URL or credentials | Verify database configuration |
| pgvector extension error | Extension unavailable | Check database provider support |
| Ollama connection error | Localhost points to cloud server | Configure reachable AI service |
| Application sleeps | Free hosting restriction | Check provider plan |
| Upload fails | File size or storage restriction | Verify limits |
| Migration fails | Schema conflict | Inspect Alembic migration history |
| AI request times out | Model too slow or server overloaded | Reduce prompt size or improve inference resources |
| Deployment build fails | Missing dependency or configuration | Inspect build logs |

---

## 19. Deployment Checklist

### Before Deployment

- [ ] Frontend tests pass.
- [ ] Backend tests pass.
- [ ] Database migrations work.
- [ ] Environment variables are configured.
- [ ] Secrets are removed from source code.
- [ ] AI provider is configured.
- [ ] File storage is configured.
- [ ] API health endpoint works.

### During Deployment

- [ ] Deploy frontend.
- [ ] Deploy backend.
- [ ] Connect PostgreSQL.
- [ ] Run migrations.
- [ ] Configure HTTPS.
- [ ] Configure CORS.
- [ ] Configure AI service.
- [ ] Configure storage.

### After Deployment

- [ ] Open public frontend.
- [ ] Test registration and login.
- [ ] Test resume upload.
- [ ] Test resume analysis.
- [ ] Test job matching.
- [ ] Test database persistence.
- [ ] Test AI responses.
- [ ] Test error handling.
- [ ] Verify logs.
- [ ] Verify backups.

---

## 20. Recommended Nexora AI Deployment Roadmap

### Phase 1: Local Deployment

- Install dependencies.
- Run frontend.
- Run backend.
- Connect PostgreSQL.
- Enable pgvector.
- Configure Ollama.
- Verify core workflows.

**Deliverable:** Fully working local application.

### Phase 2: Public Demo

- Deploy frontend.
- Deploy backend.
- Configure hosted PostgreSQL.
- Configure private file storage.
- Configure reachable AI inference.
- Test public access.

**Deliverable:** Publicly accessible demonstration.

### Phase 3: Production Preparation

- Configure domain.
- Enable HTTPS.
- Harden authentication.
- Configure backups.
- Add monitoring.
- Test performance.
- Complete security review.

**Deliverable:** Production-ready deployment candidate.

### Phase 4: Production Launch

- Configure production infrastructure.
- Run final tests.
- Apply database migrations.
- Deploy application.
- Verify monitoring.
- Establish backup and recovery procedures.

**Deliverable:** Nexora AI production release.

---

## 21. Final Deployment Decisions

| Area | Initial Decision |
|---|---|
| Frontend | React + Vite |
| Frontend Hosting | Vercel or Cloudflare Pages |
| Backend | FastAPI |
| Backend Hosting | Suitable Python hosting provider |
| Database | PostgreSQL |
| Vector Database | pgvector |
| AI Runtime | Local Ollama for development |
| AI Model | Qwen 2.5 3B initial candidate |
| AI Framework | LangChain + LangGraph |
| File Storage | Local development, private object storage in production |
| CI/CD | GitHub Actions |
| Monitoring | Application logs and error monitoring |
| Deployment Strategy | Local first, public demo second, production later |

These are initial choices, not a commitment to a particular provider. Verify current free-tier availability and technical limits before deployment.

## 22. Final Principle

**Build locally, validate thoroughly, deploy a small public demo, and move to production infrastructure only when the product needs it.**

Nexora AI should remain modular so that frontend hosting, backend hosting, databases, storage, and AI inference can be changed independently without rewriting the entire application.