#!/bin/bash

# Start Nginx in the background
nginx

# Start Auth Service on port 8001
echo "Starting Auth Service..."
(cd services/auth_service && uvicorn app.main:app --host 127.0.0.1 --port 8001) &

# Start Core Service on port 8002
echo "Starting Core Service..."
(cd services/core_service && uvicorn app.main:app --host 127.0.0.1 --port 8002)

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
