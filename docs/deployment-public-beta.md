# Deployment: Public Beta

This guide describes a bounded single-node public-beta deployment for Battery-RAG Agent using Docker Compose and Nginx. It is intentionally small in scope and is designed for early external testing rather than high-availability production.

## 1. Server Preparation

- Prepare a Linux server or VM with enough disk for PostgreSQL, Qdrant, and user-uploaded files.
- Install Docker Engine and Docker Compose plugin.
- Open only the ports you intend to expose publicly, typically `80` and later `443` if you add HTTPS.
- Clone this repository onto the server.
- Create a dedicated operator account if possible instead of deploying as a shared system user.

## 2. Environment Variable Configuration

- Copy [`.env.production.example`](/D:/projects/battery_rag_agent/.env.production.example) to `.env.production`.
- Set a strong random `JWT_SECRET`.
- Set a strong `POSTGRES_PASSWORD`.
- Set `BACKEND_CORS_ORIGINS` to your deployed frontend origin only.
- Set `COOKIE_DOMAIN` to your real deployment domain.
- Keep `COOKIE_SECURE=true` for public deployment.
- Keep `LLM_API_KEY` and any model-provider secrets in backend env only.
- Do not place secrets in `NEXT_PUBLIC_*` variables.

## 3. Docker Compose Startup

Run from the repository root:

```bash
cp .env.production.example .env.production
# edit .env.production first

./scripts/deploy-prod.sh
```

If you prefer manual commands:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml pull
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

## 4. Database Initialization

- The backend currently initializes database tables on startup through the application lifecycle.
- There is no separate migration tool in this phase.
- For a fresh public beta, starting the backend after PostgreSQL is enough to create the current schema.
- For future schema-breaking upgrades, plan a maintenance window because this repository is not yet using a formal migration workflow.

## 5. Frontend Access

- Nginx is the public entry point.
- By default the public stack exposes port `80`.
- Frontend traffic is proxied by Nginx to the frontend container.
- API traffic under `/api/` is proxied by Nginx to the backend container.
- If `NEXT_PUBLIC_API_BASE_URL` is left blank in `.env.production`, the frontend uses same-origin API requests behind Nginx.

## 6. Backend Health Check

- Backend app health endpoint: `/api/health`
- Example from the server:

```bash
curl http://127.0.0.1/api/health
```

- Example through a published domain:

```bash
curl http://your-domain.example/api/health
```

- The production compose file also defines a backend container health check.

## 7. HTTPS / Domain Configuration Suggestions

- Use a real domain before inviting external testers.
- Add HTTPS before exposing login flows widely.
- Keep `COOKIE_SECURE=true` in public deployment.
- You can terminate TLS in front of this Nginx container or extend Nginx with certificate management later.
- This change does not implement automated certificate provisioning.

## 8. Common Issues

- Login works locally but not on the public host:
  - Check `BACKEND_CORS_ORIGINS`, `COOKIE_DOMAIN`, `COOKIE_SECURE`, and whether HTTPS is configured.
- Frontend loads but API requests fail:
  - Check the Nginx `/api/` proxy path and backend container health.
- Uploaded files disappear after restart:
  - Check that the production volume for `/app/storage` is mounted and healthy.
- Qdrant search fails after restart:
  - Check the `qdrant_data` volume.
- The frontend calls the wrong API origin:
  - Check `NEXT_PUBLIC_API_BASE_URL` at build time.

## 9. How to View Logs

Show all services:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f
```

Show one service:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f frontend
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f nginx
```

The compose file uses Docker `json-file` logging with simple rotation settings (`max-size` and `max-file`) as a bounded public-beta default.

## 10. How to Back Up PostgreSQL and User Uploads

PostgreSQL logical backup example:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec postgres \
  sh -lc 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup-$(date +%F).sql
```

User-file backup considerations:

- Back up the Docker volume mounted at `/app/storage`.
- That storage root contains uploaded documents and generated experiment outputs in the current architecture.
- Back up the storage volume on the same schedule as PostgreSQL if testers are actively using uploads.

Qdrant backup considerations:

- Back up the `qdrant_data` volume if you need to preserve vector state between rebuilds or disasters.

## 11. How to Stop Services

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

If you need to stop containers without removing the network:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml stop
```

## 12. How to Update Versions

Typical public-beta update flow:

1. Pull the latest repository changes.
2. Review changes to `.env.production.example` and update your real `.env.production` if needed.
3. Back up PostgreSQL and the storage volume.
4. Rebuild and restart:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

5. Re-check `/api/health`.
6. Verify login, project listing, and one upload flow manually.

## Public Beta Safety Checklist

- Use a strong random `JWT_SECRET`.
- Keep `.env.production` out of Git.
- Keep model provider keys in backend env only.
- Keep `COOKIE_SECURE=true`.
- Restrict `BACKEND_CORS_ORIGINS` to the deployed frontend origin only.
- Use HTTPS before inviting external users broadly.
- Do not expose storage or output directories through static Nginx aliases.
- Treat uploaded files as untrusted data only.
- Back up PostgreSQL, Qdrant, and `/app/storage` before version updates.
- Stay within single-node public-beta expectations for this deployment shape.
