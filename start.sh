#!/bin/sh
# Start script for concurrent SkaldEngine services with Nginx routing.

echo "Configuring Nginx routing..."
# Link custom Nginx config and remove default
rm -f /etc/nginx/sites-enabled/default
ln -sf /app/nginx.conf /etc/nginx/sites-enabled/default
# Start Nginx service
service nginx start

if [ "$SERVICE_NAME" = "auth" ]; then
    echo "Starting Auth Service exclusively on 8001..."
    cd /app/services/auth_service && uvicorn app.main:app --host 0.0.0.0 --port 8001
elif [ "$SERVICE_NAME" = "core" ]; then
    echo "Starting Core Service exclusively on 8000..."
    cd /app/services/core_service && uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "Starting services in combined mode with Nginx routing on port 80..."
    # Start Auth Service in background
    cd /app/services/auth_service && uvicorn app.main:app --host 0.0.0.0 --port 8001 &
    # Start Core Service in foreground
    cd /app/services/core_service && uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
