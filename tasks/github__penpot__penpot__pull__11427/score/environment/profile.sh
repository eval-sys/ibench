#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start, or ready}" in
setup)
  bash -lc 'cd frontend && pnpm install --frozen-lockfile && clojure -P -M:dev:shadow-cljs && cd ../render-wasm && pnpm install --frozen-lockfile && cargo fetch --locked && cd ../backend && clojure -P -M && cd ../exporter && pnpm install --frozen-lockfile && clojure -P -M:dev:shadow-cljs && pnpm exec playwright install chromium'
  bash -ec 'bash /opt/penpot-runtime/prepare.sh'
  bash -ec 'bash /opt/penpot-runtime/build.sh'
  ;;
start)
  exec bash -ec 'bash /opt/penpot-runtime/start.sh'
  ;;
ready)
  bash -ec 'bash /opt/penpot-runtime/dependencies-ready.sh'
  bash -ec 'bash /opt/penpot-runtime/healthcheck.sh'
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
