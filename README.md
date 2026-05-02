# Battery-RAG Agent

Battery-RAG Agent is an online research assistant platform for lithium-ion battery, energy storage, BMS, control engineering, and AI research workflows.

This repository currently contains the project bootstrap plus the `change-002` auth and personal workspace foundation, and an in-progress `change-003` implementation for project-level local document storage. It provides a monorepo scaffold, frontend and backend shells, local development infrastructure, Cookie-based authentication, owner-scoped project workspace APIs, and local file storage foundations. It does not implement document parsing, embeddings, RAG, Agent workflows, or cloud object storage.

## Repository Structure

```text
.
├── frontend/   # Next.js + React + Tailwind CSS web shell
├── backend/    # FastAPI API shell
├── openspec/   # Product specs and change management artifacts
└── docker-compose.yml / .env.example / README.md
```

## Local Development Model

- `docker-compose.yml` provisions shared dependency services for local development.
- The frontend and backend applications are started separately on the host during development.
- PostgreSQL, Redis, and Qdrant run in Docker; for `change-003`, PostgreSQL is required by the application flow and local file uploads are stored on the host filesystem under the configured storage root.
- Authentication uses a backend-issued HttpOnly Cookie. The frontend never stores JWTs in `localStorage` or `sessionStorage` and sends authenticated requests with `credentials: "include"`.
- Uploaded files are stored locally under `STORAGE_ROOT`, and the storage directory must remain outside Git-tracked files.
- The current scaffold is designed to support future document, RAG, Agent, and export changes without restructuring the repository.

## Local Startup

1. Copy `.env.example` to `.env` and adjust values if needed.
2. Start shared local services:

   ```bash
   docker compose up -d postgres redis qdrant
   ```

3. Install frontend dependencies and start the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. Install backend dependencies with `uv` and start the backend:

   ```bash
   cd backend
   uv sync --all-groups
   uv run uvicorn app.main:app --reload
   ```

5. Open the app in your browser:

   - Frontend: `http://localhost:3000`
   - Backend health check: `http://localhost:8000/api/health`

6. Validate the implemented workspace and storage flow:

   - Register a user at `/register`
   - Log in at `/login`
   - Enter the authenticated dashboard at `/dashboard`
   - Create and list owner-scoped projects at `/projects`
   - Open the project document workspace at `/projects/:projectId`
   - Upload supported files (`PDF`, `TXT`, `MD`, `CSV`) to the selected project

## Required Environment Notes

- `JWT_SECRET` is required. The backend will fail to start if it is missing.
- `COOKIE_SECURE=false` is appropriate for local HTTP development. Set `COOKIE_SECURE=true` in production.
- `COOKIE_SAMESITE` defaults to `lax`.
- Leave `DATABASE_URL` empty to use the composed PostgreSQL settings, or set it explicitly to override the connection string.
- `BACKEND_CORS_ORIGINS` should include the frontend origin, such as `http://localhost:3000`.
- `STORAGE_ROOT` defaults to `storage` at the repository root.
- `MAX_UPLOAD_SIZE_BYTES` controls the upload ceiling enforced by the backend.
- `ALLOWED_UPLOAD_EXTENSIONS` and `ALLOWED_UPLOAD_MIME_TYPES` define the bounded local upload policy for this change.

## Implemented Scope So Far

- Frontend landing page placeholder
- Frontend login and registration pages
- Frontend authenticated dashboard workspace
- Frontend current-user project list, create-project form, and project detail placeholder
- Frontend project-level document upload, file list, and delete UI
- Backend health check
- Backend register, login, logout, and current-user endpoints
- Backend owner-scoped project create, list, detail, and delete APIs
- Backend owner-scoped document upload, list, detail, and delete APIs with local filesystem storage
- Docker Compose for PostgreSQL, Redis, and Qdrant
- Root `.env.example`

## Out of Scope

- Document parsing and knowledge base ingestion beyond raw file storage
- RAG retrieval and chat
- Agent orchestration and skills execution
- OCR and cloud object storage
- Third-party login, email verification, password reset, and payments
- Production deployment pipeline

## OpenSpec

Project-level source of truth lives under `openspec/specs/`.

Archived bootstrap artifacts live under `openspec/changes/archive/`.

The active change for the current implementation is:

`openspec/changes/change-003-document-upload-and-storage/`
