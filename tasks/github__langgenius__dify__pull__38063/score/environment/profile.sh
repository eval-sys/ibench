#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start, or ready}" in
setup)
  bash -lc 'pnpm install --frozen-lockfile && uv sync --project api --frozen --group dev'
  bash -ec 'bash /opt/dify-runtime/prepare.sh'
  bash -ec 'pnpm --dir web build'
  ;;
start)
  exec bash -ec 'bash /opt/dify-runtime/start.sh'
  ;;
ready)
  pg_isready -q -d "$DATABASE_URL"
  redis-cli -h redis -a difyai123456 ping | grep -q PONG
  curl -fsS http://weaviate:8080/v1/.well-known/ready > /dev/null
  curl -fsS --max-time 10 http://plugin-daemon:5002/health/check |
    jq -e '.status == "ok" and .platform == "local"' > /dev/null
  curl -fsS --max-time 10 http://localhost:5001/health |
    jq -e '.status == "ok"' > /dev/null
  curl -fsS --max-time 10 http://localhost:5001/console/api/setup |
    jq -e '.step == "finished"' > /dev/null
  curl -fsS --max-time 10 http://localhost:3210/signin > /dev/null
  kill -0 "$(cat /tmp/dify-worker.pid)"
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
