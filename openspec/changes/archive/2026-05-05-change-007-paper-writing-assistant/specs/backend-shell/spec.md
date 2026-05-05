## MODIFIED Requirements

### Requirement: Backend shell SHALL avoid business capability implementation
The backend shell MUST NOT implement external web search, Skills that call external tools, OCR, external literature APIs, experimental data analysis, complex multi-step ReAct planning, billing logic, or other out-of-scope business workflows in this change, but it MAY implement user authentication, owner-scoped project workspace APIs, project document storage APIs, document ingestion and chunk persistence APIs, project vector indexing APIs, semantic retrieval APIs, streaming project-scoped RAG chat APIs, owner-scoped chat history APIs, project-scoped Agent plus Skills APIs, and project-scoped paper-writing assistant APIs introduced by this change.

#### Scenario: Backend scope is limited to auth, workspace, retrieval, RAG chat, bounded Agent execution, and writing assistance
- **WHEN** the backend shell is reviewed for accepted functionality in this change
- **THEN** the functional expansion beyond health check SHALL be limited to authentication, owner-scoped workspace and document APIs, chunk persistence, vector indexing and retrieval, streaming project-scoped RAG chat, owner-scoped chat session and message APIs, bounded project-scoped Agent and Skills execution, and bounded project-scoped writing assistant APIs, and SHALL exclude external tools, web search, OCR, experiment analysis, and complex autonomous planning
