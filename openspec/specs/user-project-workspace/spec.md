# user-project-workspace Specification

## Purpose
Define the authenticated owner-scoped project workspace so each user can manage projects, inspect project state, and enter bounded downstream research workflows only within their own scope.

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
The project detail capability introduced in this change SHALL expand from project metadata plus knowledge-base build state and chat plus Agent entry structure into owner-scoped project metadata plus a Paper Writing entry structure, and MUST NOT introduce external retrieval, external tools, or broader autonomous research workflows.

#### Scenario: Project Paper Writing route remains project-scoped and owner-scoped
- **WHEN** an authenticated owner enters the Paper Writing page from project detail
- **THEN** the resulting writing experience SHALL remain scoped to that owner's current project, current writing artifacts, and current project sources only

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
