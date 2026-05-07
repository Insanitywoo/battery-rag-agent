# project-paper-writing-assistant Specification

## Purpose
Define a bounded project-scoped paper-writing assistant so authenticated owners can generate evidence-grounded writing artifacts inside their own project without enabling unrestricted paper ghostwriting or cross-user data access.

## Requirements

### Requirement: The system SHALL provide a project-scoped paper-writing assistant
The system SHALL provide a bounded paper-writing assistant for authenticated owners inside projects they own, and the assistant SHALL generate evidence-grounded writing artifacts rather than unrestricted paper ghostwriting output.

#### Scenario: Authenticated owner runs a writing task
- **WHEN** an authenticated owner submits a supported writing task inside a project they own
- **THEN** the system SHALL generate a bounded writing result within that owner and project scope

### Requirement: Writing artifacts SHALL be persisted as owner-scoped project records
The system SHALL persist each generated writing result as a `writing_artifacts` record bound to `user_id` and `project_id`.

#### Scenario: Writing artifact is stored
- **WHEN** an authenticated owner generates a writing result
- **THEN** the system SHALL store the artifact type, title, Markdown content, sources, unsupported claims, and timestamps for that owner and project

### Requirement: Writing results SHALL preserve Markdown content, sources, and unsupported claims
Every saved writing artifact in this capability SHALL preserve `content_markdown`, `sources_json`, and `unsupported_claims_json` so the user can review grounded content and unsupported areas later.

#### Scenario: Saved artifact includes evidence context
- **WHEN** a writing result is persisted
- **THEN** the artifact SHALL include Markdown content plus source references and unsupported-claim data tied to that result

### Requirement: Writing generation SHALL remain evidence-first
Writing-oriented outputs SHALL be grounded in current project evidence, SHALL mark unsupported conclusions as needing manual confirmation, and SHALL NOT fabricate references, experiments, results, or citations.

#### Scenario: Unsupported writing claims are marked explicitly
- **WHEN** a writing-oriented Skill lacks enough evidence for part of the generated result
- **THEN** the returned artifact SHALL identify unsupported claims or manual-confirmation warnings rather than inventing support

### Requirement: Writing prompts SHALL include explicit anti-fabrication and source instructions
The backend writing prompts in this capability SHALL include system instruction, the user writing task, retrieved evidence chunks, a requirement to surface sources, a requirement to surface unsupported claims, and a prohibition against fabricated literature references or fabricated results.

#### Scenario: Prompt contains bounded writing instructions
- **WHEN** the backend assembles a writing prompt
- **THEN** the prompt SHALL contain the current writing task, retrieved project evidence, source requirements, unsupported-claim requirements, and explicit anti-fabrication guidance

### Requirement: Writing artifacts SHALL be listable, viewable, deletable, and exportable only by the owner
The system SHALL allow the authenticated owner to list, read, delete, and export only their own writing artifacts inside the current project.

#### Scenario: Owner lists writing artifacts
- **WHEN** an authenticated owner requests writing artifacts for a project they own
- **THEN** the system SHALL return only that owner's writing artifacts for that project

#### Scenario: Cross-user writing access is blocked
- **WHEN** a user attempts to view, delete, or export another user's writing artifact
- **THEN** the system SHALL reject the request and SHALL NOT expose the other user's writing content, sources, or unsupported claims

### Requirement: Markdown export SHALL remain owner-scoped and artifact-scoped
The system SHALL support exporting one writing artifact as Markdown, and the exported content SHALL only contain the current owner's current project artifact data.

#### Scenario: Owner exports one Markdown artifact
- **WHEN** an authenticated owner exports a writing artifact in a project they own
- **THEN** the returned Markdown content SHALL correspond only to that artifact and SHALL not contain another user's data

### Requirement: Writing assistant SHALL support bounded reuse of saved external references
The writing assistant in this capability MAY reuse saved project-scoped `external_references` for related-work-oriented and citation-support-oriented writing flows, but it SHALL label them explicitly as external references and SHALL not treat them as uploaded-document evidence.

#### Scenario: Related-work drafting uses saved external references safely
- **WHEN** an authenticated owner generates a related-work-oriented or citation-support-oriented writing artifact
- **THEN** the writing assistant MAY incorporate saved external references with explicit external labeling while preserving the distinction from internal project evidence
