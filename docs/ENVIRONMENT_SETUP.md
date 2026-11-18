# ENVIRONMENT_SETUP.md

# Nexora AI: Development Environment Setup

## 1. Purpose

This document explains how to set up the complete local development environment for Nexora AI.

The setup covers:

- Frontend development.
- Backend development.
- PostgreSQL database.
- Local AI models using Ollama.
- LangChain and LangGraph.
- Embedding models.
- Git and GitHub.
- API testing.
- Environment variables.
- Running the complete application locally.

The initial development environment will use free and open-source tools wherever practical.

---

## 2. Development Environment

### Hardware

| Component | Specification |
|---|---|
| Operating System | Windows |
| RAM | 24 GB |
| GPU | NVIDIA RTX 2040 |
| GPU VRAM | 4 GB |
| Development Language | JavaScript and Python |
| AI Runtime | Ollama |

### Software Requirements

| Software | Purpose |
|---|---|
| Visual Studio Code | Code editor |
| Node.js | Frontend runtime |
| npm | JavaScript package manager |
| Python | Backend and AI development |
| pip | Python package manager |
| PostgreSQL | Main database |
| pgvector | Vector similarity search |
| Ollama | Local LLM runtime |
| Git | Version control |
| Postman | API testing |
| Docker Desktop | Optional database container management |

---

## 3. Recommended Project Location

Keep the project and model files away from the low-space system drive.

Recommended directory:

```text
D:/
|
+-- Projects/
|   |
|   +-- nexora-ai/
|
+-- AI-Models/
|   |
|   +-- ollama/
|
+-- Development/
    |
    +-- python-envs/
```

Create the directories using PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "D:\Projects"
New-Item -ItemType Directory -Force -Path "D:\AI-Models\ollama"
New-Item -ItemType Directory -Force -Path "D:\Development\python-envs"
```

Check available disk space:

```powershell
Get-PSDrive -PSProvider FileSystem
```

Keep enough free storage for:

- Python dependencies.
- Node dependencies.
- PostgreSQL data.
- Ollama models.
- Resume test documents.
- Application logs and temporary files.

Avoid downloading several large models before benchmarking the first model.

---

## 4. Install Visual Studio Code

Download:

https://code.visualstudio.com/

Install VS Code with the recommended options.

### Recommended Extensions

| Extension | Purpose |
|---|---|
| Python | Python development |
| Pylance | Python code intelligence |
| Python Debugger | Debugging |
| ESLint | JavaScript code quality |
| Prettier | Code formatting |
| Tailwind CSS IntelliSense | Tailwind support |
| ES7+ React Snippets | React development |
| PostgreSQL | Database assistance |
| GitLens | Git history |
| REST Client | API testing |
| Docker | Docker support |

Install only the extensions you need.

---

## 5. Install Node.js

Node.js is required for React, Vite, and frontend dependencies.

Download:

https://nodejs.org/

Use an active LTS release compatible with the selected Vite version.

### Verify Installation

Open PowerShell:

```powershell
node --version
npm --version
```

Expected baseline from the existing development environment:

```text
Node.js: v24.13.1
npm: 11.8.0
```

If these versions are already installed and working, there is no need to reinstall them.

### Configure npm Cache

```powershell
npm config set cache "D:\Development\npm-cache"
```

Verify:

```powershell
npm config get cache
```

---

## 6. Install Python

Python is required for FastAPI, NLP, machine learning, and AI workflows.

Download:

https://www.python.org/downloads/

Use Python 3.11 for the initial project environment.

During installation:

- Enable Add Python to PATH.
- Install pip.
- Install the Python launcher if available.

### Verify Installation

```powershell
python --version
py --version
pip --version
```

Expected baseline:

```text
Python 3.11.9
```

If Python 3.11 is already installed and working, keep it.

### Create a Virtual Environment

Move into the project:

```powershell
cd D:\Projects\nexora-ai
```

Create the environment:

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use this for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Verify:

```powershell
python --version
```

The active environment should use Python 3.11.

---

## 7. Create the Frontend

Technology:

- React.
- JavaScript.
- Vite.
- Tailwind CSS.
- Shadcn UI.

### Step 1: Create Vite Application

From the project root:

```powershell
npm create vite@latest frontend -- --template react
```

Move into the frontend:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start development server:

```powershell
npm run dev
```

Default address:

```text
http://localhost:5173
```

### Step 2: Install Frontend Packages

```powershell
npm install react-router-dom
npm install @tanstack/react-query
npm install react-hook-form
npm install zod
npm install @hookform/resolvers
npm install recharts
npm install lucide-react
npm install framer-motion
```

### Step 3: Install Tailwind CSS

Use the current Tailwind CSS Vite integration:

```powershell
npm install tailwindcss @tailwindcss/vite
```

Configure the Vite plugin in `vite.config.js`:

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
});
```

