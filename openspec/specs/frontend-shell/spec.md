# frontend-shell

## Purpose

Define the baseline frontend application shell for Battery-RAG Agent so future product interfaces can grow on a stable Next.js structure.
## Requirements
### Requirement: Frontend SHALL use Next.js, React, and Tailwind CSS
The frontend shell SHALL be scaffolded with Next.js and React, and it SHALL include Tailwind CSS in its baseline setup so that future product UI work can build on the agreed web stack.

#### Scenario: Frontend stack matches project constraints
- **WHEN** a developer inspects the frontend shell configuration
- **THEN** the frontend SHALL be identifiable as a Next.js and React application with Tailwind CSS configured as part of the shell

### Requirement: Frontend SHALL provide a landing page placeholder
The frontend shell SHALL include a publicly reachable landing page placeholder that communicates the project identity of Battery-RAG Agent without implementing production product content.

#### Scenario: Landing page exists
- **WHEN** the frontend shell is started and the root route is opened
- **THEN** the application SHALL render a landing page placeholder for Battery-RAG Agent

### Requirement: Frontend SHALL provide a dashboard placeholder route
The frontend shell SHALL provide a dashboard route that can evolve from a placeholder into an authenticated personal workspace page, and this change MAY implement the logged-in dashboard experience needed for user auth and project workspace flows.

#### Scenario: Dashboard route supports authenticated workspace
- **WHEN** the frontend is reviewed after this change
- **THEN** the dashboard route SHALL be allowed to represent an authenticated user workspace rather than a placeholder-only screen

### Requirement: Frontend shell SHALL avoid premature business workflows
The frontend shell MUST NOT implement document workflows, chat experiences, RAG interfaces, Agent task flows, or other out-of-scope product capabilities in this change, but it MAY implement login, registration, dashboard, project list, and create-project flows required for the personal user workspace.

#### Scenario: Frontend scope is limited to auth and workspace flows
- **WHEN** the frontend shell is reviewed
- **THEN** product-facing pages introduced by this change SHALL be limited to authentication and personal project workspace flows, and SHALL exclude document, RAG, Agent, and Skills experiences

### Requirement: Frontend SHALL support a bounded production container path
The frontend shell SHALL support a production-oriented container build and runtime path suitable for single-node public-beta deployment, without expanding into unrelated product capabilities.

#### Scenario: Frontend production build path is documented
- **WHEN** an operator prepares the frontend for public-beta deployment
- **THEN** the repository SHALL provide a frontend production container path and documented build or runtime expectations

### Requirement: Frontend production deployment SHALL not expose backend secrets
The frontend production deployment path SHALL continue to avoid exposing backend JWT secrets, model provider keys, or other server-only secrets through client-visible environment variables or deployment docs.

#### Scenario: Frontend production env remains non-secret
- **WHEN** frontend deployment assets are reviewed
- **THEN** no server-only secret SHALL be documented as a client-side runtime value
