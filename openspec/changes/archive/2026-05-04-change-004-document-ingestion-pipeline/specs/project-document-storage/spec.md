## MODIFIED Requirements

### Requirement: Document metadata SHALL be persisted with explicit ownership and storage fields
The system SHALL persist document metadata for every accepted upload, and document records in this change SHALL also support ingestion lifecycle fields including `error_message`, `processed_at`, and `chunk_count`.

#### Scenario: Document record tracks ingestion outcomes
- **WHEN** a document is processed successfully or fails during ingestion
- **THEN** the corresponding document record SHALL be able to store processing outcome metadata, including status, processed timestamp, chunk count, and sanitized failure message when relevant

### Requirement: This change SHALL not execute or process uploaded file contents
The system MAY parse, clean, and chunk uploaded document contents for owner-scoped ingestion in this change, but it MUST NOT execute code from uploaded files and MUST NOT introduce embeddings, vector indexing, RAG, Agent, Skills, OCR, or complex external retrieval workflows.

#### Scenario: Ingestion scope remains bounded
- **WHEN** the document workflow is reviewed in this change
- **THEN** accepted behavior SHALL include parsing, cleaning, and chunk persistence only, and SHALL exclude content execution or downstream retrieval workflows