Add this to `src/index.css`:

```css
@import "tailwindcss";
```

### Step 4: Configure Shadcn UI

Follow the current JavaScript setup instructions:

https://ui.shadcn.com/docs/installation/vite

Initialize the project:

```powershell
npx shadcn@latest init
```

Add components as required:

```powershell
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add input
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
npx shadcn@latest add sidebar
npx shadcn@latest add table
npx shadcn@latest add progress
npx shadcn@latest add badge
npx shadcn@latest add tabs
```

The generated components should use JavaScript files where supported. Do not introduce TypeScript into the frontend.

---

## 8. Install PostgreSQL

PostgreSQL will store:

- User accounts.
- User profiles.
- Resumes.
- Resume analysis.
- Skills.
- Companies.
- Jobs.
- Job matches.
- Career roadmaps.
- Assessments.
- Applications.
- Copilot conversations.

Download:

https://www.postgresql.org/download/windows/

Install PostgreSQL using the official Windows installer.

During setup:

- Keep the default PostgreSQL service configuration unless you have a reason to change it.
- Set a strong database password.
- Remember the database port.
- Install pgAdmin if you want a graphical database manager.

Default local connection:

```text
Host: localhost
Port: 5432
Username: postgres
```

### Verify PostgreSQL

If `psql` is available in PowerShell:

```powershell
psql --version
```

Connect:

```powershell
psql -U postgres -h localhost -p 5432
```

Enter your database password when prompted.

### Create Nexora Database

Inside the PostgreSQL terminal:

```sql
CREATE DATABASE nexora_ai;
```

Connect:

```sql
\c nexora_ai
```

List databases:

```sql
\l
```

Exit:

```sql
\q
```

---

## 9. Install pgvector

pgvector enables vector similarity search inside PostgreSQL.

It will support:

- Resume semantic search.
- Job matching.
- Learning resource retrieval.
- Career Copilot context retrieval.

### Recommended Initial Approach

For Windows development, using a PostgreSQL container with pgvector can be easier than compiling the pgvector extension manually.

Docker is optional, but it is a practical option for the database.

Download Docker Desktop:

https://www.docker.com/products/docker-desktop/

Install and start Docker Desktop.

Check:

```powershell
docker --version
docker compose version
```

Create a `docker-compose.yml` file in the project root:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17
    container_name: nexora-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: nexora_ai
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - nexora_postgres_data:/var/lib/postgresql/data

volumes:
  nexora_postgres_data:
```

Create a `.env` file in the project root with a strong local password:

```env
POSTGRES_PASSWORD=replace_with_a_strong_local_password
```

Start PostgreSQL:

```powershell
docker compose up -d
```

Check the container:

```powershell
docker ps
```

Connect to the database:

```powershell
docker exec -it nexora-postgres psql -U postgres -d nexora_ai
```

Enable pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Verify:

```sql
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

Exit:

```sql
\q
```

**Important:** Use either the native PostgreSQL installation or the Docker PostgreSQL setup on port 5432. Do not run both on the same port at the same time.

Docker Desktop licensing should be checked against its current terms for your usage. The pgvector database image itself is open source.

---

## 10. Install Ollama

Ollama will run local language models without requiring paid AI APIs.

Download:

https://ollama.com/download/windows

Install Ollama for Windows.

### Verify Installation

```powershell
ollama --version
```

Check the local service:

