# local-dev-infra

## Purpose

Define the shared local development infrastructure needed to run Battery-RAG Agent shells consistently during development.

## Requirements

### Requirement: Local development SHALL provide shared dependency containers
The repository SHALL include a Docker Compose configuration for the local development environment that provisions PostgreSQL, Redis, and Qdrant as shared dependency services for future application work.

#### Scenario: Compose file defines required dependencies
- **WHEN** a developer reviews the local development infrastructure configuration
- **THEN** the configuration SHALL define service entries for PostgreSQL, Redis, and Qdrant

### Requirement: Repository SHALL provide environment variable examples
The repository SHALL include a root `.env.example` that documents the baseline configuration values needed to run the frontend shell, backend shell, and local dependency services.

#### Scenario: Environment configuration can be discovered
- **WHEN** a developer prepares a local environment from a fresh clone
- **THEN** the repository SHALL provide an `.env.example` file that lists the expected configuration keys for bootstrap development

### Requirement: Local development infra SHALL support shell-only application scope
The local infrastructure SHALL support the engineering shell introduced by this change and MUST NOT require login, RAG indexing, Agent execution, or external provider credentials to validate the bootstrap environment.

#### Scenario: Bootstrap environment remains minimal
- **WHEN** a developer validates the scaffold created by this change
- **THEN** the required local dependencies SHALL be limited to infrastructure needed for future development rather than current business feature execution

### Requirement: Local development SHALL document storage configuration and exclude storage artifacts from Git
The repository SHALL document the storage configuration needed for local document uploads, including environment-backed storage settings, and it SHALL exclude the local storage directory from version control.

#### Scenario: Storage configuration is documented for local development
- **WHEN** a developer prepares a local environment for document upload work
- **THEN** the repository SHALL provide discoverable storage-related configuration in `.env.example` and `README.md`

#### Scenario: Storage artifacts are not committed
- **WHEN** document uploads are created in local development
- **THEN** the configured storage directory SHALL be excluded from Git-tracked repository contents

### Requirement: Local development SHALL document backend-only vector DB and model gateway configuration
The repository SHALL document the environment-backed configuration required for local vector indexing and backend-only model access, including Qdrant connectivity and model-provider settings, while keeping secrets out of frontend-exposed configuration.

#### Scenario: Vector and model settings are discoverable for local setup
- **WHEN** a developer prepares a local environment for project vector build and RAG chat work
- **THEN** the repository SHALL provide discoverable Qdrant and backend-only model gateway configuration in `.env.example` and `README.md`

### Requirement: Local development SHALL document Agent and Skills framework configuration
The repository SHALL document the environment-backed configuration needed to run the bounded Agent, Skills, and writing-assistant framework locally, including backend-only model settings, Agent-specific knobs, and writing-assistant usage limits, while keeping secrets out of frontend-exposed configuration.

#### Scenario: Writing-assistant configuration is discoverable for local setup
- **WHEN** a developer prepares a local environment for project writing assistance
- **THEN** the repository SHALL provide discoverable writing-assistant and backend-only provider configuration plus usage limitations in `.env.example` and `README.md`

### Requirement: Local development SHALL document external scholarly tool configuration
The repository SHALL document the environment-backed configuration needed to run bounded external scholarly metadata tools locally, including backend-only provider settings, timeout or rate-limit expectations, and BibTeX draft limitations, while keeping any provider secrets out of frontend-exposed configuration.

#### Scenario: External-tool configuration is discoverable for local setup
- **WHEN** a developer prepares a local environment for project external-reference workflows
- **THEN** the repository SHALL provide discoverable external-tool and backend-only provider configuration plus BibTeX draft limitations in `.env.example` and `README.md`

### Requirement: Local development SHALL document experiment-analysis configuration
The repository SHALL document the environment-backed configuration needed to run bounded CSV experiment-analysis workflows locally, including dataset and output storage settings, chart-output configuration, backend-only analysis settings, and export limitations, while keeping secrets out of frontend-exposed configuration.

#### Scenario: Experiment-analysis configuration is discoverable for local setup
- **WHEN** a developer prepares a local environment for project experiment-analysis workflows
- **THEN** the repository SHALL provide discoverable experiment-analysis configuration, storage expectations, and export limitations in `.env.example` and `README.md`

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
