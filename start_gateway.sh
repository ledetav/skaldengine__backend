#!/bin/bash
export PYTHONPATH="/home/runner/workspace:$PYTHONPATH"

bash /home/runner/workspace/start_auth.sh &
bash /home/runner/workspace/start_core.sh &

echo "Waiting for auth and core services to start..."
sleep 3

cd /home/runner/workspace
exec python3 -m uvicorn gateway.main:app --host 0.0.0.0 --port 5000
