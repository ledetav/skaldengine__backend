# ── Auth Service Dockerfile ───────────────────────────────────────────────────
# Build context: repo root (so we can include shared/)

# Stage 1: install dependencies
FROM python:3.12-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY services/auth_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

COPY --from=builder /install /usr/local

# Copy source
COPY --chown=appuser:appuser shared/ ./shared/
COPY --chown=appuser:appuser services/auth_service/ ./services/auth_service/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

USER appuser

WORKDIR /app/services/auth_service

# Run migrations then start server
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"]
