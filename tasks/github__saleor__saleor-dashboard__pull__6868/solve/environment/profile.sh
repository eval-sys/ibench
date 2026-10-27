#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start, or ready}" in
setup)
  generated=()
  mapfile -d '' -t generated < <(git ls-files -z -- 'src/graphql/*.generated.ts')
  restore_generated() {
    ((${#generated[@]} == 0)) || git restore --worktree -- "${generated[@]}"
  }
  trap restore_generated EXIT
  pnpm install --frozen-lockfile
  bash -ec 'pnpm run generate:main && pnpm exec cross-env NODE_OPTIONS=--max-old-space-size=8192 vite build'
  restore_generated
  trap - EXIT
  ;;
start)
  exec bash -ec 'pnpm exec vite preview --host 0.0.0.0 --port 9000'
  ;;
ready)
  bash -ec 'bash /opt/saleor-dashboard-runtime/dependencies-ready.sh'
  bash -ec 'curl -fsS http://localhost:9000/ > /dev/null'
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
