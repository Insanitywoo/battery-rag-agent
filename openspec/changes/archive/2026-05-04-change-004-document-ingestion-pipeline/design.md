## Context

Battery-RAG Agent already supports authenticated users, owner-scoped projects, and project-level raw document storage. The next increment is not retrieval yet, but ingestion: converting stored source files into clean, structured chunks that later embedding and retrieval changes can consume.

This change crosses several boundaries:

- The backend must read already-stored files from the configured storage root.
- The system must parse supported document types into text without executing any user content.
- The system must normalize and split parsed text into deterministic chunks.
- Chunks must be persisted with explicit ownership and document lineage.
- The frontend project detail page must show ingestion state and allow an owner to trigger or re-trigger processing.

Primary constraints:

- Only authenticated users may trigger ingestion.
- A user may only ingest documents inside projects they own.
- Chunk rows must always carry `user_id`, `project_id`, and `document_id`.
- File reads must stay inside the configured storage root.
- Processing failures must not expose sensitive server paths.
- The ingestion pipeline must not introduce embeddings, vector DB writes, RAG, Agent, Skills, OCR, image parsing, or async queue infrastructure.

## Goals / Non-Goals

**Goals:**

- Provide a synchronous, owner-scoped document processing path for already-uploaded files.
- Parse PDF text while preserving page-number lineage.
- Parse TXT and Markdown as raw textual content.
- Handle CSV in a bounded way by exposing simple text preview or metadata-oriented ingestion only.
- Clean parsed text before chunking.
- Split text into chunks using configurable `chunk_size` and `chunk_overlap`.
- Persist chunks with minimal but useful metadata for later embedding work.
- Support reprocessing by removing prior chunks before storing new ones.
- Surface document status and chunk counts in the project detail UI.

**Non-Goals:**

- Embedding generation.
- Qdrant or any vector index integration.
- Vector search or RAG answering.
- Agent orchestration or Skills execution.
- OCR or image/PDF scan interpretation.
- Complex table reconstruction for CSV or PDF.
- Celery or any other async queue/worker system.

## Decisions

### Decision: Introduce a dedicated `DocumentChunk` model now

Chunk persistence should be explicit rather than embedded into ad hoc JSON fields on the document record. A first-class chunk model gives later changes a stable place to attach embeddings, retrieval metadata, ranking state, and source references.

Planned fields:

- `id`
- `user_id`
- `project_id`
- `document_id`
- `page_number`
- `chunk_index`
- `content`
- `char_count`
- `created_at`

### Decision: Extend the existing `Document` model with ingestion lifecycle fields

The current document record already owns storage metadata and coarse status. This change should extend it with:

- `error_message`
- `processed_at`
- `chunk_count`

The document status lifecycle remains:

- `uploaded`
- `processing`
- `processed`
- `failed`

Ingestion behavior should update status as follows:

1. set `processing` before parsing starts
2. clear prior chunks when reprocessing begins
3. set `processed`, `processed_at`, and `chunk_count` on success
4. set `failed` and a sanitized `error_message` on failure

### Decision: Parse files from local storage only after re-validating the resolved path

The ingestion pipeline must never trust the stored relative path blindly. Even though upload already constrains paths, ingestion should resolve the file path again against `STORAGE_ROOT` before reading. This preserves the same storage-root boundary for the read path as for the write path.

### Decision: Use bounded parsing strategies per file type

Supported handling in this change:

- `PDF`: extract page text and preserve `page_number`
- `TXT`: read as plain text
- `MD`: read as plain text/markdown source
- `CSV`: do not attempt complex table semantics; allow only simple textual preview or metadata-oriented ingestion

This keeps ingestion deterministic while avoiding premature complexity around OCR, scanned PDFs, or structured table semantics.

### Decision: Clean text before chunking, then use character-based chunking with overlap

The baseline pipeline should:

1. normalize line endings
2. trim redundant whitespace
3. collapse obvious repeated blank lines
4. discard empty parse results

Then split content with backend-configured defaults:

- `CHUNK_SIZE=1000`
- `CHUNK_OVERLAP=150`

Character-based chunking is sufficient for this stage because the goal is stable persistence, not semantic optimization.

### Decision: Reprocessing should replace old chunks atomically within the same document workflow

If a user reprocesses a document, the system should delete existing chunks for that document before inserting the new chunk set. This avoids stale chunk duplication and keeps `chunk_count` aligned with the current document representation.

### Decision: Extend the project-detail UI without introducing downstream research workflows

The project detail page may now show:

- document status
- document chunk count
- “process document” action
- updated success or failure feedback

It must still exclude:

- chunk inspection browsers beyond basic counts/status
- embeddings
- vector search
- RAG QA
- agent workflows

## Risks / Trade-offs

- [Synchronous processing may be slower for large PDFs] -> acceptable for this change because async workers are explicitly out of scope.
- [PDF extraction quality varies by source document] -> acceptable as a first-pass ingestion baseline, while leaving OCR and richer parsing for later changes.
- [Character chunking is not semantically perfect] -> acceptable because the immediate goal is persistence and stable downstream foundations.
- [Reprocessing can temporarily drop old chunks before new chunks are written] -> should be handled inside a controlled transaction flow so the final persisted state stays consistent.
- [Failure messages may leak internal details if not sanitized] -> implementation should ensure error text is user-safe and excludes sensitive absolute paths.

## Migration Plan

This is an additive change on top of document upload/storage.

Suggested rollout order:

1. Add ingestion-related configuration defaults.
2. Extend the document model and add the chunk model.
3. Add parsing, cleaning, and chunking services.
4. Add processing trigger APIs with owner-scoped authorization.
5. Add reprocessing behavior that clears old chunks first.
6. Extend the frontend project detail page with process controls and ingestion status display.
7. Update README and validate success, failure, reprocessing, and cross-user rejection paths.

Rollback path:

- remove the chunk model and ingestion services
- remove ingestion fields from the document flow
- restore project detail to upload/list/delete only
- leave upload/storage behavior intact

## Open Questions

- Should CSV ingestion persist a single preview chunk, or should it be allowed to produce multiple text chunks if the raw preview grows large?
- Should future changes preserve both raw parsed page text and cleaned chunk text separately, or is cleaned chunk content sufficient for the near-term roadmap?
