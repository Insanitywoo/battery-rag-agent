## MODIFIED Requirements

### Requirement: Frontend MAY provide only a reserved project-detail entry point in this change
The frontend SHALL provide a functional project-detail route for the authenticated owner that includes document ingestion controls, document processing status, and chunk-count display for that project, but it MUST remain limited to document-management and ingestion scope and MUST NOT implement embeddings, vector search, RAG, Agent, or Skills workflows.

#### Scenario: Project-detail route becomes a minimal ingestion workspace
- **WHEN** an authenticated owner enters the project-detail route from the project list
- **THEN** the frontend SHALL render the project-level ingestion workspace with upload/list/delete plus processing controls and status feedback, and SHALL exclude downstream research workflows
