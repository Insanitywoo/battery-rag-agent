## MODIFIED Requirements

### Requirement: Project detail scope SHALL remain limited to project metadata in this change
The project detail capability introduced in this change SHALL expand from project metadata plus document-management structure into owner-scoped project metadata plus document ingestion controls and status display, and MUST NOT introduce embeddings, vector search, RAG, Agent, or Skills workflows.

#### Scenario: Project detail remains within project-and-ingestion-workspace scope
- **WHEN** project detail behavior is reviewed in this change
- **THEN** the returned or displayed detail scope SHALL remain limited to project metadata plus owner-scoped document ingestion workflow structure, and SHALL NOT expose embeddings, vectors, RAG, Agent, or Skills workflows
