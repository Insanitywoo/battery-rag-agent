## MODIFIED Requirements

### Requirement: Agent execution SHALL support bounded external-reference assistance for literature workflows
The system SHALL allow literature-review-oriented and related-work-oriented flows in this capability to reuse saved project-scoped `external_references`, and any live external metadata lookup enabled by this change SHALL remain bounded to explicit user search intent rather than private document content.

#### Scenario: Literature workflow uses saved external references safely
- **WHEN** an authenticated owner runs a literature-review-oriented or related-work-oriented task
- **THEN** the Agent or writing flow MAY use saved project-scoped external references in addition to internal project evidence, while preserving owner and project isolation

### Requirement: External references SHALL remain distinct from internal evidence
The Agent framework SHALL label external metadata as `external reference`, SHALL NOT treat it as uploaded-document evidence, and SHALL NOT auto-ingest it into chunks, embeddings, or vector search state in this change.

#### Scenario: External result does not masquerade as uploaded-document evidence
- **WHEN** an Agent or writing flow uses a saved or live external scholarly result
- **THEN** the output SHALL label that material as external reference content and SHALL NOT present it as internal project document evidence
