## MODIFIED Requirements

### Requirement: Project detail scope SHALL remain limited to bounded project research tools in this change
The project detail capability introduced in this change SHALL expand from project metadata plus chat, Agent, and Paper Writing entry structure into owner-scoped project metadata plus an External References entry structure, and MUST NOT introduce unrestricted crawling or broader autonomous research workflows.

#### Scenario: Project External References route remains project-scoped and owner-scoped
- **WHEN** an authenticated owner enters the External References page from project detail
- **THEN** the resulting external-reference experience SHALL remain scoped to that owner's current project, current saved references, and current export actions only
