## MODIFIED Requirements

### Requirement: Local development SHALL document Agent and Skills framework configuration
The repository SHALL document the environment-backed configuration needed to run the bounded Agent, Skills, and writing-assistant framework locally, including backend-only model settings, Agent-specific knobs, and writing-assistant usage limits, while keeping secrets out of frontend-exposed configuration.

#### Scenario: Writing-assistant configuration is discoverable for local setup
- **WHEN** a developer prepares a local environment for project writing assistance
- **THEN** the repository SHALL provide discoverable writing-assistant and backend-only provider configuration plus usage limitations in `.env.example` and `README.md`
