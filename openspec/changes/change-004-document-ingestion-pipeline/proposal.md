## Why

Battery-RAG Agent can now store project documents safely, but those files are still opaque blobs. Before we can generate embeddings, write vectors, or answer RAG questions, the system needs a deterministic ingestion pipeline that can parse supported documents, clean text, split it into chunks, and persist those chunks under the correct user, project, and document boundaries.

## What Changes

- Add backend document-ingestion APIs that let an authenticated project owner trigger processing for an uploaded document.
- Extend document persistence with ingestion outcome fields such as `processed_at`, `chunk_count`, and `error_message`.
- Add a `document_chunks` persistence model bound to `user_id`, `project_id`, and `document_id`.
- Implement parsing support for PDF, TXT, and Markdown documents, and bounded CSV handling for metadata or simple text preview.
- Implement text cleaning and configurable character-based chunking with overlap.
- Clear prior chunks before reprocessing a document and replace them with the latest ingestion result.
- Update document status transitions so successful ingestion ends in `processed` and failures end in `failed`.
- Extend the frontend project detail page to show processing status, chunk count, and a “process document” action.
- Update README to describe the ingestion flow and its current limits.
- **BREAKING**: Document workflows will no longer stop at upload/delete; project documents can now enter an ingestion lifecycle with chunk persistence.

## Capabilities

### New Capabilities

- `document-ingestion-pipeline`: Defines owner-scoped document parsing, cleaning, chunk generation, ingestion status transitions, and chunk persistence behavior.

### Modified Capabilities

- `backend-shell`: Expands accepted backend scope from document storage only to document storage plus ingestion and chunk persistence APIs.
- `project-document-storage`: Extends stored documents from upload metadata only into ingestion-aware document records with processing lifecycle fields.
- `user-project-workspace`: Expands project detail to surface document processing state and chunk counts while remaining within owner-scoped document workflows.
- `frontend-auth-workspace`: Extends the project-detail route to trigger ingestion and display ingestion outcomes for the current user’s project documents.

## Impact

- Affected code: backend document model, parsing/cleaning/chunking services, document APIs, chunk persistence, frontend project detail UI, and README documentation.
- Affected APIs: new processing trigger endpoints and updated document detail/list payloads with ingestion fields.
- Affected systems: PostgreSQL metadata persistence, local file reads from the storage root, ingestion status lifecycle, and chunk data foundation for future embeddings.
- Dependencies likely introduced or activated: PDF text extraction library, text normalization helpers, and chunking configuration values.
