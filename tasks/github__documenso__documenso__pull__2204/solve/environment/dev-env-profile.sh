#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start or ready}" in
  setup)
    cp .env.example .env
    npm ci --no-audit --no-fund
    npm run prisma:generate
    npm run prisma:migrate-deploy
    npx turbo run build --filter=@documenso/remix...
    npm run prisma:seed
    ;;
  start)
    export NEXT_PRIVATE_SIGNING_LOCAL_FILE_PATH="$PWD/apps/remix/example/cert.p12"
    exec npm run start -w @documenso/remix
    ;;
  ready)
    curl -fsS --max-time 3 http://localhost:3000/api/health |
      jq -e '.checks.database.status == "ok" and .status != "error"' >/dev/null
    ;;
  *) exit 2 ;;
esac
