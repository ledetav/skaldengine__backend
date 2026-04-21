#!/bin/bash
export PYTHONPATH="/home/runner/workspace:$PYTHONPATH"
cd /home/runner/workspace/services/auth_service
exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001
