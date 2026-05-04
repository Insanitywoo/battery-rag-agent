# user-project-workspace Specification

## Purpose
TBD - created by archiving change change-002-auth-and-user-workspace. Update Purpose after archive.
## Requirements
### Requirement: Authenticated users SHALL be able to create research projects
The system SHALL allow an authenticated user to create a research project record that is bound to that user as the owner.

#### Scenario: User creates a project
- **WHEN** an authenticated user submits valid project creation data
- **THEN** the system SHALL create a project whose `owner_id` or equivalent ownership field is bound to the current user

### Requirement: Authenticated users SHALL be able to list only their own projects
The system SHALL provide a project list capability that returns only projects owned by the current authenticated user.

#### Scenario: Project list is owner-scoped
- **WHEN** an authenticated user requests the project list
- **THEN** the system SHALL return only projects owned by that user

### Requirement: Authenticated users SHALL be able to retrieve their own project details
The system SHALL allow an authenticated user to retrieve details for a specific project only when the project is owned by that user.

#### Scenario: Owner retrieves project detail
- **WHEN** an authenticated user requests a project they own
- **THEN** the system SHALL return that project's details

#### Scenario: Non-owner cannot retrieve project detail
- **WHEN** an authenticated user requests a project owned by another user
- **THEN** the system SHALL reject the request

### Requirement: Project detail scope SHALL remain limited to project metadata in this change
The project detail capability introduced in this change SHALL expand from project metadata plus document-management structure into owner-scoped project metadata plus document ingestion controls and status display, and MUST NOT introduce embeddings, vector search, RAG, Agent, or Skills workflows.

#### Scenario: Project detail remains within project-and-ingestion-workspace scope
- **WHEN** project detail behavior is reviewed in this change
- **THEN** the returned or displayed detail scope SHALL remain limited to project metadata plus owner-scoped document ingestion workflow structure, and SHALL NOT expose embeddings, vectors, RAG, Agent, or Skills workflows

### Requirement: Authenticated users SHALL be able to delete only their own projects
The system SHALL allow an authenticated user to delete a project only when the project is owned by that user.

#### Scenario: Owner deletes project
- **WHEN** an authenticated user deletes a project they own
- **THEN** the system SHALL remove that project from the user's accessible workspace

#### Scenario: Non-owner cannot delete project
- **WHEN** an authenticated user attempts to delete a project owned by another user
- **THEN** the system SHALL reject the request

### Requirement: All project APIs SHALL enforce owner-bound access control
Every project API introduced in this change SHALL validate the current authenticated user and SHALL use project ownership checks to prevent cross-user access, modification, or deletion.

#### Scenario: Unauthenticated project request is rejected
- **WHEN** a client calls a project API without a valid authenticated user context
- **THEN** the system SHALL reject the request

#### Scenario: Cross-user project access is blocked
- **WHEN** a client attempts to access another user's project by identifier
- **THEN** the system SHALL reject the request and SHALL NOT expose project data

