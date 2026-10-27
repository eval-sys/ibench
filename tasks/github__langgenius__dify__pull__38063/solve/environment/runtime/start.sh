#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/artifacts
pids=()
trap 'for pid in "${pids[@]}"; do kill -- "-$pid" 2>/dev/null || true; done' EXIT
trap 'exit 143' TERM INT
setsid uv run --frozen --directory api dotenv -f .env run --no-override -- python -m app > /logs/artifacts/dify-api.log 2>&1 &
pids+=("$!")
bash /opt/dify-runtime/bootstrap.sh > /logs/artifacts/dify-bootstrap.log 2>&1
setsid bash dev/start-worker --concurrency 1 > /logs/artifacts/dify-worker.log 2>&1 &
pids+=("$!")
printf '%s\n' "$!" > /tmp/dify-worker.pid
setsid env NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3210 pnpm --dir web start > /logs/artifacts/dify-web.log 2>&1 &
pids+=("$!")
wait -n "${pids[@]}"
exit 1
