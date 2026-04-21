# ── Core Service Dockerfile ───────────────────────────────────────────────────
# Build context: repo root (so we can include shared/)

# Stage 1: install dependencies
FROM python:3.12-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY services/core_service/requirements.txt ./requirements.txt
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
COPY --chown=appuser:appuser services/core_service/ ./services/core_service/

# Uploads volume mount point
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CORE_UPLOAD_DIR=/app/uploads

USER appuser

WORKDIR /app/services/core_service

EXPOSE 8000

# Run migrations then start server
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