```powershell
ollama list
```

Ollama normally provides its local API at:

```text
http://localhost:11434
```

### Configure Model Storage

Keep model downloads outside the low-space C drive.

Create the directory:

```powershell
New-Item -ItemType Directory -Force -Path "D:\AI-Models\ollama"
```

Set the model directory:

```powershell
setx OLLAMA_MODELS "D:\AI-Models\ollama"
```

Restart Ollama after setting the environment variable.

If Ollama is already running, quit it from the system tray before restarting it.

Verify that the environment variable is available in a new terminal:

```powershell
echo $env:OLLAMA_MODELS
```

### Download Initial Model

Start with one lightweight candidate:

```powershell
ollama pull qwen2.5:3b
```

Run it:

```powershell
ollama run qwen2.5:3b
```

Test:

```text
Explain what a resume-to-job matching system does.
```

Check downloaded models:

```powershell
ollama list
```

### Hardware Guidelines

With 24 GB RAM and 4 GB GPU VRAM:

- Begin with a 3B model.
- Test inference speed and memory use.
- Avoid loading multiple large models simultaneously.
- Test 7B models only after the initial setup works.
- Expect CPU offloading for larger models.
- Monitor GPU and RAM usage during inference.

The initial model is a candidate, not a final production decision.

---

## 11. Install Python Backend Dependencies

Create the backend directory:

```powershell
cd D:\Projects\nexora-ai
mkdir backend
cd backend
```

Create the Python environment if it has not already been created at the project root:

```powershell
cd ..
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
```

Create `requirements.txt`:

```text
fastapi
uvicorn[standard]
python-multipart
pydantic
pydantic-settings
sqlalchemy
alembic
psycopg[binary]
pgvector
pymupdf
python-docx
langchain
langchain-ollama
langgraph
sentence-transformers
scikit-learn
spacy
python-dotenv
httpx
pytest
```

Install:

```powershell
pip install -r requirements.txt
```

Some ML dependencies, especially PyTorch, may require platform-specific installation choices.

Do not force a CUDA build before verifying compatibility with your NVIDIA driver and Python environment.

For an initial CPU-based embedding test, allow Sentence Transformers to install its compatible dependencies. Add GPU acceleration only after testing.

### Verify Important Packages

```powershell
python -c "import fastapi, langchain, langgraph, sentence_transformers, sqlalchemy; print('Dependencies installed successfully')"
```

---

## 12. Configure FastAPI

Inside `backend`, create:

```text
backend/
|
+-- app/
|   |
|   +-- __init__.py
|   +-- main.py
|
+-- requirements.txt
```

Create `app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(
    title="Nexora AI API",
    description="AI-powered Career Intelligence Platform",
    version="0.1.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to Nexora AI API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }
```

Run the backend:

```powershell
uvicorn app.main:app --reload
```

Default backend address:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

---

## 13. Configure Environment Variables

Use environment variables to keep configuration separate from source code.

Suggested structure:

```text
nexora-ai/
|
+-- .env
+-- .env.example
+-- .gitignore
+-- docker-compose.yml
+-- frontend/
+-- backend/
+-- docs/
```

### Example `.env.example`

```env
APP_NAME=Nexora AI
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/nexora_ai

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

UPLOAD_DIR=./storage/resumes
MAX_UPLOAD_SIZE_MB=10
```

Create your local `.env` from this template and replace the database password.

Do not commit `.env` to GitHub.

The frontend should use only public configuration values. Never expose database credentials, private keys, or model service secrets through Vite environment variables.

### Backend Configuration

Use Pydantic Settings to read environment variables.

Example:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nexora AI"
    app_env: str = "development"

    database_url: str

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
```

---

## 14. Configure Git

Download:

https://git-scm.com/downloads

Verify:

```powershell
git --version
```

Configure your Git identity:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

Replace these values with your own Git identity.

### Initialize Repository

From the project root:

```powershell
cd D:\Projects\nexora-ai
git init
```

Create `.gitignore`:

```gitignore
# Environment variables
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Node
node_modules/
dist/

# Logs
*.log

# Database and local storage
storage/
uploads/
*.db

