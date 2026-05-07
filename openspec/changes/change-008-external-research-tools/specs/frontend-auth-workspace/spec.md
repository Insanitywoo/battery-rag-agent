## MODIFIED Requirements

### Requirement: Frontend MAY provide only bounded project research workspace extensions in this change
The frontend SHALL provide a functional project-detail route for the authenticated owner that includes knowledge-base, chat, Agent, Paper Writing, and External References entry points, and it SHALL provide a project-scoped External References page for bounded metadata search, save, delete, and BibTeX export flows, but it MUST remain limited to project research tooling scope and MUST NOT implement unrestricted crawling or open-ended external automation workflows.

#### Scenario: Project workspace includes external reference controls
- **WHEN** an authenticated owner uses the project workspace after this change
- **THEN** the frontend SHALL provide an External References workspace with search, candidate review, save, delete, and BibTeX export controls, and SHALL exclude unrelated automation workflows

### Requirement: Frontend external-reference flows SHALL use authenticated backend-only execution
The frontend SHALL call backend external-reference and BibTeX endpoints with `credentials: "include"` and SHALL render candidate and saved reference metadata without exposing provider secrets or browser-stored tokens.

#### Scenario: External search request uses cookie-authenticated fetch
- **WHEN** the frontend sends a project external-reference search request
- **THEN** the request SHALL use authenticated backend calls with `credentials: "include"`

#### Scenario: Frontend never exposes provider secrets for external tools
- **WHEN** the external-references implementation is reviewed
- **THEN** it SHALL not store scholarly-provider API keys in the browser and SHALL not call provider APIs directly from the frontend
