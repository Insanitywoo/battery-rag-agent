## MODIFIED Requirements

### Requirement: Backend shell SHALL avoid business capability implementation
The backend shell MUST NOT implement arbitrary Python execution, user-defined experiment scripts, simulation systems, hardware control, complex machine-learning modeling, billing logic, or other out-of-scope business workflows in this change, but it MAY implement user authentication, owner-scoped project workspace APIs, project document storage APIs, document ingestion and chunk persistence APIs, project vector indexing APIs, semantic retrieval APIs, streaming project-scoped RAG chat APIs, owner-scoped chat history APIs, project-scoped Agent plus Skills APIs, project-scoped paper-writing assistant APIs, bounded external scholarly metadata and BibTeX tooling, and bounded CSV experiment-analysis plus controlled chart APIs introduced by this change.

#### Scenario: Backend scope is limited to bounded research workflows plus experiment-analysis tools
- **WHEN** the backend shell is reviewed for accepted functionality in this change
- **THEN** the functional expansion beyond health check SHALL be limited to authentication, owner-scoped workspace and document APIs, retrieval and chat, bounded Agent and writing assistance, bounded external scholarly metadata plus BibTeX APIs, and bounded CSV experiment-analysis plus controlled chart APIs, and SHALL exclude arbitrary script execution, simulation, device control, and complex autonomous planning
