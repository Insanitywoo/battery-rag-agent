# Battery-RAG Agent Architecture Spec

## Purpose

This document defines the project-level technical architecture and boundary decisions for Battery-RAG Agent.

## Architecture Principles

- Web-first product, not a local-only demo.
- Clear separation between frontend, backend, storage, and asynchronous processing.
- Project-scoped retrieval and generation as the default execution model.
- Multi-user isolation must be designed into every layer, not added later.
- Model providers and external tools must be abstracted behind internal services.

## System Context

```text
Browser
  -> Next.js frontend
  -> FastAPI backend
  -> Service layer
     -> PostgreSQL
     -> Qdrant
     -> Object storage
     -> Redis
     -> Celery workers
     -> LLM gateway
     -> Approved external tools
```

## Technology Stack

### Frontend

- Next.js with App Router
- React
- Tailwind CSS

### Backend

- FastAPI
- Python service layer
- SQLAlchemy or SQLModel for relational persistence
- Alembic for migrations

### Data and Infrastructure

- PostgreSQL for relational data
- Qdrant for vector retrieval
- Redis for queueing and short-lived state
- Celery for long-running async tasks
- Object storage via local storage in development and MinIO or S3-compatible storage in deployment

### AI and Retrieval

- Internal LLM gateway abstraction over supported providers
- Embedding provider abstraction
- Project-scoped retrieval pipeline with optional reranking

## Core Subsystems

### Frontend

Owns:

- auth flows,
- dashboard and project navigation,
- document upload UX,
- chat and source rendering,
- agent task submission and status,
- export download surfaces.

Frontend must not contain provider secrets, direct vector access, or trust-sensitive business rules.

### Backend API

Owns:

- authentication,
- authorization,
- request validation,
- orchestration entry points,
- persistence,
- quota enforcement,
- download authorization.

### Ingestion and Knowledge Base

Owns:

- file validation,
- document parsing,
- chunking,
- embedding,
- vector writes,
- knowledge base rebuilds and reindex tasks.

### RAG Service

Owns:

- retrieval filters,
- prompt assembly,
- evidence packaging,
- answer and source contract,
- abstention when evidence is insufficient.

### Agent Service

Owns:

- task routing,
- skill selection,
- plan execution,
- result aggregation,
- task status persistence.

### Export Service

Owns:

- markdown export in MVP,
- artifact persistence,
- controlled access to generated files.

## Multi-User Data Isolation Principles

Every persisted or retrievable artifact must be scoped by ownership metadata.

### Required Ownership Fields

- `user_id` for all user-owned records
- `project_id` for all project-bound records

### Isolation Rules

- All API handlers must resolve and authorize project ownership before returning project data.
- Documents, chunks, chat sessions, messages, exports, and agent tasks must inherit project ownership.
- Retrieval requests must filter by both `user_id` and `project_id`, or use a per-project collection with equivalent guarantees.
- File download paths must never be directly exposed as public URLs without authorization checks.

### Preferred Vector Isolation

The default design target is one Qdrant collection per project in early versions because it is operationally simple and easy to reason about.

If a shared collection strategy is adopted later, payload filtering by `user_id` and `project_id` becomes mandatory and must be covered by tests.

## Data Flow Summary

### Document Ingestion

1. User uploads a document into a project.
2. Backend stores the original file and creates a document record.
3. Async worker parses the file and produces chunks.
4. Chunks are embedded and written to Qdrant with ownership metadata.
5. Document and knowledge base status are updated.

### RAG Chat

1. User sends a question within a project chat.
2. Backend authorizes project access.
3. RAG service retrieves relevant chunks from the project scope only.
4. Prompt is built using retrieved evidence and answer constraints.
5. Assistant response and sources are stored and returned.

### Agent Task

1. User submits a task within a project.
2. Backend authorizes project access and creates a task record.
3. Agent router selects task type and required skills.
4. Worker executes skills and persists intermediate and final results.
5. Output artifact is stored and exposed through authorized download or view APIs.

## System Boundary Decisions

### Inside The Platform

- Identity and ownership enforcement
- Document ingestion and retrieval
- Evidence-grounded generation
- Structured agent workflows
- Export generation and storage

### Outside The Platform

- Raw provider SDK usage from frontend
- Arbitrary code execution by end users
- Unrestricted internet crawling in the MVP
- Public sharing of project data by default

## Operational Constraints

- Long-running tasks must be asynchronous.
- Failures must be observable through task status and logs.
- Secrets must be injected through environment variables only.
- Architecture should support local development via Docker Compose.

## MVP Architecture Scope

The MVP must include:

- frontend, backend, PostgreSQL, Qdrant, Redis, Celery worker, and local or S3-compatible object storage.

The MVP may defer:

- autoscaling,
- microservice decomposition,
- advanced observability stack,
- distributed tracing,
- billing infrastructure.
