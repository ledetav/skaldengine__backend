# Stage 1: Build dependencies
FROM python:3.10-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY services/auth_service/requirements.txt ./auth_req.txt
COPY services/core_service/requirements.txt ./core_req.txt
RUN pip install --no-cache-dir --user -r auth_req.txt -r core_req.txt

# Stage 2: Final image
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 nginx && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY services/ ./services/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Ensure permissions for Nginx to run as non-root if needed
RUN mkdir -p /app/services/core_service/uploads && \
    mkdir -p /var/cache/nginx /var/log/nginx /run && \
    chmod -R 777 /var/cache/nginx /var/log/nginx /run

# Updated Nginx Config - Listening on 8000
RUN echo 'server {\n\
    listen 8000;\n\
    location /api/v1/auth { proxy_pass http://127.0.0.1:8001; proxy_set_header Host $host; }\n\
    location /api/v1/users { proxy_pass http://127.0.0.1:8001; proxy_set_header Host $host; }\n\
    location / { \n\
        proxy_pass http://127.0.0.1:8002; \n\
        proxy_set_header Host $host; \n\
        proxy_http_version 1.1; \n\
        proxy_set_header Upgrade $http_upgrade; \n\
        proxy_set_header Connection "upgrade"; \n\
    }\n\
}' > /etc/nginx/sites-available/default

# Primary Exposed Port
EXPOSE 8000

# Start command: Nginx in background, then Services.
# Auth Service -> 8001
# Core Service -> 8002 (matching Nginx config above)
CMD nginx && \
    (cd services/auth_service && DATABASE_URL=$AUTH_DATABASE_URL SECRET_KEY=$SECRET_KEY uvicorn app.main:app --host 127.0.0.1 --port 8001 &) && \
    (cd services/core_service && DATABASE_URL=$CORE_DATABASE_URL SECRET_KEY=$SECRET_KEY POLZA_API_KEY=$POLZA_API_KEY uvicorn app.main:app --host 127.0.0.1 --port 8002)
