# user-authentication Specification

## Purpose
TBD - created by archiving change change-002-auth-and-user-workspace. Update Purpose after archive.
## Requirements
### Requirement: System SHALL allow user registration with hashed password storage
The system SHALL provide a user registration capability that accepts a new user's identity fields and password, validates uniqueness of the account identifier, and stores the password only in hashed form.

#### Scenario: Successful registration
- **WHEN** a client submits valid registration data for a new email address
- **THEN** the system SHALL create a user record and store a password hash rather than the plaintext password

#### Scenario: Duplicate account is rejected
- **WHEN** a client submits registration data for an email address that already exists
- **THEN** the system SHALL reject the request and SHALL NOT create a second user account

### Requirement: System SHALL allow user login and issue JWT access tokens
The system SHALL provide a login capability that validates user credentials against the stored password hash, issues a JWT access token for successful authentication, and sends that token to the client using an HttpOnly Cookie.

#### Scenario: Successful login
- **WHEN** a client submits valid login credentials
- **THEN** the system SHALL issue a valid JWT access token representing the authenticated user and SHALL set it using an HttpOnly Cookie

#### Scenario: Invalid credentials are rejected
- **WHEN** a client submits an incorrect email or password
- **THEN** the system SHALL reject the login request and SHALL NOT issue a token

### Requirement: JWT signing configuration SHALL come from environment variables
The system SHALL load JWT signing configuration, including the secret used to sign access tokens, from backend environment variables and MUST NOT hardcode the secret in application code or frontend code.

#### Scenario: Backend boots with configured JWT secret
- **WHEN** the backend starts in a configured environment
- **THEN** the JWT signing secret SHALL be resolved from environment-backed configuration

### Requirement: Auth cookie behavior SHALL be environment-configurable and secure by default
The system SHALL configure the auth Cookie using environment-backed settings, with `COOKIE_SAMESITE` defaulting to `lax`, `COOKIE_SECURE=false` in development, and `COOKIE_SECURE=true` in production.

#### Scenario: Development cookie configuration is non-secure for local HTTP
- **WHEN** the backend runs in development
- **THEN** the auth Cookie SHALL allow `COOKIE_SECURE=false` for local HTTP development

#### Scenario: Production cookie configuration is secure
- **WHEN** the backend runs in production
- **THEN** the auth Cookie SHALL use `COOKIE_SECURE=true`

### Requirement: Protected interfaces SHALL require valid authenticated user context
All protected backend interfaces introduced in this change SHALL validate the presented token from the auth Cookie, resolve the current user from it, and reject requests that lack a valid authenticated user context.

#### Scenario: Protected route accepts valid token
- **WHEN** a client calls a protected endpoint with a valid auth Cookie for an existing user
- **THEN** the system SHALL resolve the current user and allow the request to continue

#### Scenario: Protected route rejects missing or invalid token
- **WHEN** a client calls a protected endpoint without an auth Cookie or with an invalid token in that Cookie
- **THEN** the system SHALL reject the request

### Requirement: System SHALL provide logout by clearing the auth Cookie
The system SHALL provide a logout capability that clears the auth Cookie used for access token transport.

#### Scenario: Logout clears auth Cookie
- **WHEN** an authenticated client requests logout
- **THEN** the system SHALL clear the auth Cookie so subsequent protected requests are no longer authenticated

### Requirement: System SHALL provide a current-user profile endpoint
The system SHALL provide an endpoint that returns the authenticated user's basic account information for a valid current user context.

#### Scenario: Current user information is returned
- **WHEN** an authenticated client requests the current user profile
- **THEN** the system SHALL return the current user's identity information without exposing password hashes or secrets

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
