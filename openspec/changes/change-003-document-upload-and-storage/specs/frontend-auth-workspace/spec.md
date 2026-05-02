## MODIFIED Requirements

### Requirement: Frontend MAY provide only a reserved project-detail entry point in this change
The frontend SHALL provide a functional project-detail route for the authenticated owner that includes file upload, file list, and file delete interactions for that project, but it MUST remain limited to document-management scope and MUST NOT implement document parsing, knowledge base, RAG, Agent, or Skills workflows.

#### Scenario: Project-detail route becomes a minimal document workspace
- **WHEN** an authenticated owner enters the project-detail route from the project list
- **THEN** the frontend SHALL render the project-level document workspace with upload and list/delete controls, and SHALL exclude downstream research workflows
