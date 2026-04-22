#!/bin/bash

# Ожидание и применение миграций для Auth Service
echo "Applying Auth Service migrations..."
(
  cd services/auth_service || exit
  until alembic upgrade head; do
    echo "Auth DB is unavailable or starting up - sleeping 2s..."
    sleep 2
  done
  echo "Auth Service migrations applied successfully!"
)

# Ожидание и применение миграций для Core Service
echo "Applying Core Service migrations..."
(
  cd services/core_service || exit
  until alembic upgrade head; do
    echo "Core DB is unavailable or starting up - sleeping 2s..."
    sleep 2
  done
  echo "Core Service migrations applied successfully!"
)

# Start Nginx in the background
nginx &

# Start Auth Service on port 8001
echo "Starting Auth Service..."
(cd services/auth_service && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001) &

# Start Core Service on port 8002
echo "Starting Core Service..."
(cd services/core_service && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002)

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
