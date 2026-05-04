## MODIFIED Requirements

### Requirement: Backend shell SHALL avoid business capability implementation
The backend shell MUST NOT implement Agent execution, Skills orchestration, OCR, external literature retrieval, reranking, hybrid BM25 retrieval, billing logic, or other out-of-scope business workflows in this change, but it MAY implement user authentication, owner-scoped project workspace APIs, project document storage APIs, document ingestion and chunk persistence APIs, project vector indexing APIs, semantic retrieval APIs, streaming project-scoped RAG chat APIs, and owner-scoped chat history APIs introduced by this change.

#### Scenario: Backend scope is limited to auth, workspace, ingestion, vector DB, and RAG chat
- **WHEN** the backend shell is reviewed for accepted functionality in this change
- **THEN** the functional expansion beyond health check SHALL be limited to authentication, owner-scoped workspace and document APIs, chunk persistence, vector indexing and retrieval, streaming project-scoped RAG chat, and owner-scoped chat session and message APIs, and SHALL exclude Agent, Skills, OCR, external retrieval, and advanced ranking workflows
