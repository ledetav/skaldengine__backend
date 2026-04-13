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
    libpq5 nginx && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder to /usr/local
COPY --from=builder /install /usr/local

COPY --chown=appuser:appuser services/ ./services/
COPY --chown=appuser:appuser shared/ ./shared/
COPY --chown=appuser:appuser start.sh ./start.sh
RUN chmod +x ./start.sh

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CORE_UPLOAD_DIR=/app/uploads
ENV PATH=/usr/local/bin:$PATH

# Ensure permissions for Nginx and Uploads
RUN mkdir -p /app/uploads && \
    mkdir -p /var/lib/nginx/body /var/cache/nginx /var/log/nginx /run /etc/nginx && \
    chown -R appuser:appuser /var/lib/nginx /var/cache/nginx /var/log/nginx /run /etc/nginx /app/uploads && \
    chmod -R 775 /var/lib/nginx /var/cache/nginx /var/log/nginx /run /etc/nginx /app/uploads

# Nginx Config - Properly structured with events section and stdout logging
RUN echo 'daemon off;' > /etc/nginx/nginx.conf && \
    echo 'error_log /dev/stderr warn;' >> /etc/nginx/nginx.conf && \
    echo 'pid /run/nginx.pid;' >> /etc/nginx/nginx.conf && \
    echo 'events { worker_connections 1024; }' >> /etc/nginx/nginx.conf && \
    echo 'http {' >> /etc/nginx/nginx.conf && \
    echo '    include /etc/nginx/mime.types;' >> /etc/nginx/nginx.conf && \
    echo '    default_type application/octet-stream;' >> /etc/nginx/nginx.conf && \
    echo '    access_log /dev/stdout;' >> /etc/nginx/nginx.conf && \
    echo '    sendfile on;' >> /etc/nginx/nginx.conf && \
    echo '    keepalive_timeout 65;' >> /etc/nginx/nginx.conf && \
    echo '    server {' >> /etc/nginx/nginx.conf && \
    echo '        listen 8000;' >> /etc/nginx/nginx.conf && \
    echo '        client_max_body_size 20M;' >> /etc/nginx/nginx.conf && \
    echo '        location /api/v1/auth { proxy_pass http://127.0.0.1:8001; proxy_set_header Host $host; }' >> /etc/nginx/nginx.conf && \
    echo '        location /api/v1/users { proxy_pass http://127.0.0.1:8001; proxy_set_header Host $host; }' >> /etc/nginx/nginx.conf && \
    echo '        location / { ' >> /etc/nginx/nginx.conf && \
    echo '            proxy_pass http://127.0.0.1:8002; ' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Host $host; ' >> /etc/nginx/nginx.conf && \
    echo '            proxy_http_version 1.1; ' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Upgrade $http_upgrade; ' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Connection "upgrade"; ' >> /etc/nginx/nginx.conf && \
    echo '        }' >> /etc/nginx/nginx.conf && \
    echo '        location /static/ { alias /app/uploads/; }' >> /etc/nginx/nginx.conf && \
    echo '    }' >> /etc/nginx/nginx.conf && \
    echo '}' >> /etc/nginx/nginx.conf

# Primary Exposed Port
EXPOSE 8000

USER appuser

# Start command
CMD ["./start.sh"]
