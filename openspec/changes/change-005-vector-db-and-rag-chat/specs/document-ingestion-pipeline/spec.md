## MODIFIED Requirements

### Requirement: The system SHALL generate and persist owner-scoped document chunks
The system SHALL continue to persist owner-scoped chunks as the canonical source for downstream embedding and project-scoped retrieval workflows introduced in this change.

#### Scenario: Persisted chunks are retrieval-ready
- **WHEN** ingestion succeeds
- **THEN** the resulting chunks SHALL be usable as the authoritative source for project-level vector indexing and later retrieval
