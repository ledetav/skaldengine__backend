#!/bin/bash
export PYTHONPATH="/home/runner/workspace:$PYTHONPATH"
cd /home/runner/workspace/services/core_service

echo "Running core service migrations..."
python3 -m alembic upgrade head

echo "Starting core service on port 8000..."
exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
