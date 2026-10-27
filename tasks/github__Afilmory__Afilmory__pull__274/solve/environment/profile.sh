#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start, or ready}" in
setup)
  if [[ ${DEV_ENV_LOCK_MODE:-restore} == resolve ]]; then
    cutoff_epoch="$(git show -s --format=%ct HEAD)"
    now_epoch="$(date +%s)"
    test "$cutoff_epoch" -le "$now_epoch"
    minimum_release_age_minutes=$(( (now_epoch - cutoff_epoch) / 60 ))
    pnpm install --lockfile-only --lockfile=true --ignore-scripts --config.resolution-mode=highest --config.minimum-release-age="$minimum_release_age_minutes"
  fi
  pnpm install --frozen-lockfile --lockfile=true
  bash -ec 'bash /opt/dev-env-fixtures/prepare.sh'
  bash -ec 'pnpm --filter @afilmory/web build:serve && pnpm --filter @afilmory/dashboard build && pnpm --filter @afilmory/core build'
  ;;
start)
  exec bash -ec 'pnpm --filter @afilmory/core exec vite-node --config fixture.vite.config.ts src/index.ts'
  ;;
ready)
  bash -ec 'pg_isready -q -h postgresql -U postgres -d afilmory && redis-cli -h redis ping && curl -sS http://rustfs:9000/ -o /dev/null'
  bash -ec 'curl -fsS http://localhost:3210/api/manifest && curl -fsS http://root.localhost:3210/platform/root-login'
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
