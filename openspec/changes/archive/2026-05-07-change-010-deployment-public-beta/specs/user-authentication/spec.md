## MODIFIED Requirements

### Requirement: Cookie-based authentication SHALL define production deployment expectations
The authenticated cookie model SHALL document production deployment expectations for `COOKIE_SECURE`, `COOKIE_SAMESITE`, and `COOKIE_DOMAIN`, and public deployment guidance SHALL assume HttpOnly cookies remain the only browser auth transport.

#### Scenario: Production cookie settings are documented
- **WHEN** an operator prepares auth settings for public-beta deployment
- **THEN** the repository SHALL document production-safe cookie expectations including secure transport and domain configuration

### Requirement: Production auth deployment SHALL assume HTTPS guidance
Public-beta deployment guidance for cookie-based authentication SHALL warn operators to use HTTPS before exposing the system to external users.

#### Scenario: Deployment docs warn about HTTPS for auth
- **WHEN** an operator reviews authentication deployment guidance
- **THEN** the documentation SHALL explicitly recommend HTTPS for public-facing auth flows
