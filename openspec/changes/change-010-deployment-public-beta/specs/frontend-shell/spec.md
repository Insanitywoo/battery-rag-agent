## MODIFIED Requirements

### Requirement: Frontend SHALL support a bounded production container path
The frontend shell SHALL support a production-oriented container build and runtime path suitable for single-node public-beta deployment, without expanding into unrelated product capabilities.

#### Scenario: Frontend production build path is documented
- **WHEN** an operator prepares the frontend for public-beta deployment
- **THEN** the repository SHALL provide a frontend production container path and documented build or runtime expectations

### Requirement: Frontend production deployment SHALL not expose backend secrets
The frontend production deployment path SHALL continue to avoid exposing backend JWT secrets, model provider keys, or other server-only secrets through client-visible environment variables or deployment docs.

#### Scenario: Frontend production env remains non-secret
- **WHEN** frontend deployment assets are reviewed
- **THEN** no server-only secret SHALL be documented as a client-side runtime value
