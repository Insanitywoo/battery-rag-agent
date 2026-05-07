# frontend-auth-workspace Specification

## Purpose
Define the authenticated frontend workspace for Battery-RAG Agent, including auth entry points, owner-scoped project workflows, and project-scoped RAG chat interaction.

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

### Requirement: Frontend MAY provide only bounded project research workspace extensions in this change
The frontend SHALL provide a functional project-detail route for the authenticated owner that includes knowledge-base, chat, Agent, Paper Writing, and External References entry points, and it SHALL provide a project-scoped External References page for bounded metadata search, save, delete, and BibTeX export flows, but it MUST remain limited to project research tooling scope and MUST NOT implement unrestricted crawling or open-ended external automation workflows.

#### Scenario: Project workspace includes external reference controls
- **WHEN** an authenticated owner uses the project workspace after this change
- **THEN** the frontend SHALL provide an External References workspace with search, candidate review, save, delete, and BibTeX export controls, and SHALL exclude unrelated automation workflows

### Requirement: Frontend Paper Writing SHALL use authenticated backend-only execution
The frontend SHALL call backend writing-assistant endpoints with `credentials: "include"` and SHALL render saved writing artifacts without exposing provider secrets or browser-stored tokens.

#### Scenario: Writing request uses cookie-authenticated fetch
- **WHEN** the frontend sends a project writing request
- **THEN** the request SHALL use authenticated backend calls with `credentials: "include"`

#### Scenario: Frontend never exposes provider secrets for writing assistant execution
- **WHEN** the project writing implementation is reviewed
- **THEN** it SHALL not store model API keys in the browser and SHALL not call model providers directly from the frontend

### Requirement: Frontend project Agent SHALL use authenticated backend-only execution
The frontend SHALL call backend Agent endpoints with `credentials: "include"` and SHALL render structured Agent task results without exposing provider secrets or browser-stored tokens.

#### Scenario: Agent request uses cookie-authenticated fetch
- **WHEN** the frontend sends a project Agent request
- **THEN** the request SHALL use authenticated backend calls with `credentials: "include"`

#### Scenario: Frontend never exposes provider secrets for Agent execution
- **WHEN** the project Agent implementation is reviewed
- **THEN** it SHALL not store model API keys in the browser and SHALL not call model providers directly from the frontend

### Requirement: Frontend external-reference flows SHALL use authenticated backend-only execution
The frontend SHALL call backend external-reference and BibTeX endpoints with `credentials: "include"` and SHALL render candidate and saved reference metadata without exposing provider secrets or browser-stored tokens.

#### Scenario: External search request uses cookie-authenticated fetch
- **WHEN** the frontend sends a project external-reference search request
- **THEN** the request SHALL use authenticated backend calls with `credentials: "include"`

#### Scenario: Frontend never exposes provider secrets for external tools
- **WHEN** the external-references implementation is reviewed
- **THEN** it SHALL not store scholarly-provider API keys in the browser and SHALL not call provider APIs directly from the frontend

### Requirement: Frontend project chat SHALL use authenticated streaming requests only
The frontend SHALL call the backend streaming chat endpoint with `credentials: "include"` and SHALL render assistant output incrementally without storing provider secrets or tokens in browser storage.

#### Scenario: Streaming chat uses cookie-authenticated fetch
- **WHEN** the frontend sends a project chat request
- **THEN** the request SHALL use `fetch` `ReadableStream` or equivalent streaming support with `credentials: "include"`

#### Scenario: Frontend never stores model secrets or access tokens for chat
- **WHEN** the project chat implementation is reviewed
- **THEN** it SHALL not store model API keys in the browser and SHALL not introduce token persistence beyond the existing HttpOnly cookie approach

### Requirement: Frontend project chat SHALL support owner-scoped session history
The frontend SHALL let the authenticated owner view their project chat list, reopen a prior session, continue asking follow-up questions, and delete their own chat sessions.

#### Scenario: User reopens a historical project session
- **WHEN** an authenticated owner selects one of their prior sessions in a project
- **THEN** the frontend SHALL display that session's message history and allow continued chat within it

#### Scenario: User deletes one of their project sessions
- **WHEN** an authenticated owner deletes a session from the chat list
- **THEN** the frontend SHALL remove that session from the visible history after successful backend confirmation

### Requirement: Frontend SHALL not embed backend secrets or sensitive service keys
The frontend MUST NOT store backend JWT secrets, provider API keys, or other server-side sensitive keys in client code, browser-exposed configuration, or frontend environment variables.

#### Scenario: Frontend configuration remains non-secret
- **WHEN** frontend code and browser-exposed configuration are reviewed
- **THEN** no backend signing secret or provider secret SHALL be present in client-accessible code or configuration
