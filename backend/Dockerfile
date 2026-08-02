# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.lock .
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.lock

# Stage 2: Production
FROM python:3.11-slim AS production

WORKDIR /app

RUN addgroup --system --gid 1001 ultron && \
    adduser --system --uid 1001 --gid 1001 ultron

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links /wheels /wheels/* && rm -rf /wheels

COPY alembic.ini alembic/ ./
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN chown -R ultron:ultron /app

USER ultron

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/livez || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
