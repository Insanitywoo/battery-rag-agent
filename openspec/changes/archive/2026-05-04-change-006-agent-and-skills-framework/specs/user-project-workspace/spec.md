## MODIFIED Requirements

### Requirement: Project detail scope SHALL remain limited to project metadata in this change
The project detail capability introduced in this change SHALL expand from project metadata plus knowledge-base build state and chat entry structure into owner-scoped project metadata plus chat and Agent entry structure, and MUST NOT introduce external retrieval, external tools, or broader autonomous research workflows.

#### Scenario: Project Agent route remains project-scoped and owner-scoped
- **WHEN** an authenticated owner enters the Agent page from project detail
- **THEN** the resulting Agent experience SHALL remain scoped to that owner's current project, current task history, and current project sources only
