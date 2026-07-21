# Troubleshooting Guide

## Common Issues

### `SECRET_KEY must be changed from the default value`

Set a strong SECRET_KEY in your `.env` file:
```
SECRET_KEY=$(openssl rand -hex 32)
```

### `ENCRYPTION_KEY is required`

Generate a Fernet key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Database not initialized / `RuntimeError: Database not initialized`

Ensure the lifespan handler runs. This happens automatically with `uvicorn` but may fail in tests if `init_db()` is not called. Run:
```bash
alembic upgrade head
```

### Alembic migration fails

Ensure `DATABASE_URL` is set in your environment or `.env` file. For SQLite:
```
DATABASE_URL=sqlite+aiosqlite:///./ultron.db
```

### Redis connection refused

Redis is optional. If `REDIS_URL` is not set, the system falls back to in-memory rate limiting. Set `REDIS_URL` in `.env` to enable Redis:
```
REDIS_URL=redis://localhost:6379/0
```

### `ModuleNotFoundError: No module named 'asyncpg'`

Install the PostgreSQL driver:
```bash
pip install asyncpg
```
Or use SQLite for development.

### Rate limiting too aggressive

Adjust in `.env`:
```
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_AUTH_PER_MINUTE=30
```

### Port already in use

```bash
# Find process on port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

## Getting Help

Open an issue on the repository with:
1. The full error message and traceback
2. Your configuration (redact secrets)
3. Steps to reproduce
4. Environment: Python version, OS, database type
