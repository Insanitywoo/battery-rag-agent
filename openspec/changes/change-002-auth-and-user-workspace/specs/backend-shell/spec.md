## MODIFIED Requirements

### Requirement: Backend shell SHALL avoid business capability implementation
The backend shell MUST NOT implement document ingestion, RAG retrieval, Agent execution, Skills orchestration, or other out-of-scope business workflows in this change, but it MAY implement user authentication and owner-scoped project workspace APIs introduced by this change.

#### Scenario: Backend scope is limited to auth and project workspace
- **WHEN** the backend shell is reviewed for accepted functionality in this change
- **THEN** the functional expansion beyond health check SHALL be limited to authentication and owner-scoped project workspace APIs, and SHALL exclude document, RAG, Agent, and Skills capabilities
