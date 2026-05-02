## Why

Battery-RAG Agent now has authenticated users and owner-scoped research projects, but projects still cannot hold source files. Before we can parse documents, build knowledge bases, or answer RAG questions, the system needs a safe project-level file management foundation that lets users upload, view, and delete their own files.

## What Changes

- Add backend project-document upload, list, detail, and delete APIs for authenticated users.
- Add a document metadata model bound to both `user_id` and `project_id`.
- Store raw uploaded files in a local backend storage directory and persist metadata in the database.
- Enforce owner-scoped authorization for every document API through current-user and project ownership checks.
- Validate allowed file types (`pdf`, `txt`, `md`, `csv`), file size, MIME type, and safe filename handling.
- Extend the frontend project detail page from a placeholder into a minimal document workspace that supports file list, upload, and delete.
- Update `.env.example`, `README.md`, and repository ignore rules for local storage configuration.
- **BREAKING**: The project detail route will no longer be placeholder-only; it will become the minimal document-management workspace for a user's own project.

## Capabilities

### New Capabilities

- `project-document-storage`: Defines project-bound document upload, metadata persistence, local file storage, owner-scoped retrieval, and deletion behavior.

### Modified Capabilities

- `backend-shell`: Expands accepted backend scope from auth and project workspace only to auth, project workspace, and project document storage APIs.
- `user-project-workspace`: Expands project detail from metadata-only scope to include owner-scoped file management structure for that project.
- `frontend-auth-workspace`: Expands the project detail route from a placeholder reserve into a minimal authenticated document workspace.
- `local-dev-infra`: Extends local development configuration to document storage-related environment variables and ensure the storage directory is excluded from version control.

## Impact

- Affected code: backend document model, storage utilities, project detail APIs, frontend project detail UI, shared environment configuration, and documentation.
- Affected APIs: new document upload/list/detail/delete endpoints protected by Cookie-based auth and project ownership checks.
- Affected systems: local filesystem storage, database metadata persistence, project detail page behavior, and developer environment setup.
- Dependencies likely introduced or activated: multipart upload handling, MIME validation helpers, filesystem-safe path handling, and storage configuration values.
