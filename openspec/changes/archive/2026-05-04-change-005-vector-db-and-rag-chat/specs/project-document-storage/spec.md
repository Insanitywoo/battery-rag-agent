## MODIFIED Requirements

### Requirement: Document metadata SHALL be persisted with explicit ownership and storage fields
The system SHALL persist document metadata for every accepted upload, and document records in this change SHALL also support vector-build outcome fields such as `embedding_status` and `embedded_at` in addition to ingestion lifecycle metadata.

#### Scenario: Document record tracks vector-build outcomes
- **WHEN** a document's chunks are embedded successfully or vector build fails
- **THEN** the corresponding document record SHALL be able to store vector-build status information alongside ingestion outcome metadata
