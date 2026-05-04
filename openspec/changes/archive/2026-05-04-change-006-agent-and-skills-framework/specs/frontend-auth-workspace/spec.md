## MODIFIED Requirements

### Requirement: Frontend MAY provide only a reserved project-detail entry point in this change
The frontend SHALL provide a functional project-detail route for the authenticated owner that includes knowledge-base build status, a project-chat entry point, and a project-Agent entry point, and it SHALL provide a project-scoped Agent page for submitting bounded research tasks, but it MUST remain limited to project RAG chat plus bounded Agent and Skills scope and MUST NOT implement external tools or open-ended automation workflows.

#### Scenario: Project workspace includes knowledge-base, chat, and Agent controls
- **WHEN** an authenticated owner uses the project workspace after this change
- **THEN** the frontend SHALL provide knowledge-base build or rebuild controls, a project-scoped chat interface, and a project-scoped Agent interface with structured results, and SHALL exclude unrelated automation workflows

### Requirement: Frontend project Agent SHALL use authenticated backend-only execution
The frontend SHALL call backend Agent endpoints with `credentials: "include"` and SHALL render structured Agent task results without exposing provider secrets or browser-stored tokens.

#### Scenario: Agent request uses cookie-authenticated fetch
- **WHEN** the frontend sends a project Agent request
- **THEN** the request SHALL use authenticated backend calls with `credentials: "include"`

#### Scenario: Frontend never exposes provider secrets for Agent execution
- **WHEN** the project Agent implementation is reviewed
- **THEN** it SHALL not store model API keys in the browser and SHALL not call model providers directly from the frontend
