## 1. Backend Storage Foundation

- [x] 1.1 Add backend storage configuration, environment defaults, and repository ignore rules for local file storage
- [x] 1.2 Define the document persistence model and status representation with explicit `user_id` and `project_id` ownership fields
- [x] 1.3 Add backend storage utilities for filename sanitization, extension and MIME validation, file-size checks, local save, and local delete behavior

## 2. Backend Document APIs

- [x] 2.1 Implement document upload for an authenticated user under an owned project
- [x] 2.2 Implement owner-scoped document list and document detail endpoints bound to both `user_id` and `project_id`
- [x] 2.3 Implement document deletion that removes both the database record and the local stored file
- [x] 2.4 Reject unauthenticated, cross-user, invalid-extension, invalid-MIME, and oversized upload requests

## 3. Frontend Project Document Workspace

- [x] 3.1 Replace the project-detail placeholder with an authenticated project document workspace
- [x] 3.2 Add a file upload form on the project detail page for allowed file types only
- [x] 3.3 Add a file list and delete action that operate only on the current user's selected project

## 4. Security and Documentation

- [x] 4.1 Verify uploaded filenames and storage paths are handled safely and cannot escape the configured storage root
- [x] 4.2 Verify frontend code and browser-exposed configuration do not contain backend secrets or sensitive storage credentials
- [x] 4.3 Update `README.md` and `.env.example` with storage configuration and local usage guidance
- [x] 4.4 Ensure the local `storage` directory or equivalent configured storage root is not committed to Git

## 5. Validation

- [x] 5.1 Add backend tests for upload, list, detail, delete, owner scoping, type validation, and file-size validation
- [x] 5.2 Run backend tests or startup checks and frontend type/build checks for the implemented document workspace
