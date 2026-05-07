## 1. Production Container Baseline

- [x] 1.1 Add or refine a production-ready backend Dockerfile
- [x] 1.2 Add or refine a production-ready frontend Dockerfile
- [x] 1.3 Ensure container runtime expectations are documented and bounded to public-beta scope

## 2. Production Compose and Persistence

- [x] 2.1 Add `docker-compose.prod.yml` for public-beta deployment
- [x] 2.2 Configure PostgreSQL, Redis, and Qdrant production persistence volumes
- [x] 2.3 Configure persistent storage for user uploads, storage roots, and generated outputs
- [x] 2.4 Ensure production service networking and restart expectations are documented

## 3. Reverse Proxy and Runtime Security

- [x] 3.1 Add Nginx reverse-proxy configuration for frontend traffic and backend API routing
- [x] 3.2 Define production CORS expectations for explicit frontend origins only
- [x] 3.3 Define production HttpOnly cookie expectations including `COOKIE_SECURE`, `COOKIE_SAMESITE`, and `COOKIE_DOMAIN`
- [x] 3.4 Ensure storage and output paths are not exposed for arbitrary directory browsing or execution

## 4. Production Environment and Secret Handling

- [x] 4.1 Add `.env.production.example`
- [x] 4.2 Verify `.env`, provider keys, JWT secrets, and user file directories remain excluded from Git
- [x] 4.3 Document strong-random `JWT_SECRET` and backend-only provider-key requirements

## 5. Deployment Automation and Docs

- [x] 5.1 Add a bounded public-beta deployment script such as `scripts/deploy-prod.sh` or `scripts/deploy-prod.ps1`
- [x] 5.2 Add `docs/deployment-public-beta.md`
- [x] 5.3 Document server preparation, env setup, compose startup, database initialization expectations, frontend access, backend health checks, HTTPS suggestions, common issues, logs, backups, stop flow, and update flow
- [x] 5.4 Update `README.md` to explain local-development versus production-deployment differences

## 6. Logging and Public Beta Safety

- [x] 6.1 Add baseline production logging guidance for frontend, backend, Nginx, and Docker services
- [x] 6.2 Add a public-beta deployment safety checklist covering secrets, HTTPS, CORS, cookies, persistence, backups, and file handling
- [x] 6.3 Ensure the documented deployment remains bounded to single-node public-beta scope and excludes Kubernetes, CI/CD, multi-node scaling, and billing systems

## 7. Validation

- [x] 7.1 Validate OpenSpec artifacts and scope alignment for `change-010-deployment-public-beta`
- [x] 7.2 Ensure tasks remain deployment-only and do not introduce new business functionality
