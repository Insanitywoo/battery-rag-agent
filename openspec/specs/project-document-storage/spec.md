# project-document-storage Specification

## Purpose
TBD - created by archiving change change-003-document-upload-and-storage. Update Purpose after archive.
## Requirements
### Requirement: Authenticated users SHALL be able to upload supported documents under their own projects
The system SHALL allow an authenticated user to upload a document only within a project owned by that user, and it SHALL bind the created document record to both `user_id` and `project_id`.

#### Scenario: Owner uploads a document
- **WHEN** an authenticated user uploads a valid document into a project they own
- **THEN** the system SHALL create a document record bound to that user and project and SHALL persist the raw file into configured local storage

#### Scenario: Non-owner cannot upload into another user's project
- **WHEN** an authenticated user attempts to upload a document into a project owned by another user
- **THEN** the system SHALL reject the request and SHALL NOT create a document record or stored file

### Requirement: Document uploads SHALL be restricted by supported extension, MIME type, and file-size limits
The system SHALL accept only supported document types in this change, SHALL validate both file extension and MIME type, and SHALL reject uploads that exceed the configured size limit.

#### Scenario: Supported document type is accepted
- **WHEN** an authenticated owner uploads a `pdf`, `txt`, `md`, or `csv` file within the configured size limit and with an allowed MIME type
- **THEN** the system SHALL accept the upload

#### Scenario: Unsupported extension, MIME type, or oversized payload is rejected
- **WHEN** a client uploads a file with an unsupported extension, unsupported MIME type, or size above the configured limit
- **THEN** the system SHALL reject the upload and SHALL NOT persist document metadata or raw file content

### Requirement: Document metadata SHALL be persisted with explicit ownership and storage fields
The system SHALL persist document metadata for every accepted upload, including ownership fields, file identity, file size, MIME information, storage path, and document status.

#### Scenario: Accepted upload creates metadata record
- **WHEN** a valid upload is accepted
- **THEN** the system SHALL persist document metadata including `id`, `user_id`, `project_id`, `filename`, `original_filename`, `file_type`, `mime_type`, `file_size`, `storage_path`, `status`, `created_at`, and `updated_at`

### Requirement: Stored file paths and filenames SHALL be handled safely
The system SHALL sanitize user-supplied filename information for display, SHALL generate server-controlled storage paths, and MUST NOT allow uploaded filenames to escape the configured storage root.

#### Scenario: Storage path is safe and server-controlled
- **WHEN** a document is stored
- **THEN** the resulting storage path SHALL remain within the configured storage root and SHALL NOT be derived directly from unsanitized user input

### Requirement: Authenticated users SHALL be able to list and inspect only their own project documents
The system SHALL provide document list and document detail capabilities that return only documents owned by the current authenticated user within the specified project.

#### Scenario: Owner lists project documents
- **WHEN** an authenticated owner requests the document list for a project they own
- **THEN** the system SHALL return only documents associated with that user and that project

#### Scenario: Cross-user document access is blocked
- **WHEN** a client attempts to retrieve a document list or detail for another user's project or document
- **THEN** the system SHALL reject the request and SHALL NOT expose document metadata

### Requirement: Authenticated users SHALL be able to delete only their own project documents
The system SHALL allow an authenticated owner to delete a document only within a project they own, and the delete operation SHALL remove both the stored file and its metadata record.

#### Scenario: Owner deletes a document
- **WHEN** an authenticated owner deletes a document in their own project
- **THEN** the system SHALL remove the raw file from local storage and SHALL delete the document metadata record

#### Scenario: Non-owner cannot delete another user's document
- **WHEN** an authenticated user attempts to delete a document belonging to another user's project
- **THEN** the system SHALL reject the request and SHALL NOT remove the other user's metadata or file

### Requirement: This change SHALL not execute or process uploaded file contents
The system MUST NOT execute code from uploaded files and MUST NOT introduce parsing, chunking, embedding, OCR, vector indexing, RAG, Agent, or Skills workflows in this change.

#### Scenario: Upload scope remains storage-only
- **WHEN** the document workflow is reviewed in this change
- **THEN** accepted behavior SHALL remain limited to file storage and metadata management rather than content execution or downstream research processing

