#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start, or ready}" in
setup)
  yarn install --immutable
  bash -ec 'yarn db-deploy'
  bash -ec 'yarn workspace @calcom/trpc run build && yarn --cwd packages/embeds/embed-core workspace @calcom/embed-core run build && yarn --cwd apps/web workspace @calcom/web run copy-app-store-static && yarn --cwd apps/web workspace @calcom/web run build'
  ;;
start)
  exec bash -ec 'yarn start'
  ;;
ready)
  bash -ec 'pg_isready -q -h postgresql -U postgres -d calendso'
  bash -ec 'curl -fsS http://localhost:3000/api/version > /dev/null'
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
