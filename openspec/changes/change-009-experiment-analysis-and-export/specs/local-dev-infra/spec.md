## MODIFIED Requirements

### Requirement: Local development SHALL document experiment-analysis configuration
The repository SHALL document the environment-backed configuration needed to run bounded CSV experiment-analysis workflows locally, including dataset and output storage settings, chart-output configuration, backend-only analysis settings, and export limitations, while keeping secrets out of frontend-exposed configuration.

#### Scenario: Experiment-analysis configuration is discoverable for local setup
- **WHEN** a developer prepares a local environment for project experiment-analysis workflows
- **THEN** the repository SHALL provide discoverable experiment-analysis configuration, storage expectations, and export limitations in `.env.example` and `README.md`
