## Context

Battery-RAG Agent now has enough core product functionality to support a limited public beta, but the repository is still mostly shaped around local development. A public-beta release requires more than just working business features. It also requires:

- reproducible production Docker images
- a production compose topology
- reverse proxying for browser traffic and API routing
- durable storage for database and user-generated files
- secure production cookie settings
- production-only CORS boundaries
- safe secret handling
- clear deployment and maintenance documentation

This change should not introduce new end-user business workflows. Its purpose is to provide a safe, understandable, and repeatable way to deploy the existing product for small-scale public testing.

Primary constraints:

- public-beta deployment must remain single-node and Docker Compose based
- production secrets must stay outside Git
- frontend must not expose model keys or backend secrets
- backend model keys must remain environment-only
- production cookie defaults must assume HTTPS
- CORS must be restricted to explicit frontend origins
- user-uploaded and generated files must be stored persistently and must not be executable
- Nginx must not enable directory browsing for storage or output folders
- the deployment docs must remain realistic for a single cloud VM or similar host

## Goals / Non-Goals

**Goals:**

- define the production Docker and compose shape for backend, frontend, PostgreSQL, Redis, Qdrant, and Nginx
- define production persistence for data volumes and user file volumes
- define production env vars and examples
- define secure cookie, CORS, and secret-handling guidance for public beta
- define deployment, log inspection, backup, stop, and update procedures
- define a lightweight deployment script for repeatable startup
- document public-beta security checks and operational caveats

**Non-Goals:**

- Kubernetes manifests
- CI/CD automation
- blue-green or canary deployment
- object storage migration
- distributed scaling
- observability stacks such as Prometheus or Grafana
- billing or quota systems
- admin-only operations consoles

## Decisions

### Decision: Use Docker Compose for public-beta orchestration

This change should stay with a single-host `docker-compose.prod.yml` approach because:

- the user explicitly does not want Kubernetes in this phase
- the current repository already uses Docker Compose locally
- the deployment target is a small public beta rather than a scale-out cluster

The production compose file should include:

- `nginx`
- `frontend`
- `backend`
- `postgres`
- `redis`
- `qdrant`

### Decision: Treat Nginx as the public entry point

Nginx should terminate public HTTP traffic for the application stack and route requests as follows:

- `/` and frontend page traffic -> frontend app
- `/api/` -> backend app
- optionally proxy health endpoints if documented

Nginx should not expose raw storage directories or directory listings.

### Decision: Separate production env examples from local env examples

The repository should keep:

- `.env.example` for local development
- `.env.production.example` for public-beta deployment

This separation reduces confusion between local-only defaults and production-safe expectations.

### Decision: Production cookies must be explicitly configured

Production auth behavior should document and support:

- `COOKIE_SECURE=true`
- `COOKIE_SAMESITE=lax` by default unless cross-site constraints require adjustment
- `COOKIE_DOMAIN` for the deployed hostname
- HttpOnly cookies as the only token transport mechanism

The design should also call out that HTTPS is strongly recommended, and effectively required for secure cookies in public deployment.

### Decision: Persist both service state and user-generated file state

The deployment must persist:

- PostgreSQL data
- Redis data if retained in current architecture
- Qdrant storage
- user-uploaded files under storage roots
- generated experiment outputs and charts if they are stored separately

The design may model storage as either:

- one shared persistent root with well-defined subdirectories
- or several explicit named volumes for uploads, storage, outputs, and vector/database state

The important requirement is that uploaded documents and generated outputs survive container restarts.

### Decision: Production security guidance should stay bounded and concrete

This change should add a public-beta security checklist focused on practical deployment issues:

- generate a strong random `JWT_SECRET`
- keep `.env` files out of Git
- keep provider keys in backend env only
- restrict CORS to the deployed frontend origin
- enforce HttpOnly cookies
- enable `COOKIE_SECURE=true`
- keep storage and output folders off public directory indexes
- ensure uploaded files are treated as data and not as executables
- recommend HTTPS before exposing the system publicly

### Decision: Add a simple deployment script rather than CI/CD

The repository should provide a minimal deployment helper such as:

- `scripts/deploy-prod.sh`
- or `scripts/deploy-prod.ps1`

The script should help with repeatable compose startup for public beta, but should not try to become a full release pipeline.

### Decision: Health, logs, backup, and update flows must be documented

The deployment doc should cover:

1. server preparation
2. env file setup
3. compose startup
4. database initialization expectations
5. frontend access
6. backend health checks
7. HTTPS/domain guidance
8. common troubleshooting
9. log inspection
10. PostgreSQL and uploaded-file backup
11. service stop flow
12. version update flow

## Deployment Shape

Recommended production topology:

- `nginx`
  - public port binding
  - proxies frontend and backend
- `frontend`
  - production Next.js runtime or equivalent production server
- `backend`
  - production FastAPI runtime
- `postgres`
  - named volume for database persistence
- `redis`
  - named volume if persistence is retained in the chosen prod config
- `qdrant`
  - named volume for vector persistence

Recommended persistent application paths:

- documents and uploads
- generated outputs and charts
- any storage root used by current backend file workflows

## Config Shape

Suggested production env additions or clarifications:

- `APP_ENV=production`
- `BACKEND_CORS_ORIGINS=https://your-frontend-domain`
- `COOKIE_SECURE=true`
- `COOKIE_SAMESITE=lax`
- `COOKIE_DOMAIN=your-domain`
- `JWT_SECRET=<strong-random-value>`
- backend-only `LLM_API_KEY`
- backend-only provider settings

The docs should also remind operators:

- never commit populated `.env` files
- never expose provider keys via `NEXT_PUBLIC_*`
- rotate secrets if they are ever leaked

## Risks / Trade-offs

- [Single-node public beta is simpler but not highly available] -> accepted because the scope is explicitly limited to a small beta.
- [Nginx plus container networking adds deployment complexity] -> mitigated through example config and deployment docs.
- [Operators may misuse local env defaults in production] -> mitigated through `.env.production.example` and README clarification.
- [User files can be lost if volumes are misconfigured] -> mitigated through explicit volume and backup guidance.
- [Cookie or CORS misconfiguration can break login] -> mitigated through documented production defaults and health-check guidance.

## Migration Plan

Suggested implementation order:

1. add or refine backend and frontend production Dockerfiles
2. add `docker-compose.prod.yml`
3. add Nginx reverse-proxy configuration
4. define persistent volumes for databases and user files
5. add `.env.production.example`
6. add deployment script
7. add deployment docs and public-beta checklist
8. update README with local-vs-production distinctions

Rollback path:

- remove production compose and Nginx additions
- remove deployment scripts and production env example
- restore repository documentation to local-dev-only guidance
- keep existing application business features unchanged

## Open Questions

- Should the default deployment script be shell-first, PowerShell-first, or provide both?
- Should Redis persistence be explicitly enabled in the prod compose file, or only documented as optional depending on runtime usage?
- Should Nginx expose backend health checks publicly, or only internally/document them through compose and container inspection?
