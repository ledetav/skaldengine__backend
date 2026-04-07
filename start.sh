#!/bin/sh
# This script starts the backend services.
# If SERVICE_NAME is set to 'auth' or 'core', it starts only that service.
# Otherwise, it starts both (standard for monolithic autodeploy).

if [ "$SERVICE_NAME" = "auth" ]; then
    echo "Starting Auth Service..."
    cd /app/services/auth_service && uvicorn app.main:app --host 0.0.0.0 --port 8001
elif [ "$SERVICE_NAME" = "core" ]; then
    echo "Starting Core Service..."
    cd /app/services/core_service && uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "Starting both services (Monolithic mode)..."
    # Start Auth Service in background
    cd /app/services/auth_service && uvicorn app.main:app --host 0.0.0.0 --port 8001 &
    # Start Core Service in foreground
    cd /app/services/core_service && uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
