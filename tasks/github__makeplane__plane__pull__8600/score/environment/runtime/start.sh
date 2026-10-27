#!/usr/bin/env bash
set -euo pipefail

workspace=/workspace/app
mkdir -p /logs/artifacts
source /opt/plane-api/bin/activate

cd "$workspace/apps/api"
./bin/docker-entrypoint-migrator.sh --settings=plane.settings.local \
  > /logs/artifacts/plane-migrator.log 2>&1
nohup ./bin/docker-entrypoint-api-local.sh > /logs/artifacts/plane-api.log 2>&1 &
api_pid=$!

for attempt in {1..120}; do
  if nc -z 127.0.0.1 8000; then
    break
  fi
  if ! kill -0 "$api_pid" 2>/dev/null; then
    tail -100 /logs/artifacts/plane-api.log
    exit 1
  fi
  sleep 1
done
nc -z 127.0.0.1 8000
bash /opt/plane-runtime/initialize.sh

nohup ./bin/docker-entrypoint-worker.sh > /logs/artifacts/plane-worker.log 2>&1 &
nohup ./bin/docker-entrypoint-beat.sh > /logs/artifacts/plane-beat.log 2>&1 &
cd "$workspace"
exec caddy run --config /opt/plane-runtime/Caddyfile
