# document-ingestion-pipeline Specification

## Purpose
TBD - created by archiving change change-004-document-ingestion-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Authenticated owners SHALL be able to trigger document ingestion for stored project documents
The system SHALL allow an authenticated project owner to trigger ingestion for a document that belongs to that owner's project, and it SHALL reject unauthenticated or cross-user ingestion requests.

#### Scenario: Owner triggers document ingestion
- **WHEN** an authenticated owner requests processing for a stored document in a project they own
- **THEN** the system SHALL start the ingestion workflow for that document

#### Scenario: Non-owner cannot trigger ingestion
- **WHEN** an authenticated user attempts to process a document belonging to another user's project
- **THEN** the system SHALL reject the request and SHALL NOT process the other user's document

### Requirement: The ingestion pipeline SHALL support bounded parsing behavior for supported file types
The system SHALL parse PDF, TXT, and Markdown documents into text for ingestion, SHALL preserve PDF page-number lineage, and SHALL keep CSV handling bounded to metadata or simple textual preview rather than complex table parsing.

#### Scenario: PDF ingestion preserves page numbers
- **WHEN** a PDF document is processed successfully
- **THEN** the system SHALL extract text with page-number lineage that can be attached to produced chunks

#### Scenario: TXT or Markdown ingestion reads plain text
- **WHEN** a TXT or Markdown document is processed successfully
- **THEN** the system SHALL read the textual content into the ingestion pipeline

#### Scenario: CSV ingestion remains bounded
- **WHEN** a CSV document is processed in this change
- **THEN** the system SHALL remain limited to metadata-oriented or simple text-preview ingestion and SHALL NOT implement complex table parsing

### Requirement: Parsed text SHALL be cleaned before chunking
The system SHALL normalize and clean parsed document text before chunk generation so downstream chunks are derived from a stable textual representation.

#### Scenario: Parsed text is normalized
- **WHEN** document text enters the chunking stage
- **THEN** the ingestion workflow SHALL operate on cleaned text rather than raw parser output alone

### Requirement: The system SHALL generate and persist owner-scoped document chunks
The system SHALL split cleaned document text into chunks using configured chunk size and overlap values, and each persisted chunk SHALL be bound to `user_id`, `project_id`, and `document_id`.

#### Scenario: Chunks are persisted with lineage and metadata
- **WHEN** ingestion succeeds
- **THEN** the system SHALL persist chunks containing `page_number`, `chunk_index`, `content`, `char_count`, and ownership lineage fields

### Requirement: Document status SHALL reflect ingestion outcomes
The system SHALL update document status during ingestion, SHALL set `processed` on success, SHALL set `failed` on failure, and SHALL record outcome metadata including `processed_at`, `chunk_count`, and sanitized `error_message` where applicable.

#### Scenario: Successful ingestion updates document outcome fields
- **WHEN** a document is processed successfully
- **THEN** the document SHALL be marked `processed` and SHALL reflect the resulting processed timestamp and chunk count

#### Scenario: Failed ingestion records sanitized failure state
- **WHEN** a document ingestion attempt fails
- **THEN** the document SHALL be marked `failed` and SHALL store a sanitized error message without leaking sensitive server paths

### Requirement: Reprocessing SHALL replace prior chunks for the document
The system SHALL support reprocessing an existing document, and reprocessing SHALL clear previously stored chunks for that document before persisting the refreshed chunk set.

#### Scenario: Reprocessing replaces stale chunks
- **WHEN** an owner reprocesses a previously ingested document
- **THEN** the system SHALL remove that document's old chunks and persist only the refreshed chunk set

### Requirement: Ingestion SHALL read files only from the configured storage root
The system SHALL resolve stored document paths against the configured storage root before reading file content, and ingestion MUST NOT read content from outside that root.

#### Scenario: Ingestion read path remains storage-root bounded
- **WHEN** the ingestion pipeline resolves a document file for reading
- **THEN** the resolved file path SHALL remain within the configured storage root

### Requirement: Chunk content SHALL originate only from the current user's own document
The system SHALL ensure that persisted chunk content is produced only from the authenticated owner's targeted document and SHALL NOT expose or persist chunk content from another user's files.

#### Scenario: Chunk lineage stays owner-scoped
- **WHEN** chunks are created for a processed document
- **THEN** those chunks SHALL belong only to the current authenticated owner's document, project, and user scope

