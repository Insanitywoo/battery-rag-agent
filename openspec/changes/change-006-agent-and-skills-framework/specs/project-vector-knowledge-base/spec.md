## MODIFIED Requirements

### Requirement: Semantic retrieval SHALL remain owner-scoped and project-scoped
The system SHALL provide semantic retrieval over project vectors, and retrieval MUST enforce both `user_id` and `project_id` filters at the Qdrant query layer for chat and for all Agent or Skill executions that reuse project retrieval.

#### Scenario: Agent retrieval returns only current project evidence
- **WHEN** an authenticated owner executes an Agent task that requires project retrieval
- **THEN** the retrieval results SHALL be limited to vectors belonging to that user and that project
