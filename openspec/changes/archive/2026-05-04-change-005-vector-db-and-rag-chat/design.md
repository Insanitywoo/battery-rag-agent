## Context

Battery-RAG Agent already supports owner-scoped project documents, synchronous ingestion, and chunk persistence in PostgreSQL. The next increment is retrieval readiness: turning chunks into project-bounded vectors, then exposing a minimal RAG chat interface that retrieves only from the active user's active project and answers with citations instead of unconstrained generation.

This change crosses several boundaries:

- The backend must generate embeddings for existing chunks.
- The system must write vectors into Qdrant with strict ownership metadata.
- Rebuild flows must replace or overwrite prior project vectors safely.
- Retrieval must always filter by both `user_id` and `project_id`.
- The backend must call the model provider through a server-side gateway.
- The frontend must gain project knowledge-base controls and a project-scoped streaming chat experience.

Primary constraints:

- Only authenticated users may build vectors or chat.
- Users may only vectorize and query chunks from projects they own.
- Qdrant payloads and filters must carry `user_id` and `project_id`.
- Frontend chat requests must use `credentials: "include"` and must not expose provider credentials or browser-stored tokens.
- LLM and embedding API keys must stay in backend environment variables only.
- If retrieval evidence is weak or empty, the answer must explicitly say `当前知识库中没有足够信息`.
- Answers must always return source document, page number, and supporting snippet metadata.
- This change must not introduce Agent workflows, reranking, BM25, OCR, external retrieval, or async queues.

## Goals / Non-Goals

**Goals:**

- Generate embeddings for `document_chunks`.
- Persist vectors to Qdrant with project and ownership metadata.
- Support a project-scoped build vector DB and rebuild vector DB flow.
- Support project-scoped semantic retrieval with strict filters.
- Add a backend-only LLM Gateway configurable through environment variables.
- Add a bounded RAG prompt with explicit fallback when evidence is insufficient.
- Stream assistant answers from the backend to the frontend while persisting the final assistant message after stream completion.
- Persist chat sessions and chat messages for project conversations, including history listing, continuation, and deletion.
- Add project-detail knowledge-base status and a project chat page.

**Non-Goals:**

- Agent orchestration or Skills execution.
- Multi-step research workflows such as paper summary or related-work writing.
- Experiment-data analysis.
- External literature retrieval.
- Reranking or hybrid BM25 retrieval.
- Complex multi-model routing.
- Billing or usage quotas.
- Celery or any heavy async worker infrastructure unless a minimal existing primitive already exists.

## Decisions

### Decision: Split vector indexing and chat into two first-class capabilities

This change should keep build or search the project knowledge base and run RAG chat over that knowledge base conceptually distinct, even if they share APIs and services. This preserves clean boundaries:

- vector capability for embeddings, Qdrant writes, and retrieval
- chat capability for sessions, messages, prompt composition, and cited answers

### Decision: Track vector-build status at the document level

Rather than inventing a new project-level knowledge table immediately, this change should extend documents with:

- `embedding_status`
- `embedded_at`

The project-level knowledge status shown in the UI can then be derived from the project's documents and chunks:

- whether a project has any processed chunks
- whether vectorization has succeeded for those documents

This keeps the schema smaller while still surfacing useful operational state.

### Decision: Use Qdrant payload metadata as the primary ownership and citation bridge

Every vector written to Qdrant should include payload fields:

- `user_id`
- `project_id`
- `document_id`
- `chunk_id`
- `page_number`
- `chunk_index`

This enables:

- strict ownership filtering during retrieval
- deterministic lookup back into local metadata
- direct citation rendering in the frontend

### Decision: Rebuild vectors by replacing the project's prior vector set

When a user triggers rebuild for a project, the system should not append duplicate vectors indefinitely. The rebuild flow should delete or overwrite prior Qdrant points for that project's chunks, then repopulate the current chunk set. This keeps retrieval results consistent with the latest ingestion state.

### Decision: Keep retrieval strictly project-scoped with mandatory Qdrant filters

Semantic retrieval must always apply both `user_id` and `project_id` filters at the Qdrant level, not just in application-side post-filtering. This ensures:

- no cross-user leakage
- no cross-project leakage
- source citations can only originate from the current user's current project

### Decision: Build the RAG response as retrieval plus prompt assembly plus streaming generation

This change explicitly defines chat as:

1. receive the current user question within a project session
2. retrieve top matching chunks from the current user's current project
3. assemble a prompt from system instruction, recent chat history, retrieved chunks, and the current question
4. call the backend LLM Gateway
5. stream the assistant answer to the frontend in real time
6. persist the completed assistant message and its citations when streaming finishes

This prevents the product from devolving into a plain retrieval viewer and matches the intended online assistant experience.

### Decision: Implement a backend-only LLM Gateway with environment-backed configuration

The frontend must never call the model provider directly. The backend should own:

- embedding generation
- retrieval orchestration
- RAG prompt assembly
- answer generation
- streaming response generation

