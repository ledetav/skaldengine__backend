#!/bin/bash
export PYTHONPATH="/home/runner/workspace:$PYTHONPATH"
cd /home/runner/workspace/services/auth_service

echo "Running auth service migrations..."
python3 -m alembic upgrade head

echo "Starting auth service on port 8001..."
exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001
