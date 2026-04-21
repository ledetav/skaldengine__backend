#!/bin/bash
export PYTHONPATH="/home/runner/workspace:$PYTHONPATH"
cd /home/runner/workspace/services/core_service
exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
