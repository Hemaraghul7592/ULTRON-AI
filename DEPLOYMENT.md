# ULTRON Deployment Guide

## Backend

1. Provision a private PostgreSQL instance and Redis instance.
2. Generate `SECRET_KEY` and `ENCRYPTION_KEY`.
3. Set `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, and `ADMIN_USER_IDS`.
4. Copy `.env.example` to a deployment secret store and fill all required values.
5. Build and start the image:

```sh
cd backend
docker compose config
docker compose up --build -d
```

6. Verify readiness:

```sh
curl --fail https://api.example.com/livez
curl --fail https://api.example.com/readyz
```

The backend container listens on port `8000`, runs as a non-root user, validates production configuration, and performs graceful Uvicorn shutdown.

## Reverse Proxy

Terminate TLS at the ingress or reverse proxy. Forward only application traffic to the backend service. PostgreSQL and Redis are internal Compose services and must not be published to the host.

## Secrets

Do not copy `.env` files into images, source archives, CI artifacts, or backups. Use the deployment platform’s secret manager and rotate credentials independently of application releases.

## Health Checks

- `/livez`: process liveness
- `/readyz`: database readiness
- `/health`: service health summary

## Rollback

Keep the previous image digest and database backup. Roll back the container image first, then apply only backward-compatible migrations. Verify `/readyz` before restoring traffic.

## Android and macOS

Android requires `ULTRON_BASE_URL` to point to the HTTPS backend endpoint. macOS release distribution requires an Apple-signed archive and notarization workflow outside SwiftPM.
