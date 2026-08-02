from __future__ import annotations

import sys

from app.core.config import get_settings


def main() -> int:
    settings = get_settings()
    errors: list[str] = []
    if settings.DEBUG:
        errors.append("DEBUG must be false in production")
    if settings.SECRET_KEY.startswith("change-me"):
        errors.append("SECRET_KEY must be set to a generated value")
    if not settings.ENCRYPTION_KEY:
        errors.append("ENCRYPTION_KEY must be configured")
    if not settings.is_postgres:
        errors.append("DATABASE_URL must use PostgreSQL in production")
    if "*" in settings.CORS_ORIGINS:
        errors.append("CORS_ORIGINS must not contain '*'")
    if not settings.ADMIN_USER_IDS:
        errors.append("ADMIN_USER_IDS must contain at least one administrator")
    if errors:
        for error in errors:
            print(f"configuration error: {error}", file=sys.stderr)
        return 1
    print("production configuration validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
