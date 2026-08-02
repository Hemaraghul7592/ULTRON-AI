# Environment Contract

## Backend Production Variables

Required:

- `SECRET_KEY`
- `ENCRYPTION_KEY`
- `DATABASE_URL` using PostgreSQL
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `ADMIN_USER_IDS`
- `CORS_ORIGINS` without wildcard origins

Recommended:

- `LOG_LEVEL=INFO`
- `DEBUG=false`
- `WEB_CONCURRENCY=2`
- `PORT=8000`

Provider credentials are injected only through the deployment secret manager. They must not be committed or copied into Docker images.

## Android Build Variables

- `ULTRON_BASE_URL`: HTTPS API origin
- `ULTRON_KEYSTORE_FILE`: CI-only keystore path
- `ULTRON_KEYSTORE_PASSWORD`: CI secret
- `ULTRON_KEY_ALIAS`: CI secret/configuration
- `ULTRON_KEY_PASSWORD`: CI secret

See `android/keystore.properties.example` for the signing contract.

## macOS Build Variables

- `ULTRON_CODE_SIGN_IDENTITY`: Apple signing identity
- `ULTRON_DEVELOPMENT_TEAM`: Apple developer team identifier

These values belong in the signing environment or CI secret store, not source control.

## Local Development

Use separate development values and local-only endpoints. Never reuse production credentials locally. Backend `.env.example` is a template only and must not contain real secrets.
