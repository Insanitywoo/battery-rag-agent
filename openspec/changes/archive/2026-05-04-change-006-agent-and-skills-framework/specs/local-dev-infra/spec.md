## ADDED Requirements

### Requirement: Local development SHALL document Agent and Skills framework configuration
The repository SHALL document the environment-backed configuration needed to run the bounded Agent and Skills framework locally, including backend-only model settings and any Agent-specific knobs, while keeping secrets out of frontend-exposed configuration.

#### Scenario: Agent configuration is discoverable for local setup
- **WHEN** a developer prepares a local environment for project Agent execution
- **THEN** the repository SHALL provide discoverable Agent and backend-only provider configuration in `.env.example` and `README.md`