# IDE
.vscode/

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
```

Make the first commit:

```powershell
git add .
git commit -m "Initialize Nexora AI project"
```

Create a GitHub repository and connect it:

```powershell
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git branch -M main
git push -u origin main
```

Never commit API keys, passwords, private resumes, model files, or database dumps.

---

## 15. Configure Frontend API Connection

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Create an API service:

```text
frontend/
    src/
        services/
            api.js
```

Example `api.js`:

```javascript
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error("Unable to connect to the backend");
  }

  return response.json();
}
```

Use the API service instead of writing repeated fetch calls throughout page components.

---

## 16. Configure Database Connection

Install the required database packages:

```powershell
pip install sqlalchemy psycopg[binary] alembic
```

Create:

```text
backend/
    app/
        database/
            __init__.py
            connection.py
```

Example `connection.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
```

Create database models separately.

Use Alembic for schema migrations instead of manually modifying production database tables.

Initialize Alembic later, after the first SQLAlchemy models are ready:

```powershell
alembic init migrations
```

---

## 17. Configure AI Model Connection

Create:

```text
backend/
    app/
        ai/
            __init__.py
            ollama_client.py
```

Example `ollama_client.py`:

```python
from langchain_ollama import ChatOllama

from app.config import settings


llm = ChatOllama(
    model=settings.ollama_model,
    base_url=settings.ollama_base_url,
    temperature=0.2,
)


