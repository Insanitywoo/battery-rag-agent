# Battery-RAG Agent

Battery-RAG Agent is an online research assistant platform for lithium-ion battery, energy storage, control engineering, and AI research workflows. The current repository includes the project bootstrap, authentication and owner-scoped workspace, project document upload and ingestion, project-level vector knowledge-base build, streaming RAG chat, a bounded Agent plus Skills framework for project-scoped research tasks, an evidence-first paper writing assistant, and a bounded external-references workspace for Crossref/arXiv metadata plus draft BibTeX export.

## Repository Structure

```text
.
|- frontend/          # Next.js + React + Tailwind CSS web app
|- backend/           # FastAPI API service
|- openspec/          # Product source of truth and change history
|- docker-compose.yml
|- .env.example
`- README.md
```

## Current Scope

- User registration, login, logout, and current-user session with HttpOnly Cookie auth
- Owner-scoped project create, list, detail, and delete flows
- Project-level document upload, local file storage, list, detail, and delete flows
- Synchronous document ingestion for PDF, TXT, MD, and CSV preview handling
- Chunk persistence in PostgreSQL
- Project vector knowledge-base build and rebuild
- Qdrant payloads filtered by `user_id` and `project_id`
- Project-scoped chat sessions and messages
- Backend-only LLM gateway configuration
- Streaming RAG chat endpoint and frontend streaming chat UI
- Citation persistence with `document_id`, `document_name`, `page_number`, `chunk_id`, `chunk_index`, and `excerpt`
- Project-scoped Agent routing and structured Skills execution
- Agent task persistence with `agent_tasks`
- Structured outputs for `research_qa`, `paper_summary`, `multi_paper_compare`, `literature_review`, `writing_outline`, and `evidence_check`
- Paper writing assistant with saved `writing_artifacts`
- Writing tasks for outline, introduction outline, related work, method framework, conclusion draft, citation check, and Markdown export
- Evidence-first writing outputs that persist markdown content, sources, and unsupported claims per owner and project
- Project-scoped external reference search against Crossref and arXiv from explicit user-entered queries
- Curated `external_references` persistence with owner and project lineage
- Draft BibTeX export for saved external references
- Bounded Agent and writing reuse of saved external references under explicit `external reference` labeling

## Still Out of Scope

- OCR, image parsing, and complex table extraction
- Rerank, BM25, and hybrid retrieval
- Embedding queues or Celery-style async workers
- Third-party login, email verification, password reset, billing, and payments
- Semantic Scholar integration, web-scale crawling, PDF download, and full-text scraping
- Complex multi-step autonomous ReAct workflows

## Local Development Model

- `docker-compose.yml` provisions PostgreSQL, Redis, and Qdrant for local development.
- The frontend and backend run on the host machine during development.
- Authentication uses a backend-issued HttpOnly Cookie. The frontend never stores JWTs in `localStorage` or `sessionStorage`.
- Protected frontend requests use `credentials: "include"`.
- Uploaded files are stored locally under `STORAGE_ROOT`.
- Vector build, chat, and Agent execution are owner-scoped and project-scoped.
- Model keys stay on the backend only.
- External provider calls use only explicit user-entered keyword, title, or DOI input from the External References workspace.
- Saved external references remain separate from uploaded-document chunks, embeddings, and vector knowledge-base state.

## Environment Variables

Copy `.env.example` to `.env` and adjust values as needed.

Important settings:

- `JWT_SECRET` is required.
- `COOKIE_SECURE=false` is appropriate for local HTTP development.
- `DATABASE_URL` may be left empty to derive from the PostgreSQL compose settings.
- `STORAGE_ROOT` defaults to `storage`.
- `QDRANT_URL` defaults to `http://127.0.0.1:6333`.
- `QDRANT_COLLECTION_NAME` controls the shared vector collection name.
- `LLM_PROVIDER=mock` is the easiest local default for bounded development and smoke checks.
- Set `LLM_PROVIDER` plus `LLM_API_BASE_URL`, `LLM_API_KEY`, `LLM_CHAT_MODEL`, and `LLM_EMBEDDING_MODEL` to use a real backend model provider.
- `RAG_TOP_K`, `RAG_MIN_SIMILARITY`, and `CHAT_HISTORY_LIMIT` control retrieval and prompt assembly.
- `AGENT_ENABLE_LLM_ROUTING=false` keeps Agent routing rules-only by default.
- `AGENT_MIN_PROMPT_CHARACTERS`, `AGENT_MAX_CLAIMS`, and `AGENT_MAX_COMPARISON_DOCUMENTS` control bounded Agent execution behavior.
- `EXTERNAL_TOOL_USER_AGENT` sets the backend-only outbound user-agent header for external metadata providers.
- `EXTERNAL_SEARCH_TIMEOUT_SECONDS` bounds provider request time.
- `CROSSREF_MAILTO` is optional but recommended when using Crossref heavily.

