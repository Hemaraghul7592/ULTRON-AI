#!/bin/sh
set -eu

python scripts/validate_env.py
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --log-level "${LOG_LEVEL:-info}"