def generate_response(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content
```

Test the model after starting Ollama.

Do not call the LLM directly from frontend components. All AI requests should go through the backend.

---

## 18. Recommended Project Structure

The initial project structure:

```text
nexora-ai/
|
+-- frontend/
|   |
|   +-- public/
|   +-- src/
|   |   +-- assets/
|   |   +-- components/
|   |   +-- pages/
|   |   +-- services/
|   |   +-- hooks/
|   |   +-- routes/
|   |   +-- utils/
|   |   +-- App.jsx
|   |   +-- main.jsx
|   |
|   +-- package.json
|
+-- backend/
|   |
|   +-- app/
|   |   +-- api/
|   |   +-- core/
|   |   +-- database/
|   |   +-- models/
|   |   +-- schemas/
|   |   +-- services/
|   |   +-- ai/
|   |   +-- workflows/
|   |   +-- utils/
|   |   +-- config.py
|   |   +-- main.py
|   |
|   +-- migrations/
|   +-- tests/
|   +-- requirements.txt
|
+-- docs/
|   +-- PROJECT_OVERVIEW.md
|   +-- FEATURE_CATALOG.md
|   +-- DEVELOPMENT_ROADMAP.md
|   +-- TECH_STACK.md
|   +-- SYSTEM_ARCHITECTURE.md
|   +-- DATABASE_SCHEMA.md
|   +-- API_DOCUMENTATION.md
|   +-- AI_MODEL_STRATEGY.md
|   +-- UI_UX_GUIDELINES.md
|   +-- ENVIRONMENT_SETUP.md
|
+-- storage/
|
+-- .env.example
+-- .gitignore
+-- docker-compose.yml
+-- README.md
```

---

## 19. Run Nexora AI Locally

Open three PowerShell terminals.

### Terminal 1: Database

If using Docker PostgreSQL:

```powershell
cd D:\Projects\nexora-ai
docker compose up -d
```

If using native PostgreSQL, ensure its Windows service is running instead.

### Terminal 2: Backend

```powershell
cd D:\Projects\nexora-ai
.\.venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --reload
```

### Terminal 3: Frontend

```powershell
cd D:\Projects\nexora-ai\frontend
npm run dev
```

Ensure Ollama is running in the background.

### Local Application URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Backend Health | http://localhost:8000/health |
| Ollama API | http://localhost:11434 |
| PostgreSQL | localhost:5432 |

---

## 20. Verify the Complete Environment

Use this checklist after setup.

### Development Tools

- [ ] VS Code installed.
- [ ] Node.js installed.
- [ ] npm working.
- [ ] Python 3.11 installed.
- [ ] Python virtual environment working.
- [ ] Git installed.

### Frontend

- [ ] React application created.
- [ ] Vite development server working.
- [ ] Tailwind CSS configured.
- [ ] Shadcn UI initialized.
- [ ] Frontend opens successfully.

### Backend

- [ ] FastAPI installed.
- [ ] Backend starts successfully.
- [ ] Health endpoint works.
- [ ] API documentation opens.

### Database

- [ ] PostgreSQL running.
- [ ] Nexora database created.
- [ ] Backend database connection works.
- [ ] pgvector extension enabled.

### AI Environment

- [ ] Ollama installed.
- [ ] Ollama API responding.
- [ ] Initial LLM downloaded.
- [ ] LangChain installed.
- [ ] LangGraph installed.
- [ ] Embedding package installed.
- [ ] AI test request works.

### Project Management

- [ ] Git initialized.
- [ ] `.gitignore` configured.
- [ ] `.env` excluded from Git.
- [ ] GitHub repository connected.

---

## 21. Common Problems and Solutions

### Problem 1: Python Command Not Found

Check:

```powershell
py --version
```

If the Python launcher works, use:

```powershell
py -3.11 -m venv .venv
```

Otherwise, verify that Python is installed and added to PATH.

### Problem 2: PowerShell Blocks Virtual Environment

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Problem 3: PostgreSQL Connection Failed

Check:

- PostgreSQL service is running.
- Port 5432 is available.
- Database name is correct.
- Username and password are correct.
- The connection URL uses the correct driver.

### Problem 4: pgvector Extension Not Found

Check whether the PostgreSQL installation includes pgvector.

If using Docker, confirm that the container uses the pgvector image.

### Problem 5: Ollama Model Not Found

Check:

```powershell
ollama list
```

Download the model:

```powershell
ollama pull qwen2.5:3b
```

### Problem 6: Ollama Runs Slowly

Possible causes:

- GPU memory limitations.
- CPU offloading.
- Large context size.
- Other applications consuming RAM.
- Multiple model requests running simultaneously.

Start with a smaller model and a shorter context.

### Problem 7: Frontend Cannot Connect to Backend

Check:

- Backend is running.
- API URL is correct.
- CORS is configured.
- Frontend environment variables are correct.
- The frontend server was restarted after changing `.env`.

---

## 22. Security and Development Rules

1. Never commit `.env`.
2. Never expose database credentials in frontend code.
3. Validate uploaded PDF and DOCX files.
4. Limit upload size.
5. Store uploaded resumes outside publicly accessible directories.
6. Validate all API inputs.
7. Keep AI model access inside the backend.
8. Use database migrations.
9. Avoid logging passwords or private resume content.
10. Use separate development and production configurations.
11. Do not run untrusted code directly in the backend.
12. Back up important database data.

---

## 23. Free Development Strategy

The initial development environment should avoid paid APIs and unnecessary hosting costs.

| Component | Initial Approach |
|---|---|
| Code Editor | VS Code |
| Frontend | React + Vite |
| Backend | FastAPI |
| Database | Local PostgreSQL |
| Vector Search | pgvector |
| LLM | Ollama |
| Embeddings | Sentence Transformers |
| AI Workflows | LangChain + LangGraph |
| Version Control | Git + GitHub |
| API Testing | Postman or REST Client |
| Development | Local machine |

### Important Deployment Note

A local Ollama model is not automatically available to a publicly hosted FastAPI backend.

For a public demo, Nexora AI will need an appropriate model-hosting strategy.

Possible future approaches:

- Host the backend and AI model on a machine you control.
- Use a suitable free-tier compute provider if its current limits support the workload.
- Run a reduced AI feature set in the public demo.
- Introduce an optional hosted model provider later.

Do not assume that a free hosting tier can run Ollama and a database reliably.

---

## 24. Final Setup Goal

After completing this document, the development machine should be able to run:

- React frontend.
- FastAPI backend.
- PostgreSQL database.
- pgvector.
- Ollama local LLM.
- LangChain and LangGraph workflows.
- Local embedding generation.

**Final Goal:** Establish a stable, free-first local development environment for building Nexora AI before moving toward public deployment and production infrastructure.