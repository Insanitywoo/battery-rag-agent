## MODIFIED Requirements

### Requirement: Project detail scope SHALL remain limited to bounded project research tools in this change
The project detail capability introduced in this change SHALL expand from project metadata plus chat, Agent, Paper Writing, External References entry structure into owner-scoped project metadata plus an Experiment Analysis entry structure, and MUST NOT introduce unrestricted compute pipelines or broader autonomous workflows.

#### Scenario: Project Experiment Analysis route remains project-scoped and owner-scoped
- **WHEN** an authenticated owner enters the Experiment Analysis page from project detail
- **THEN** the resulting experiment-analysis experience SHALL remain scoped to that owner's current project, current experiment datasets, current saved outputs, and current export actions only
