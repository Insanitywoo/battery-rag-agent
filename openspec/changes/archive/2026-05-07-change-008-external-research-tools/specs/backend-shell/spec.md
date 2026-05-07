## MODIFIED Requirements

### Requirement: Backend shell SHALL avoid business capability implementation
The backend shell MUST NOT implement external web search beyond bounded scholarly metadata lookup, OCR, experimental data analysis, complex multi-step ReAct planning, billing logic, or other out-of-scope business workflows in this change, but it MAY implement user authentication, owner-scoped project workspace APIs, project document storage APIs, document ingestion and chunk persistence APIs, project vector indexing APIs, semantic retrieval APIs, streaming project-scoped RAG chat APIs, owner-scoped chat history APIs, project-scoped Agent plus Skills APIs, project-scoped paper-writing assistant APIs, and bounded external scholarly metadata and BibTeX tooling introduced by this change.

#### Scenario: Backend scope is limited to internal research workflows plus bounded external metadata tools
- **WHEN** the backend shell is reviewed for accepted functionality in this change
- **THEN** the functional expansion beyond health check SHALL be limited to authentication, owner-scoped workspace and document APIs, retrieval and chat, bounded Agent and writing assistance, and bounded external scholarly metadata plus BibTeX APIs, and SHALL exclude external full-text scraping, copyright bypass, experiment analysis, and complex autonomous planning
