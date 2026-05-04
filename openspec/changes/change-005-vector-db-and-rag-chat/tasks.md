## 1. Backend Vector Foundation

- [x] 1.1 Add backend configuration and dependencies for embeddings, Qdrant access, and backend-only LLM Gateway settings
- [x] 1.2 Extend document persistence with vector-build status fields and add `chat_sessions` plus `chat_messages` models
- [x] 1.3 Add backend services for embedding generation, Qdrant upsert/delete flows, project-scoped retrieval, bounded prompt assembly, and streaming chat orchestration

## 2. Vector Build and Retrieval APIs

- [x] 2.1 Implement an authenticated owner-scoped API to build or rebuild a project's vector knowledge base from its chunks
- [x] 2.2 Ensure rebuild clears or overwrites prior vectors for the same project before storing the refreshed vector set
- [x] 2.3 Ensure Qdrant writes and retrieval always include `user_id` and `project_id` ownership metadata and filters
- [x] 2.4 Expose project knowledge-base status needed by the frontend detail view

## 3. Chat Persistence and RAG APIs

- [x] 3.1 Implement owner-scoped chat session persistence with list, open or continue, and delete operations for the current user's project conversations
- [x] 3.2 Implement chat message persistence so each message is bound to `user_id`, `project_id`, and `session_id`
- [x] 3.3 Implement an authenticated owner-scoped streaming chat API that performs retrieval, assembles prompt context from system instruction plus the most recent `N=6` messages plus top-k chunks plus the current question, calls the backend LLM Gateway, and streams the answer
- [x] 3.4 Persist the full assistant message only after stream completion and ensure saved `sources_json` contains `document_id`, `document_name`, `page_number`, `chunk_id`, `chunk_index`, and `excerpt` from only the current user's current project
- [x] 3.5 Return the explicit fallback text `当前知识库中没有足够信息` when retrieval evidence is not strong enough
- [x] 3.6 Ensure chat session query, deletion, and message append flows always enforce current-user ownership

## 4. Frontend Project Knowledge Base and Chat

- [x] 4.1 Add project-detail knowledge-base status and a build or rebuild vector DB control
- [x] 4.2 Add a project-scoped chat page with owner-scoped session list, history open flow, and follow-up question support within the current project
- [x] 4.3 Implement streaming answer rendering in the frontend using `fetch` `ReadableStream` or equivalent with `credentials: "include"` and no frontend provider secrets
- [x] 4.4 Show cited answer sources including document name, page number, and supporting snippet
- [x] 4.5 Provide session deletion UX for the current user's own chats only

## 5. Security and Documentation

- [x] 5.1 Verify frontend code and browser-exposed configuration do not contain model or Qdrant secrets
- [x] 5.2 Verify vector build and retrieval remain owner-scoped at both API and Qdrant filter layers, and verify chat session and message APIs remain owner-scoped
- [x] 5.3 Update `README.md` and `.env.example` with vector-build, Qdrant, and backend-only LLM Gateway configuration and workflow notes

## 6. Validation

- [x] 6.1 Add backend tests for vector build, rebuild replacement, owner-scoped retrieval, streaming chat completion persistence, insufficient-evidence fallback, and owner-scoped chat history
- [x] 6.2 Run backend tests or startup checks and frontend type/build checks for the vector DB and streaming RAG chat workflow
