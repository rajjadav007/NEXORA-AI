# Nexora AI

Nexora AI is an AI-powered career intelligence platform designed to help students, freshers, internship seekers, and early-career professionals make confident, data-driven career decisions.

By connecting resume intelligence, job description parsing, market research, skill-gap analysis, and personalized roadmaps, Nexora AI bridges the gap between candidate preparation and employer expectations.

---

## 🏗️ Repository Architecture

Modular monorepo separating frontend presentation from backend API services:

```text
nexora-ai/
  frontend/          # React (Vite, Tailwind CSS, Shadcn UI)
  backend/           # FastAPI (Python 3.11, SQLAlchemy, Alembic)
  docs/              # Architectural specifications and PRD
  scripts/           # Local development scripts
  .gitignore         # Unified git ignore rules
  .env.example       # Global environment example
  README.md          # Project documentation
```

---

## 🚀 Quickstart

### Prerequisites
- Node.js (v18+) & npm
- Python (3.11+)

### Backend Setup
1. Navigate to backend:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
5. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Interactive API documentation available at `http://localhost:8000/docs`.

### Frontend Setup
1. Navigate to frontend:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Run the Vite development server:
   ```bash
   npm run dev
   ```
   Application runs on `http://localhost:3000`.

---

## 📚 Project Documentation

Detailed system documentation is located in [`docs/`](./docs):
- [Architecture Guide](./docs/ARCHITECTURE.md)
- [Project Overview](./docs/PROJECT_OVERVIEW.md)
- [System Architecture](./docs/SYSTEM_ARCHITECTURE.md)
- [PRD](./docs/PRD.md)
- [API Documentation](./docs/API_DOCUMENTATION.md)
- [Database Schema](./docs/DATABASE_SCHEMA.md)
- [Tech Stack](./docs/TECH_STACK.md)

---

## 📄 License
This project is licensed under the terms defined in the repository.
