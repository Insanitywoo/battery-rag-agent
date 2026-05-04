## MODIFIED Requirements

### Requirement: Project detail scope SHALL remain limited to project metadata in this change
The project detail capability introduced in this change SHALL expand from project metadata plus document ingestion controls into owner-scoped project metadata plus knowledge-base build state and chat entry structure, and MUST NOT introduce Agent, Skills, external retrieval, or broader research-automation workflows.

#### Scenario: Project detail remains within project knowledge-base scope
- **WHEN** project detail behavior is reviewed in this change
- **THEN** the returned or displayed detail scope SHALL remain limited to project metadata plus owner-scoped knowledge-base and chat-entry workflow structure, and SHALL NOT expose broader automation workflows

#### Scenario: Project chat route remains project-scoped and owner-scoped
- **WHEN** an authenticated owner enters chat from project detail
- **THEN** the resulting chat experience SHALL remain scoped to that owner's current project sessions and retrieved sources only
