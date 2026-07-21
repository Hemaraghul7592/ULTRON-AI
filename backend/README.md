# ULTRON — Personal AI Assistant Backend

A production-ready, multi-tenant AI backend built with FastAPI.

## Quick Start

```bash
cp .env.example .env
# Edit .env with your editor
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design.

## Documentation

- [API Reference](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Architecture](ARCHITECTURE.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## Environment

Copy `.env.example` to `.env` and fill in your secrets. See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

### Google OAuth Setup

`GOOGLE_REFRESH_TOKEN` is **not** stored in `.env`. It is automatically obtained via the OAuth flow and stored encrypted in the database.

To connect your Google account:

1. Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in `.env`.
2. Start the backend and register a user.
3. Open in browser (while logged in):
   ```
   GET /api/v1/google/auth/login
   ```
4. Sign in to your Google account and click **Allow**.
5. ULTRON automatically receives the **Refresh Token**, encrypts it, and stores it in the database.
6. The Refresh Token is used to obtain new Access Tokens automatically when they expire.

**Never manually create or search for a Refresh Token.** The implementation handles it automatically.

## Development

```bash
pip install -e ".[dev]"
ruff check .
mypy app/ --ignore-missing-imports
pytest tests/ -v
```

## Testing

```bash
pytest tests/ -v
```

## License

MIT
