## ADDED Requirements

### Requirement: The system SHALL provide a bounded public-beta deployment topology
The repository SHALL provide a bounded production-like deployment topology for Battery-RAG Agent that supports a small public beta on a single host using Docker Compose, persistent storage, and a reverse proxy, without introducing unrelated product features.

#### Scenario: Public-beta deployment topology is present
- **WHEN** an operator reviews the repository for public-beta deployment support
- **THEN** the repository SHALL include production deployment assets such as production compose configuration, reverse-proxy configuration, env examples, and deployment documentation

### Requirement: Public-beta deployment SHALL persist service state and user-generated file state
The public-beta deployment topology SHALL persist database, vector-store, cache-state expectations where configured, and user-generated file state across container restarts.

#### Scenario: Restart does not discard core deployment state
- **WHEN** the public-beta stack is restarted
- **THEN** PostgreSQL data, Qdrant data, and documented user-uploaded or generated file directories SHALL remain on persistent volumes

### Requirement: Public-beta deployment SHALL provide bounded operational documentation
The repository SHALL provide public-beta deployment documentation that covers server preparation, env setup, compose startup, health checks, logging, backups, stop flow, and update flow.

#### Scenario: Operator can follow deployment documentation
- **WHEN** a new operator prepares a single server for public beta
- **THEN** the repository SHALL provide enough documentation to deploy, inspect, back up, update, and stop the system without relying on tribal knowledge

### Requirement: Public-beta deployment SHALL include a bounded deployment helper script
The repository SHALL provide at least one bounded deployment helper script for public-beta startup or update flows, and that script SHALL remain limited to Docker Compose oriented deployment tasks.

#### Scenario: Deployment helper stays within bounded scope
- **WHEN** the deployment helper is reviewed
- **THEN** it SHALL support repeatable public-beta deployment steps and SHALL NOT attempt to implement full CI/CD or multi-cluster orchestration

### Requirement: Public-beta deployment SHALL provide a practical security checklist
The repository SHALL provide a public-beta security checklist that reminds operators about HTTPS, secret handling, cookie security, CORS restriction, persistence, and safe file handling.

#### Scenario: Security checklist warns about production misconfiguration
- **WHEN** an operator prepares a public-facing beta deployment
- **THEN** the repository SHALL explicitly warn about strong random secrets, backend-only API keys, HTTPS, HttpOnly cookies, and safe handling of storage directories
