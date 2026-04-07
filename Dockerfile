# Multistage build for slim image
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from all services
COPY services/auth_service/requirements.txt ./auth_req.txt
COPY services/core_service/requirements.txt ./core_req.txt

# Install all dependencies into user directory
RUN pip install --no-cache-dir --user -r auth_req.txt -r core_req.txt

# Final image
FROM python:3.10-slim

WORKDIR /app

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages and code from builder
COPY --from=builder /root/.local /root/.local
# Copy all services code
COPY services/ ./services/
# Copy the start script
COPY start.sh /app/start.sh

# Environment setup
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Ensure uploads directory exists
RUN mkdir -p /app/services/core_service/uploads

RUN chmod +x /app/start.sh

# Expose ports for both services
EXPOSE 8000
EXPOSE 8001

CMD ["/app/start.sh"]
