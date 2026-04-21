#!/bin/bash
export PYTHONPATH="/home/runner/workspace:$PYTHONPATH"

bash /home/runner/workspace/start_auth.sh > auth.log 2>&1 &
bash /home/runner/workspace/start_core.sh > core.log 2>&1 &

echo "Waiting for auth and core services to start..."
sleep 5

cd /home/runner/workspace
exec python3 -m uvicorn gateway.main:app --host 0.0.0.0 --port 5000
