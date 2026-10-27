#!/usr/bin/env bash
set -euo pipefail

pids=()
run_backend() {
  while node packages/hoppscotch-backend/dist/src/main.js; do
    sleep 1
  done
}
cleanup() {
  trap - EXIT TERM INT
  kill "${pids[@]}" 2>/dev/null || true
  wait "${pids[@]}" 2>/dev/null || true
}
trap cleanup EXIT TERM INT

run_backend &
pids+=("$!")
pnpm start &
pids+=("$!")
pnpm --filter hoppscotch-sh-admin preview --host 0.0.0.0 --port 3100 &
pids+=("$!")

wait -n "${pids[@]}"
