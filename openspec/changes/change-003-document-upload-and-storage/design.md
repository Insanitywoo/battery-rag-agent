## Context

Battery-RAG Agent already supports Cookie-based user authentication and owner-scoped research projects, but the project workspace still stops at metadata. The next safe increment is to let a user place source files inside a project without yet parsing them. This gives later changes a stable base for document processing, chunking, embeddings, retrieval, and downstream agent workflows.

This change crosses several boundaries:

- The backend must accept multipart uploads and persist document metadata.
- The system must save raw files to a configured local storage root.
- The project workspace must expand from metadata-only detail into minimal file management.
- Security controls must cover ownership, path safety, type validation, size validation, and repository hygiene.

Primary constraints:

- Only authenticated users may upload files.
- Every document must be bound to both `user_id` and `project_id`.
- Every document API must validate current user ownership through the containing project and document record.
- Allowed file types are limited to `PDF`, `TXT`, `MD`, and `CSV`.
- File extension and MIME type must both be validated.
- File names must be sanitized and storage paths must prevent path traversal.
- Raw storage remains local filesystem storage only in this change.
- No parsing, chunking, embedding, OCR, vector DB writes, RAG, Agent, or Skills behavior may be introduced.

## Goals / Non-Goals

**Goals:**

- Provide a minimal but complete project-level document storage workflow.
- Persist document metadata in the relational database with explicit ownership fields.
- Persist uploaded file bytes in a configured local storage directory.
- Expose owner-scoped upload, list, detail, and delete APIs.
- Turn the frontend project detail page into a minimal file workspace that supports upload, list, and delete.
- Document storage configuration and keep storage artifacts out of Git.

**Non-Goals:**

- PDF text extraction or document parsing.
- Text chunking, embeddings, or Qdrant integration.
- RAG question answering, chat, or citation workflows.
- Agent orchestration or Skills execution.
- Cloud object storage, signed URLs, or CDN delivery.
- OCR, antivirus scanning, or remote literature fetching.

## Decisions

### Decision: Introduce a dedicated `Document` metadata model now

This change should add a first-class document entity instead of storing files implicitly under projects. The document record gives later processing changes a stable object to attach parsing state, processing failures, derived chunks, and retrieval metadata to.

Planned fields:

- `id`
- `user_id`
- `project_id`
- `filename`
- `original_filename`
- `file_type`
- `mime_type`
- `file_size`
- `storage_path`
- `status`
- `created_at`
- `updated_at`

The initial status lifecycle remains bounded to:

- `uploaded`
- `processing`
- `processed`
- `failed`

Even though this change does not implement processing, defining the status field now prevents a later schema reshape.

### Decision: Store raw files on the local filesystem and metadata in the database

Raw files should be written to a configurable backend storage root on local disk, while the database stores the authoritative metadata and ownership bindings. This preserves a clear separation:

- filesystem for bytes
- database for identity, ownership, and state

This is the smallest practical storage model for local development and early product iterations. Cloud object storage is intentionally deferred.

### Decision: Use safe generated storage names and sanitize user-facing filenames

Uploaded filenames must never be used directly as filesystem paths. The system should preserve a sanitized `original_filename` for UI display, but the stored file path should be generated from server-controlled identifiers such as UUIDs plus a validated extension. This prevents path traversal, reserved-name issues, and collisions.

### Decision: Enforce authorization at both project and document boundaries

Document access control should not rely on UI filtering alone. Every document API must:

1. resolve the current authenticated user from the auth Cookie
2. validate that the target project belongs to that user
3. scope document retrieval and deletion to both `user_id` and `project_id`

This double scoping blocks cross-user and cross-project access even if an attacker guesses a document identifier.

### Decision: Validate both extension and MIME type, and enforce a configured file-size ceiling

The upload contract should allow only `pdf`, `txt`, `md`, and `csv`. Validation should check:

- declared filename extension
- incoming MIME type
- configured maximum file size

This is not a full content-security solution, but it is an appropriate baseline for a bounded MVP file-ingestion step.

Recommended storage-related configuration:

- `STORAGE_ROOT`
- `MAX_UPLOAD_SIZE_BYTES`
- `ALLOWED_UPLOAD_EXTENSIONS`
- `ALLOWED_UPLOAD_MIME_TYPES`

### Decision: Expand project detail into a minimal document workspace

The frontend project detail page should now become functional, but only for file management. It may show:

- project metadata
- file upload form
- file list
- file delete action
- per-file status and metadata

It must still exclude:

- parsing previews
- chunk browsers
- vector search
- RAG chat
- Agent tasks

## Risks / Trade-offs

- [Local filesystem storage is not horizontally scalable] -> acceptable for the current change because cloud object storage is explicitly out of scope.
- [Extension and MIME validation are helpful but not complete content inspection] -> acceptable for this bounded MVP, while keeping stronger scanning options open for later changes.
- [Project detail page complexity grows] -> controlled by keeping the page limited to metadata and file management only.
- [Delete flow must stay consistent across DB and filesystem] -> implementation should define a single delete path that removes both metadata and the raw file, with tests covering consistency.

## Migration Plan

This is an additive change on top of the authenticated project workspace.

Suggested rollout order:

1. Add storage-related configuration and ignore rules.
2. Add document model and status representation.
3. Add backend storage utilities for validation, save, lookup, and delete.
4. Add owner-scoped document APIs under project context.
5. Expand frontend project detail into the minimal document workspace.
6. Update docs and validate upload, list, detail, delete, invalid type, invalid size, and cross-user rejection paths.

Rollback path:

- remove the document model, storage utilities, and document APIs
- restore project detail to its placeholder behavior
- leave auth and project workspace capabilities untouched

## Open Questions

- Should duplicate filenames within the same project remain allowed as long as storage filenames are server-generated?
- Should delete be hard delete only in this change, or is a future soft-delete/archive state likely to be needed for research traceability?
