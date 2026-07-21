# Stage 1: Build
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install -e ".[ocr,embeddings]"

# Stage 2: Production
FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system --gid 1001 ultron && \
    adduser --system --uid 1001 --gid 1001 ultron

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY alembic.ini alembic/ ./
COPY app/ ./app/

RUN chown -R ultron:ultron /app

USER ultron

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
