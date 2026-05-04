## MODIFIED Requirements

### Requirement: Frontend MAY provide only a reserved project-detail entry point in this change
The frontend SHALL provide a functional project-detail route for the authenticated owner that includes knowledge-base build status and a project-chat entry point, and it SHALL provide a project-scoped chat page for asking questions against that project's knowledge base, but it MUST remain limited to project RAG chat scope and MUST NOT implement Agent or Skills workflows.

#### Scenario: Project workspace includes knowledge-base controls and chat
- **WHEN** an authenticated owner uses the project workspace after this change
- **THEN** the frontend SHALL provide knowledge-base build or rebuild controls plus a project-scoped chat interface with cited answers, and SHALL exclude unrelated automation workflows

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
