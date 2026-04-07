#!/bin/sh
# Start script for SkaldEngine services with Nginx routing.

# Exit on any error
set -e

echo "=== System Check ==="
echo "Operating Directory: $(pwd)"

# Ensure Nginx config is correctly placed
echo "Configuring Nginx..."
rm -f /etc/nginx/sites-enabled/default
ln -sf /app/nginx.conf /etc/nginx/sites-enabled/default

# Create necessary directories for Nginx
mkdir -p /var/log/nginx
mkdir -p /run/nginx

echo "Starting Nginx in background..."
nginx &

# Check if we should starting individual services or combined mode
if [ "$SERVICE_NAME" = "auth" ]; then
    echo "Starting Auth Service on 8001..."
    cd /app/services/auth_service && uvicorn app.main:app --host 0.0.0.0 --port 8001
elif [ "$SERVICE_NAME" = "core" ]; then
    echo "Starting Core Service on 8000..."
    cd /app/services/core_service && uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "Starting Services in COMBINED mode..."
    
    # Start Auth Service in background
    echo "Starting Auth Service (background)..."
    (cd /app/services/auth_service && uvicorn app.main:app --host 127.0.0.1 --port 8001) &
    
    # Start Core Service in foreground
    echo "Starting Core Service (foreground)..."
    cd /app/services/core_service && uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
