# Battery-RAG Agent

Battery-RAG Agent is an online research assistant platform for lithium-ion battery, energy storage, BMS, control engineering, and AI research workflows.

This repository currently contains the project bootstrap only. It provides a monorepo scaffold, frontend and backend shells, local development infrastructure, and baseline documentation. It does not yet implement login, RAG, Agent workflows, or product business logic.

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
- The frontend and backend shells are started separately during development.
- The current scaffold is designed to support future authentication, RAG, Agent, and export changes without restructuring the repository.

## Bootstrap Startup

1. Copy `.env.example` to `.env` and adjust values if needed.
2. Start shared local services:

   ```bash
   docker compose up -d postgres redis qdrant
   ```

3. Start the frontend shell:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. Start the backend shell:

   ```bash
   cd backend
   uv sync
   uv run uvicorn app.main:app --reload
   ```

The bootstrap environment is intentionally limited to application shells and shared dependencies. No login, RAG, Agent, or database-backed business workflow is required to validate this stage.

## Planned Bootstrap Deliverables

- Frontend landing page placeholder
- Frontend dashboard placeholder
- Backend health check
- Docker Compose for PostgreSQL, Redis, and Qdrant
- Root `.env.example`

## Out of Scope For This Bootstrap

- Authentication and authorization flows
- Document upload and knowledge base ingestion
- RAG retrieval and chat
- Agent orchestration and skills execution
- Production deployment pipeline

## OpenSpec

Project-level source of truth lives under `openspec/specs/`.

Change artifacts for the bootstrap scaffold live under:

`openspec/changes/change-001-project-bootstrap/`
