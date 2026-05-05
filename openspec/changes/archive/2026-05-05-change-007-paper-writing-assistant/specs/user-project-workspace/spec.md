## MODIFIED Requirements

### Requirement: Project detail scope SHALL remain limited to project metadata in this change
The project detail capability introduced in this change SHALL expand from project metadata plus knowledge-base build state and chat plus Agent entry structure into owner-scoped project metadata plus a Paper Writing entry structure, and MUST NOT introduce external retrieval, external tools, or broader autonomous research workflows.

#### Scenario: Project Paper Writing route remains project-scoped and owner-scoped
- **WHEN** an authenticated owner enters the Paper Writing page from project detail
- **THEN** the resulting writing experience SHALL remain scoped to that owner's current project, current writing artifacts, and current project sources only
