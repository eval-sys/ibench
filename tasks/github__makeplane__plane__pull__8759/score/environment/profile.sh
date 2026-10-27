#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start, or ready}" in
setup)
  bash -lc 'pnpm install --frozen-lockfile && python3 -m venv /opt/plane-api && /opt/plane-api/bin/pip install --no-cache-dir -r apps/api/requirements/local.txt'
  bash -ec 'bash /opt/plane-runtime/prepare.sh'
  bash -ec 'pnpm exec turbo run build --filter=web'
  ;;
start)
  exec bash -ec 'bash /opt/plane-runtime/start.sh'
  ;;
ready)
  bash -ec 'pg_isready -q -h plane-db -U plane -d plane && redis-cli -h plane-redis ping | grep -q PONG && nc -z plane-mq 5672 && curl -fsS http://plane-rustfs:9000/health > /dev/null'
  bash -ec 'curl -fsS http://localhost:3000/ > /dev/null && curl -fsS http://localhost:8000/ > /dev/null'
  curl -fsS http://localhost:8000/api/instances/ | python3 -c \
    'import json, sys; raise SystemExit(json.load(sys.stdin).get("instance", {}).get("is_setup_done") is not True)'
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
