## 1. Backend Ingestion Foundation

- [x] 1.1 Add backend ingestion configuration defaults for chunk sizing, overlap, and supported parser behavior
- [x] 1.2 Extend the document persistence model with ingestion lifecycle fields and add the `document_chunks` model with explicit `user_id`, `project_id`, and `document_id`
- [x] 1.3 Add backend ingestion services for safe storage-path resolution, document parsing, text cleaning, and character-based chunk generation

## 2. Backend Ingestion APIs

- [x] 2.1 Implement an authenticated owner-scoped API to trigger document ingestion for an uploaded document
- [x] 2.2 Implement status transitions for `processing`, `processed`, and `failed`, including sanitized error recording
- [x] 2.3 Implement reprocessing that removes prior chunks before storing the refreshed chunk set
- [x] 2.4 Ensure ingestion APIs reject unauthenticated, cross-user, and out-of-storage-root document access

## 3. Frontend Project Detail Updates

- [x] 3.1 Update the project detail document list to show ingestion status and chunk count
- [x] 3.2 Add a “process document” action for supported uploaded documents
- [x] 3.3 Add frontend feedback for processing success, failure, and reprocessing results without exposing sensitive backend details

## 4. Security and Documentation

- [x] 4.1 Verify document reads remain constrained to the configured storage root during ingestion
- [x] 4.2 Verify failure messages do not expose sensitive server paths or backend secrets
- [x] 4.3 Update `README.md` with the document ingestion flow, current parser support, and known limitations

## 5. Validation

- [x] 5.1 Add backend tests for successful ingestion, failed ingestion, reprocessing chunk replacement, owner scoping, and status transitions
- [x] 5.2 Run backend tests or startup checks and frontend type/build checks for the ingestion-enabled project detail workflow
