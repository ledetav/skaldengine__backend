# Stage 1: Build dependencies
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY services/auth_service/requirements.txt ./auth_req.txt
COPY services/core_service/requirements.txt ./core_req.txt
RUN pip install --no-cache-dir --user -r auth_req.txt -r core_req.txt

# Stage 2: Final image
FROM python:3.11-slim
WORKDIR /app

# Create a non-root user
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 nginx && rm -rf /var/lib/apt/lists/*

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser services/ ./services/
COPY --chown=appuser:appuser shared/ ./shared/
COPY --chown=appuser:appuser start.sh ./start.sh
RUN chmod +x ./start.sh

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CORE_UPLOAD_DIR=/app/uploads

# Ensure permissions for Nginx and Uploads
RUN mkdir -p /app/uploads && \
    mkdir -p /var/lib/nginx/body /var/cache/nginx /var/log/nginx /run /etc/nginx && \
    chown -R appuser:appuser /var/lib/nginx /var/cache/nginx /var/log/nginx /run /etc/nginx /app/uploads && \
    chmod -R 770 /var/lib/nginx /var/cache/nginx /var/log/nginx /run /etc/nginx /app/uploads

# Nginx Config - Listening on 8000, routing to services
RUN echo 'daemon off;\nuser appuser;\n' > /etc/nginx/nginx.conf && \
    cat /etc/nginx/nginx.conf.default | grep -v user >> /etc/nginx/nginx.conf || true && \
    echo 'server {\n\
    listen 8000;\n\
    client_max_body_size 20M;\n\
    location /api/v1/auth { proxy_pass http://127.0.0.1:8001; proxy_set_header Host $host; }\n\
    location /api/v1/users { proxy_pass http://127.0.0.1:8001; proxy_set_header Host $host; }\n\
    location / { \n\
        proxy_pass http://127.0.0.1:8002; \n\
        proxy_set_header Host $host; \n\
        proxy_http_version 1.1; \n\
        proxy_set_header Upgrade $http_upgrade; \n\
        proxy_set_header Connection "upgrade"; \n\
    }\n\
    location /static/ { \n\
        alias /app/uploads/; \n\
    }\n\
}' > /etc/nginx/sites-available/default

# Primary Exposed Port
EXPOSE 8000

USER appuser

# Start command
CMD ["./start.sh"]
