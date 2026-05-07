## MODIFIED Requirements

### Requirement: Local development SHALL document external scholarly tool configuration
The repository SHALL document the environment-backed configuration needed to run bounded external scholarly metadata tools locally, including backend-only provider settings, timeout or rate-limit expectations, and BibTeX draft limitations, while keeping any provider secrets out of frontend-exposed configuration.

#### Scenario: External-tool configuration is discoverable for local setup
- **WHEN** a developer prepares a local environment for project external-reference workflows
- **THEN** the repository SHALL provide discoverable external-tool and backend-only provider configuration plus BibTeX draft limitations in `.env.example` and `README.md`
