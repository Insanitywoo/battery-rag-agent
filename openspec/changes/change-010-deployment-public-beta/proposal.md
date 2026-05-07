## Why

Battery-RAG Agent already has the core application flows needed for a small public beta: authentication, owner-scoped projects, document workflows, RAG chat, Agent and Skills, paper writing, external references, and experiment analysis. What the repository still lacks is a production-ready deployment layer that lets the team run the system safely on a public cloud server for limited external users.

Today the project is still optimized mainly for local development. There is no production-oriented compose topology, no explicit Nginx reverse-proxy setup, no public-beta deployment guide, no production env example, and no formalized handling for persistent user-file directories, secure production cookies, or production-only CORS boundaries. Without those pieces, the product is difficult to deploy safely even for a small invite-only test.

This change adds a bounded public-beta deployment capability. It does not expand end-user product workflows. Instead, it formalizes the Docker, Nginx, persistence, env var, deployment-script, and operational documentation needed to run Battery-RAG Agent in production-like conditions for a small public beta.

## What Changes

- Add or refine a backend production Dockerfile.
- Add or refine a frontend production Dockerfile.
- Add `docker-compose.prod.yml` for public-beta deployment.
- Add production persistence configuration for PostgreSQL, Redis, Qdrant, and user-file storage.
- Add Nginx reverse-proxy configuration for frontend traffic and backend API routing.
- Add production environment configuration guidance for:
  - CORS
  - HttpOnly cookies
  - `COOKIE_SECURE`
  - `COOKIE_SAMESITE`
  - `COOKIE_DOMAIN`
  - backend-only provider keys
- Add `.env.production.example`.
- Add deployment scripts such as `scripts/deploy-prod.sh` or `scripts/deploy-prod.ps1`.
- Add deployment and operations documentation under `docs/deployment-public-beta.md`.
- Update `README.md` to explain local-vs-production differences.
- Add a public-beta safety checklist covering secrets, HTTPS guidance, persistent volumes, logs, and backup expectations.

## Capabilities

### New Capabilities

- `public-beta-deployment`: Defines the bounded deployment, persistence, proxy, configuration, and operational documentation needed to run Battery-RAG Agent as a small public beta.

### Modified Capabilities

- `backend-shell`: Extends accepted backend shell scope to include production containerization, health-check readiness guidance, logging expectations, and environment-backed runtime configuration for public-beta deployment.
- `frontend-shell`: Extends accepted frontend shell scope to include production containerization and documented production build and runtime expectations.
- `local-dev-infra`: Extends repository infrastructure expectations to include a production compose topology, persistent storage guidance, env examples, deployment scripts, and deployment documentation.
- `user-authentication`: Extends cookie-auth and secret-handling expectations to include production cookie flags, domain configuration, and secure deployment guidance for public beta.

## Impact

- Affected code and config:
  - backend Docker build and runtime files
  - frontend Docker build and runtime files
  - production compose topology
  - Nginx reverse-proxy configuration
  - production env examples
  - deployment scripts
  - deployment documentation
  - README and operational notes
- Affected systems:
  - production networking between frontend, backend, Nginx, PostgreSQL, Redis, and Qdrant
  - persistent storage for database state and user-uploaded/generated files
  - secure cookie behavior across domain and HTTPS boundaries
  - operational startup, shutdown, backup, and update flows
- Explicitly not affected in this change:
  - payments
  - admin backoffice
  - email verification
  - team collaboration
  - Kubernetes
  - CI/CD pipelines
  - multi-node scaling
