#!/bin/bash
export PYTHONPATH="/home/runner/workspace:$PYTHONPATH"
cd /home/runner/workspace/services/core_service
exec python3 -m uvicorn app.main:app --host localhost --port 8000
