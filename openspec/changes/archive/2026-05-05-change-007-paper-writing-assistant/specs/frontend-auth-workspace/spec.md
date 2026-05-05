## MODIFIED Requirements

### Requirement: Frontend MAY provide only a reserved project-detail entry point in this change
The frontend SHALL provide a functional project-detail route for the authenticated owner that includes knowledge-base build status, a project-chat entry point, a project-Agent entry point, and a project Paper Writing entry point, and it SHALL provide a project-scoped Paper Writing page for bounded writing assistance, but it MUST remain limited to project RAG chat plus bounded Agent, Skills, and writing-assistant scope and MUST NOT implement external tools or open-ended automation workflows.

#### Scenario: Project workspace includes knowledge-base, chat, Agent, and writing controls
- **WHEN** an authenticated owner uses the project workspace after this change
- **THEN** the frontend SHALL provide knowledge-base build or rebuild controls, a project-scoped chat interface, a project-scoped Agent interface, and a project-scoped writing interface with artifact history and export controls, and SHALL exclude unrelated automation workflows

### Requirement: Frontend Paper Writing SHALL use authenticated backend-only execution
The frontend SHALL call backend writing-assistant endpoints with `credentials: "include"` and SHALL render saved writing artifacts without exposing provider secrets or browser-stored tokens.

#### Scenario: Writing request uses cookie-authenticated fetch
- **WHEN** the frontend sends a project writing request
- **THEN** the request SHALL use authenticated backend calls with `credentials: "include"`

#### Scenario: Frontend never exposes provider secrets for writing assistant execution
- **WHEN** the project writing implementation is reviewed
- **THEN** it SHALL not store model API keys in the browser and SHALL not call model providers directly from the frontend
