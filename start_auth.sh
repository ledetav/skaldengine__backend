#!/bin/bash
export PYTHONPATH="/home/runner/workspace:$PYTHONPATH"
cd /home/runner/workspace/services/auth_service
exec python3 -m uvicorn app.main:app --host localhost --port 8001
