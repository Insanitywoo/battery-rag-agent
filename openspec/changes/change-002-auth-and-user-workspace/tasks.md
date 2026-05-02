## 1. Backend Auth Foundation

- [x] 1.1 Add backend configuration and dependencies for relational persistence, password hashing, and JWT signing
- [x] 1.2 Define user and project persistence models with explicit ownership fields and future-ready structure
- [x] 1.3 Add database/session initialization needed for auth and project workspace APIs

## 2. Backend Authentication APIs

- [x] 2.1 Implement user registration with uniqueness checks and hashed password storage
- [x] 2.2 Implement user login that validates credentials, issues a JWT access token, and sets it via HttpOnly Cookie
- [x] 2.3 Implement logout, current-user resolution from Cookie-based auth, and a current-user profile endpoint
- [x] 2.4 Enforce environment-backed JWT secret and cookie settings, and reject invalid or missing auth cookies on protected routes

## 3. Backend Project Workspace APIs

- [x] 3.1 Implement create-project endpoint bound to the authenticated user as owner
- [x] 3.2 Implement current-user project list endpoint with owner-scoped filtering
- [x] 3.3 Implement project detail endpoint with ownership validation
- [x] 3.4 Implement project deletion endpoint with ownership validation

## 4. Frontend Auth Experience

- [x] 4.1 Add frontend login and registration pages wired to backend auth endpoints
- [x] 4.2 Add frontend authenticated session handling using Cookie-based auth with `credentials: "include"` and without storing tokens in browser storage
- [x] 4.3 Update the dashboard route to serve as the logged-in personal workspace entry point

## 5. Frontend Project Workspace

- [x] 5.1 Add a project list page that loads only the current user's projects
- [x] 5.2 Add a create-project form that submits new projects for the authenticated user
- [x] 5.3 Add a project-detail entry from the project list and, if needed, a project detail placeholder page reserved for change-003 without implementing document, knowledge base, RAG, Agent, or Skills workflows

## 6. Security and Validation

- [x] 6.1 Verify plaintext passwords are never stored or returned by backend APIs
- [x] 6.2 Verify frontend code and browser-exposed configuration do not contain backend secrets
- [x] 6.3 Verify unauthorized and cross-user project access paths are rejected
- [x] 6.4 Update documentation and environment examples for the auth and project workspace setup
