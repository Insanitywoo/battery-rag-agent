## Why

Battery-RAG Agent can now upload documents and convert them into owner-scoped chunks, but those chunks still live only in PostgreSQL. Before the product can answer project-specific research questions, the system needs a project-level vector knowledge base and a bounded RAG chat loop that retrieves only the current user's current project's chunks, assembles those chunks with recent chat history and the current question into a prompt, calls the LLM from the backend, and streams cited answers back to the user.

## What Changes

- Add backend embedding generation for persisted `document_chunks`.
- Add Qdrant write and rebuild flows for a single project's chunk set.
- Store vector payload metadata including `user_id`, `project_id`, `document_id`, `chunk_id`, `page_number`, and `chunk_index`.
- Add owner-scoped project-level semantic retrieval with mandatory `user_id` and `project_id` filtering in Qdrant.
- Add a backend-only LLM Gateway configured through environment variables.
- Add a bounded RAG prompt that assembles system instruction, recent chat history, retrieved chunks, and the current user question before calling the LLM.
- Add a streaming chat endpoint so project answers render incrementally in the frontend and are persisted after the stream completes.
- Add account-scoped chat persistence with `chat_sessions` and `chat_messages`, including list, open, continue, and delete flows per project.
- Extend project detail to show knowledge-base status and provide a build vector DB entry point.
- Add a project-scoped chat page that shows streamed answers plus document, page, and snippet sources.
- Update `.env.example` and `README.md` with vector DB, embedding, streaming chat, and model gateway configuration.
- **BREAKING**: Project document workflows will no longer stop at ingestion; a project can now build a vector knowledge base and expose a project-scoped RAG chat interface.

## Capabilities

### New Capabilities

- `project-vector-knowledge-base`: Defines embedding generation, Qdrant persistence, project-level rebuild behavior, and owner-scoped semantic retrieval.
- `project-rag-chat`: Defines project-scoped chat sessions, message persistence, streaming RAG prompting, citation-bearing answer generation, and owner-scoped chat history management.

### Modified Capabilities

- `backend-shell`: Expands accepted backend scope from ingestion only to ingestion plus vector indexing, retrieval, streaming RAG chat APIs, and owner-scoped chat history APIs.
- `document-ingestion-pipeline`: Extends chunk persistence from retrieval-prep data only into a source for embeddings and project-level retrieval.
- `project-document-storage`: Extends document metadata to support vector-build outcome tracking such as embedding status or embedded timestamp.
- `user-project-workspace`: Expands project detail from ingestion-only controls into ingestion plus knowledge-base status, chunk-backed chat readiness, and chat entry points.
- `frontend-auth-workspace`: Expands the authenticated project workspace to include knowledge-base build controls, a streaming project chat route, and owner-scoped session history interactions.
- `local-dev-infra`: Extends environment documentation to cover Qdrant and backend-only LLM and embedding gateway configuration.

## Impact

- Affected code: backend embedding and Qdrant services, retrieval and streaming chat APIs, chat persistence models, frontend project detail and chat pages, shared environment configuration, and documentation.
- Affected APIs: vector-build endpoints, streaming chat and session endpoints, and project detail payloads with knowledge-base status information.
- Affected systems: PostgreSQL chat persistence, Qdrant collections and points, backend model gateway configuration, and project-scoped retrieval boundaries.
- Dependencies likely introduced or activated: embedding model client, streaming chat-completion client, Qdrant integration helpers, and structured source serialization.