Recommended environment-backed configuration:

- `LLM_API_BASE_URL`
- `LLM_API_KEY`
- `LLM_CHAT_MODEL`
- `LLM_EMBEDDING_MODEL`
- `LLM_PROVIDER`
- `QDRANT_URL`
- `QDRANT_API_KEY` if needed
- `QDRANT_COLLECTION_NAME`

### Decision: Use a bounded citation-first RAG prompt with recent chat history

The prompt payload should contain:

- a system instruction
- the most recent `N` chat history messages, default `N = 6`
- the retrieved top `K` chunks for the current question
- the current user question

`N` should be configurable in backend settings even if it defaults to `6`. Retrieval `top_k` should also stay backend-controlled so scope does not leak into frontend configuration.

### Decision: Stream answers and persist the final assistant message only after completion

The prompt should instruct the model to:

1. answer only from retrieved evidence
2. avoid unsupported claims
3. say the current knowledge base lacks enough information when evidence is insufficient
4. preserve source references

The chat endpoint should stream tokens or content chunks to the frontend. Once the stream completes successfully, the backend should persist one complete assistant message record with the finalized content and `sources_json`. If the stream fails partway through, the design should favor not saving a partial assistant message as if it were complete.

This is the simplest path to honest, auditable answers without introducing more advanced reranking or agent planning.

### Decision: Persist chat sessions and chat messages now

Chat history should be first-class rather than ephemeral so later changes can reuse it for summaries, export, follow-up context, and UX continuity.

Planned `chat_sessions` fields:

- `id`
- `user_id`
- `project_id`
- `title`
- `created_at`
- `updated_at`

Planned `chat_messages` fields:

- `id`
- `user_id`
- `project_id`
- `session_id`
- `role`
- `content`
- `sources_json`
- `created_at`

`chat_sessions` and `chat_messages` must always be owner-scoped:

- each session bound to `user_id` and `project_id`
- each message bound to `user_id`, `project_id`, and `session_id`
- list, read, append, continue, and delete operations must verify the current authenticated owner

The product should support:

- list current user's sessions inside a project
- open a historical session
- continue asking follow-up questions in that session
- delete a session owned by the current user

For deletion, this change should use hard delete with cascade-style message cleanup rather than soft delete. Deleting a session should also delete its messages so the account-level history remains consistent and simple.

### Decision: Persist citation payloads in a structured `sources_json` schema

Each saved assistant message should persist `sources_json` entries with:

- `document_id`
- `document_name`
- `page_number`
- `chunk_id`
- `chunk_index`
- `excerpt`

These source entries must only originate from the same `user_id` and `project_id` used by the current chat session and retrieval query.

### Decision: Extend project detail lightly and add a dedicated project chat route

The project detail page should gain:

- knowledge-base status
- build or rebuild trigger
- chat entry point

The actual question and answer experience should live on a dedicated project chat route so the detail page does not become overloaded. That route should also include:

- current project's session list for the authenticated user
- the ability to reopen and continue a past session
- streaming assistant answer rendering

The frontend should use `fetch` streaming (`ReadableStream` or equivalent) with `credentials: "include"` for chat requests and should never call the provider directly.

## Risks / Trade-offs

- [Synchronous vector building may take noticeable time on large projects] -> acceptable for this bounded change while async infrastructure remains out of scope.
- [Provider abstraction can grow complex quickly] -> controlled by using a simple backend gateway with a single configured provider and model path.
- [Retrieval quality may be basic without rerank or hybrid search] -> acceptable because this change prioritizes safe scoping and end-to-end functionality.
- [Document-level embedding status may not perfectly summarize project readiness] -> acceptable because project-level status can be derived without adding a heavier coordination table yet.
- [Hallucination risk remains if prompts are weak] -> mitigated by a strict evidence-only prompt, recent-history bounds, and explicit insufficient-information fallback.
- [Streaming failures may leave inconsistent history] -> mitigated by persisting the assistant message only after successful stream completion and by treating partial stream failures as non-final responses.

## Migration Plan

This is an additive change on top of chunk persistence.

Suggested rollout order:

1. Add vector and LLM and Qdrant configuration defaults.
2. Extend document metadata and add chat persistence models.
3. Add embedding, Qdrant, retrieval, and RAG gateway services.
4. Add project-level build and rebuild endpoints.
5. Add chat session, message, and streaming ask-question endpoints.
6. Extend project detail with knowledge-base status and add a project chat page.
7. Update docs and validate owner scoping, rebuild replacement, stream persistence, and insufficient-evidence behavior.

Rollback path:

- remove vector-build and chat APIs
- remove chat persistence models
- remove document embedding-status fields if necessary
- leave upload, ingestion, and chunk persistence intact

## Open Questions

- Should the first vector build create one shared project collection namespace with payload filters, or should each project map to a distinct logical partition strategy inside one configured collection?
- Should session titles be user-provided only, or may a later change auto-title from the first question while keeping that logic out of scope for now?
