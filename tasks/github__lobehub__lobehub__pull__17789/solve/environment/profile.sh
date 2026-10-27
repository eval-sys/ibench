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
  bash -ec 'if node -e '"'"'const s=require("./package.json").scripts||{};process.exit(s["db:migrate"]?0:1)'"'"'; then pnpm db:migrate; fi'
  bash -ec 'pnpm build'
  ;;
start)
  exec bash -ec 'pnpm start'
  ;;
ready)
  bash -ec 'pg_isready -q -h postgresql -U postgres -d lobechat && redis-cli -h redis ping | grep -q PONG && curl -fsS http://rustfs:9000/health'
  bash -ec 'curl -fsS http://localhost:3210/'
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
