# Backend Shell

This directory contains the Battery-RAG Agent backend bootstrap only.

Included in this change:

- FastAPI application shell
- baseline `app/` package structure
- system health endpoint at `/api/health`
- `uv`-managed Python environment

Explicitly excluded from this change:

- authentication and authorization
- document ingestion
- RAG retrieval and chat APIs
- Agent task execution
- database models and migrations
