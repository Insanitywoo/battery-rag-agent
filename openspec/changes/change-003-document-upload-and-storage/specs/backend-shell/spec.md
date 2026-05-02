## MODIFIED Requirements

### Requirement: Backend shell SHALL avoid business capability implementation
The backend shell MUST NOT implement document parsing, text chunking, embedding generation, vector retrieval, Agent execution, Skills orchestration, or other out-of-scope business workflows in this change, but it MAY implement user authentication, owner-scoped project workspace APIs, and owner-scoped project document storage APIs introduced by this change.

#### Scenario: Backend scope is limited to auth, project workspace, and document storage
- **WHEN** the backend shell is reviewed for accepted functionality in this change
- **THEN** the functional expansion beyond health check SHALL be limited to authentication, owner-scoped project workspace APIs, and owner-scoped project document storage APIs, and SHALL exclude parsing, RAG, Agent, and Skills capabilities
