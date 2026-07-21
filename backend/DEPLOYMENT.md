# Deployment Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 16+ (production) or SQLite (development)
- Redis 7+ (optional, for rate limiting)
- Docker (optional, for containerized deployment)

## Environment Variables

Copy `.env.example` to `.env` and configure:

### Required

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key. Generate: `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | Fernet key for encrypting stored secrets. Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

### Database

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./ultron.db` | Supports SQLite and PostgreSQL (asyncpg) |

### AI Providers

At least one of `GROQ_API_KEY` or `GEMINI_API_KEY` must be set.

### Optional

See `.env.example` for all optional variables.

## SQLite (Development)

```bash
cp .env.example .env
# Edit SECRET_KEY and ENCRYPTION_KEY in .env
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## PostgreSQL (Production)

```bash
# Create the database
createdb ultron

# Configure .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ultron

# Run migrations
alembic upgrade head

# Start
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
# Build
docker build -t ultron-backend .

# Run with SQLite
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e ENCRYPTION_KEY=your-encryption-key \
  ultron-backend

# Run with PostgreSQL and Redis
docker-compose up -d
```

## Health Checks

| Endpoint | Purpose |
|---|---|
| `/livez` | Liveness probe (always returns 200) |
| `/readyz` | Readiness probe (checks database) |
| `/health` | Full health check (DB + Redis) |

## Backup

```bash
# Backup
./scripts/backup.sh

# Restore
./scripts/restore.sh backups/ultron_db_TIMESTAMP.db
```
