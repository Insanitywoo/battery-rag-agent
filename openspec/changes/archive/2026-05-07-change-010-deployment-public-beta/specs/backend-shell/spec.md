## MODIFIED Requirements

### Requirement: Backend SHALL expose deployment-ready runtime expectations for public beta
The backend shell SHALL support production-oriented containerization, environment-backed runtime configuration, and documented health-check readiness for single-node public-beta deployment, while remaining within the existing backend framework and product scope.

#### Scenario: Backend production runtime is documented and containerized
- **WHEN** an operator prepares the backend for public-beta deployment
- **THEN** the repository SHALL provide a backend production container path, documented runtime configuration, and a clear way to verify backend health

### Requirement: Backend runtime secrets SHALL remain environment-only in public deployment
Backend secrets used in public deployment, including `JWT_SECRET` and provider API keys, SHALL remain environment-backed and SHALL NOT be hardcoded into tracked repository files or frontend-exposed configuration.

#### Scenario: Backend production secrets stay out of tracked config
- **WHEN** backend deployment assets are reviewed
- **THEN** tracked files SHALL document required secret keys without embedding real secret values
