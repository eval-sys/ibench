#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start, or ready}" in
setup)
  yarn install --immutable
  bash -ec 'yarn build:browser --skip-translations'
  ;;
start)
  exec bash -ec 'PORT=3210 node packages/desktop-client/bin/serve-build.mjs'
  ;;
ready)
  bash -ec true
  bash -ec 'curl -fsS http://localhost:3210/ > /dev/null && curl -fsS http://localhost:3210/sql-wasm.wasm > /dev/null'
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
