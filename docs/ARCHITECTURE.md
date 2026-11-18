# Nexora AI - System Architecture & Directory Structure

## 1. Overview
Nexora AI is organized as a modular monorepo containing decoupled frontend and backend services.

## 2. Repository Layout

```
nexora-ai/
  frontend/          # React (Vite, Tailwind CSS, Shadcn UI)
  backend/           # FastAPI (Python 3.11, SQLAlchemy, Alembic)
  docs/              # Architectural, PRD, and operational specifications
  scripts/           # Automation and dev helper scripts
  .gitignore         # Unified repository ignore rules
  .env.example       # Global environment variable documentation
  README.md          # Project overview and quickstart
```

## 3. Frontend Architecture (`frontend/`)

- **Tech Stack:** React, JavaScript (ES6+), Vite, Tailwind CSS, React Router.
- **Directory Breakdown:**
  - `public/`: Static public assets.
  - `src/assets/`: Media and static graphics bundled via Vite.
  - `src/components/common/`: Shared, generic presentation components.
  - `src/components/layout/`: Header, sidebar, footer components.
  - `src/components/ui/`: Base UI primitives (Shadcn-compatible).
  - `src/config/`: Frontend environment and application config.
  - `src/hooks/`: Custom reusable React hooks.
  - `src/layouts/`: Route layout wrappers.
  - `src/pages/`: Page-level route views.
  - `src/routes/`: Route declarations and navigation guards.
  - `src/services/`: HTTP API client layer.
  - `src/styles/`: Global styles and Tailwind imports.
  - `src/utils/`: Helper functions (e.g. `cn` class combiner).

## 4. Backend Architecture (`backend/`)

- **Tech Stack:** Python 3.11, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL.
- **Directory Breakdown:**
  - `app/api/v1/`: Versioned API routers and endpoint handlers.
  - `app/core/`: Application settings, environment parsing, and security foundations.
  - `app/database/`: Database engine, session lifecycle, and declarative base.
  - `app/models/`: SQLAlchemy ORM database models.
  - `app/schemas/`: Pydantic models for validation and serialization.
  - `app/services/`: Pure business logic (decoupled from transport/HTTP).
  - `app/repositories/`: Data access layer isolating raw database queries.
  - `app/utils/`: Backend helper functions.
  - `tests/`: Automated unit and integration test suites.
  - `alembic/`: Database schema migration scripts.

## 5. Architectural Principles

1. **Separation of Concerns:** Business logic belongs in `services/`, database operations in `repositories/`, and HTTP mechanics in `api/`.
2. **Schema & Model Isolation:** Pydantic schemas validate boundaries; SQLAlchemy models define persistent database state.
3. **Centralized Configuration:** All variables pass through `core/config.py` using `pydantic-settings`.
4. **Feature-Ready:** Future features (Resume Intelligence, Job Discovery, Roadmaps, Copilot) mount cleanly into `api/v1/`, `services/`, and `models/` without refactoring core scaffolding.