## Local Startup

1. Copy `.env.example` to `.env`.
2. Start shared dependency services:

   ```bash
   docker compose up -d postgres redis qdrant
   ```

3. Start the backend with `uv`:

   ```bash
   cd backend
   uv sync --all-groups
   uv run --no-sync uvicorn app.main:app --reload
   ```

4. Start the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. Open:

   - Frontend: `http://localhost:3000`
   - Backend health check: `http://localhost:8000/api/health`
   - Backend docs: `http://localhost:8000/docs`

## Suggested Manual Validation Flow

1. Register at `/register`.
2. Log in at `/login`.
3. Open `/projects` and create a project.
4. Open the project workspace at `/projects/:projectId`.
5. Upload a supported file.
6. Process the document into chunks.
7. Build or rebuild the project vector DB.
8. Open `/projects/:projectId/chat`.
9. Create a chat session and ask a project-scoped question.
10. Confirm the answer streams in and the assistant message shows saved citations.
11. Open `/projects/:projectId/agent`.
12. Run a bounded Agent task and confirm the result includes task type, warnings, and sources.
13. Open `/projects/:projectId/writing`.
14. Generate a writing artifact, confirm saved sources and unsupported claims, then export it as Markdown.
15. Open `/projects/:projectId/external-references`.
16. Search by keyword, title, or DOI, save one curated result, then export the project BibTeX draft.

## Notes on RAG Chat

- Chat uses retrieval plus prompt assembly plus backend LLM generation, not raw snippet return.
- The prompt includes a system instruction, the most recent chat history, top-k retrieved chunks, and the current question.
- If retrieval is insufficient, the system returns the fixed insufficient-information fallback string.
- Saved assistant messages keep `sources_json` scoped to the current user and current project only.

## Notes on Agent and Skills

- The Agent accepts one project-scoped request at a time and routes it to one supported Skill.
- Every Skill returns structured content plus `sources` and `warnings`.
- `EvidenceCheckSkill` returns `unsupported_claims` when the current project knowledge base cannot support part of the user input.
- Agent results and stored `agent_tasks` records remain bound to the current `user_id` and `project_id`.
- The frontend calls the backend Agent endpoint with `credentials: "include"` and never exposes provider keys.
- Literature-review-oriented Agent flows may attach saved external references, but those records are explicitly labeled as `external reference` and never treated as uploaded-document evidence.

## Notes on Paper Writing Assistant

- The Paper Writing workspace is project-scoped and owner-scoped, just like chat, documents, chunks, vectors, and Agent tasks.
- Writing generation reuses the existing project retrieval pipeline and backend-only LLM gateway.
- Every saved `writing_artifact` stores `content_markdown`, `sources_json`, and `unsupported_claims_json`.
- Markdown export is generated on the backend and returned through an authenticated owner-scoped endpoint.
- The assistant is evidence-first: unsupported conclusions are flagged for manual confirmation instead of being presented as grounded facts.
- Related-work and citation-support flows may append saved external reference notes, but those remain metadata-only and require manual confirmation.
- The writing assistant does not implement Semantic Scholar, LaTeX/Word/PDF export, experiment analysis, external tools beyond Crossref/arXiv metadata, or full-paper ghostwriting.

## Notes on External References

- External search is authenticated, owner-scoped, and project-scoped.
- The backend calls Crossref and arXiv with explicit user-entered query or DOI text only.
- The system does not send private uploaded-document chunks, project chat history, or secret keys to external metadata providers.
- Saved `external_references` store metadata only: source, title, authors, year, venue, DOI, URL, abstract, and a draft BibTeX record.
- External references are never auto-ingested into chunks, embeddings, or Qdrant.
- BibTeX export is draft-only. Users must verify author names, DOI, venue, year, and citation formatting manually.

## OpenSpec

Product source of truth lives under `openspec/specs/`.

The active implementation change in this repository is currently `change-008-external-research-tools`.
