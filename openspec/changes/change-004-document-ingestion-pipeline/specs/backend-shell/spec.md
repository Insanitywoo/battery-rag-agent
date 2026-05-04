## MODIFIED Requirements

### Requirement: Backend shell SHALL avoid business capability implementation
The backend shell MUST NOT implement embedding generation, vector retrieval, RAG answering, Agent execution, Skills orchestration, OCR, or other out-of-scope business workflows in this change, but it MAY implement user authentication, owner-scoped project workspace APIs, project document storage APIs, and project document ingestion and chunk persistence APIs introduced by this change.

#### Scenario: Backend scope is limited to auth, workspace, storage, and ingestion
- **WHEN** the backend shell is reviewed for accepted functionality in this change
- **THEN** the functional expansion beyond health check SHALL be limited to authentication, owner-scoped project workspace APIs, project document storage APIs, and document ingestion/chunk persistence APIs, and SHALL exclude embeddings, vectors, RAG, Agent, and Skills capabilities
