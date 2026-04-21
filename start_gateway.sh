#!/bin/bash
export PYTHONPATH="/home/runner/workspace:$PYTHONPATH"

bash /home/runner/workspace/start_auth.sh &
bash /home/runner/workspace/start_core.sh &

echo "Waiting for auth service on port 8001..."
for i in $(seq 1 30); do
  if python3 -c "import socket; s=socket.create_connection(('127.0.0.1', 8001), timeout=1)" 2>/dev/null; then
    echo "Auth service is up!"
    break
  fi
  echo "  Auth not ready yet, retrying in 1s... ($i/30)"
  sleep 1
done

echo "Waiting for core service on port 8000..."
for i in $(seq 1 30); do
  if python3 -c "import socket; s=socket.create_connection(('127.0.0.1', 8000), timeout=1)" 2>/dev/null; then
    echo "Core service is up!"
    break
  fi
  echo "  Core not ready yet, retrying in 1s... ($i/30)"
  sleep 1
done

echo "Starting gateway on port 5000..."
cd /home/runner/workspace
exec python3 -m uvicorn gateway.main:app --host 0.0.0.0 --port 5000
