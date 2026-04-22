# Stage 1: Build dependencies
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY services/auth_service/requirements.txt ./auth_req.txt
COPY services/core_service/requirements.txt ./core_req.txt
RUN pip install --no-cache-dir --prefix=/install -r auth_req.txt -r core_req.txt

# Stage 2: Final image
FROM python:3.11-slim
WORKDIR /app

# Create a non-root user
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder to /usr/local
COPY --from=builder /install /usr/local

COPY --chown=appuser:appuser services/ ./services/
COPY --chown=appuser:appuser shared/ ./shared/

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CORE_UPLOAD_DIR=/app/uploads
ENV PATH=/usr/local/bin:$PATH

# Ensure permissions for Uploads
RUN mkdir -p /app/uploads && \
    chown -R appuser:appuser /app/uploads && \
    chmod -R 775 /app/uploads

# Expose ports that might be used
EXPOSE 8001
EXPOSE 8002

USER appuser

# Let docker-compose override the command
CMD ["python", "-c", "print('No default CMD specified. Please run via docker-compose.')"]
