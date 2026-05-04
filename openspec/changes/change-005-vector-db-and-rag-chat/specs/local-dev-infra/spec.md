## ADDED Requirements

### Requirement: Local development SHALL document backend-only vector DB and model gateway configuration
The repository SHALL document the environment-backed configuration required for local vector indexing and backend-only model access, including Qdrant connectivity and model-provider settings, while keeping secrets out of frontend-exposed configuration.

#### Scenario: Vector and model settings are discoverable for local setup
- **WHEN** a developer prepares a local environment for project vector build and RAG chat work
- **THEN** the repository SHALL provide discoverable Qdrant and backend-only model gateway configuration in `.env.example` and `README.md`
