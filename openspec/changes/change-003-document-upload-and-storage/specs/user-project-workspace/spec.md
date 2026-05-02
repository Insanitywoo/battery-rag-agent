## MODIFIED Requirements

### Requirement: Project detail scope SHALL remain limited to project metadata in this change
The project detail capability introduced in this change SHALL expand from metadata-only scope into owner-scoped project metadata plus document-management structure, and MUST NOT introduce document parsing, knowledge base construction, RAG, Agent, or Skills business workflows.

#### Scenario: Project detail remains within project-and-document-workspace scope
- **WHEN** project detail behavior is reviewed in this change
- **THEN** the returned or displayed detail scope SHALL remain limited to project-level metadata plus owner-scoped document workspace structure, and SHALL NOT expose parsing, knowledge-base, RAG, Agent, or Skills workflows
