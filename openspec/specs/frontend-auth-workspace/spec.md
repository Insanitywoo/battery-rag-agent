# frontend-auth-workspace Specification

## Purpose
TBD - created by archiving change change-002-auth-and-user-workspace. Update Purpose after archive.
## Requirements
### Requirement: Frontend SHALL provide user registration and login pages
The frontend SHALL provide dedicated registration and login pages that let users submit credentials to the backend authentication flow.

#### Scenario: Registration page is available
- **WHEN** a user navigates to the registration route
- **THEN** the frontend SHALL render a registration form for account creation

#### Scenario: Login page is available
- **WHEN** a user navigates to the login route
- **THEN** the frontend SHALL render a login form for account authentication

### Requirement: Frontend SHALL use Cookie-based auth transport for protected requests
The frontend SHALL rely on the backend-set HttpOnly auth Cookie for authenticated API access, SHALL send protected requests using `credentials: "include"`, and MUST NOT persist the JWT token in `localStorage` or `sessionStorage`.

#### Scenario: Protected request includes credentials
- **WHEN** the frontend calls a protected API after login
- **THEN** the request SHALL be sent with `credentials: "include"`

#### Scenario: Frontend avoids browser token storage
- **WHEN** frontend auth handling is reviewed
- **THEN** the JWT access token SHALL NOT be stored in `localStorage` or `sessionStorage`

### Requirement: Frontend SHALL provide a logged-in dashboard experience
The frontend SHALL provide a dashboard experience intended for authenticated users after successful login.

#### Scenario: Authenticated user reaches dashboard
- **WHEN** a user successfully authenticates
- **THEN** the frontend SHALL present the dashboard experience for that user workspace

### Requirement: Frontend SHALL provide a project list page and create-project form
The frontend SHALL provide a project workspace that includes a project list view for the current user and a form to create a new project.

#### Scenario: Project list page is available
- **WHEN** an authenticated user navigates to the project workspace
- **THEN** the frontend SHALL display the current user's project list view

#### Scenario: Create-project form is available
- **WHEN** an authenticated user enters the project creation flow
- **THEN** the frontend SHALL render a form for creating a new project

### Requirement: Frontend MAY provide only a reserved project-detail entry point in this change
The frontend SHALL provide a functional project-detail route for the authenticated owner that includes document ingestion controls, document processing status, and chunk-count display for that project, but it MUST remain limited to document-management and ingestion scope and MUST NOT implement embeddings, vector search, RAG, Agent, or Skills workflows.

#### Scenario: Project-detail route becomes a minimal ingestion workspace
- **WHEN** an authenticated owner enters the project-detail route from the project list
- **THEN** the frontend SHALL render the project-level ingestion workspace with upload/list/delete plus processing controls and status feedback, and SHALL exclude downstream research workflows

### Requirement: Frontend SHALL not embed backend secrets or sensitive service keys
The frontend MUST NOT store backend JWT secrets, provider API keys, or other server-side sensitive keys in client code, browser-exposed configuration, or frontend environment variables.

#### Scenario: Frontend configuration remains non-secret
- **WHEN** frontend code and browser-exposed configuration are reviewed
- **THEN** no backend signing secret or provider secret SHALL be present in client-accessible code or configuration

