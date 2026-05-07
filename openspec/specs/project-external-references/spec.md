# project-external-references Specification

## Purpose
Define a bounded project-scoped external scholarly metadata workflow so authenticated owners can search public paper metadata, curate saved references, and export draft BibTeX without mixing external references into private uploaded-document evidence.

## Requirements

### Requirement: The system SHALL provide project-scoped external scholarly metadata search
The system SHALL provide bounded external scholarly metadata search for authenticated owners inside projects they own, and the search SHALL support user-entered title, keyword, or DOI inputs without requiring private project document content to be sent externally.

#### Scenario: Authenticated owner searches external literature
- **WHEN** an authenticated owner submits an external scholarly search inside a project they own
- **THEN** the system SHALL return structured external metadata candidates within that owner and project scope

### Requirement: External search tools SHALL implement a unified structured interface
Every external scholarly tool introduced in this capability SHALL implement a shared contract for structured inputs, structured outputs, and safe failure handling.

#### Scenario: Tool output uses shared structure
- **WHEN** any external scholarly tool returns a result
- **THEN** that result SHALL include normalized source, title, authors, year, venue, DOI, URL, abstract, and warning data when available

### Requirement: Curated external references SHALL be persisted as owner-scoped project records
The system SHALL persist each saved external reference as an `external_references` record bound to `user_id` and `project_id`.

#### Scenario: External reference is stored
- **WHEN** an authenticated owner saves a selected scholarly metadata result
- **THEN** the system SHALL store the source, title, authors, year, venue, DOI, URL, abstract, BibTeX draft, and timestamps for that owner and project

### Requirement: External search and save flows SHALL deduplicate obvious duplicates
The system SHALL perform at least basic deduplication across search and save flows using DOI first and normalized title second.

#### Scenario: Duplicate candidate references are collapsed
- **WHEN** multiple tool results describe the same paper by DOI or normalized title
- **THEN** the system SHALL avoid presenting or saving obvious duplicates as separate preferred records

### Requirement: External references SHALL be listable, deletable, and exportable only by the owner
The system SHALL allow the authenticated owner to list, delete, and export only their own saved external references inside the current project.

#### Scenario: Owner lists project external references
- **WHEN** an authenticated owner requests saved external references for a project they own
- **THEN** the system SHALL return only that owner's saved external references for that project

#### Scenario: Cross-user external-reference access is blocked
- **WHEN** a user attempts to view, delete, or export another user's project external references
- **THEN** the system SHALL reject the request and SHALL NOT expose the other user's saved reference metadata

### Requirement: BibTeX export SHALL remain draft-only and owner-scoped
The system SHALL support project-scoped BibTeX draft export for saved external references, and the exported content SHALL be limited to the current owner's current project references while warning that manual confirmation is required.

#### Scenario: Owner exports project BibTeX draft
- **WHEN** an authenticated owner exports BibTeX for saved external references in a project they own
- **THEN** the returned BibTeX SHALL contain only that owner's current project references and SHALL be positioned as draft output requiring manual verification

### Requirement: External scholarly tool failures SHALL degrade safely
The system SHALL handle external provider timeouts, missing fields, and provider failures without crashing the application.

#### Scenario: Provider timeout does not crash the app
- **WHEN** an external scholarly provider request times out or fails
- **THEN** the system SHALL return a safe bounded error response and SHALL keep the rest of the application available
