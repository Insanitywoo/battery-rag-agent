## MODIFIED Requirements

### Requirement: Repository SHALL provide production deployment configuration in addition to local development configuration
The repository SHALL provide a bounded production deployment configuration alongside existing local development configuration, including a production compose file, deployment env example, reverse-proxy config, and deployment docs for a small public beta.

#### Scenario: Production deployment assets are discoverable
- **WHEN** an operator prepares the repository for public-beta deployment
- **THEN** the repository SHALL provide production deployment assets that are clearly distinct from local development assets

### Requirement: Repository SHALL document production persistence and backup expectations
The repository SHALL document the persistent volumes and backup expectations for PostgreSQL, Qdrant, Redis where configured, and user-generated file directories in public-beta deployment.

#### Scenario: Production persistence is documented
- **WHEN** an operator reviews public-beta storage expectations
- **THEN** the repository SHALL identify which service state and application file paths must be persisted and backed up

### Requirement: Repository SHALL provide a public-beta deployment guide
The repository SHALL include a deployment guide for single-node public-beta operation covering startup, health, logs, backups, stop flow, update flow, and HTTPS guidance.

#### Scenario: Public-beta deployment guide covers operations
- **WHEN** an operator follows the deployment guide
- **THEN** the guide SHALL include startup, logging, health-check, backup, shutdown, and update instructions
