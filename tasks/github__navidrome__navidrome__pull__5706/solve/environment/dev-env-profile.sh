#!/usr/bin/env bash
set -euo pipefail

case "${1:?setup, start or ready}" in
  setup)
    npm --prefix ui ci
    go mod download
    make build
    git diff --exit-code -- ui/package-lock.json go.mod go.sum
    rm -rf /tmp/navidrome-runtime
    mkdir -p "$ND_DATAFOLDER" "$ND_MUSICFOLDER"
    ;;
  start)
    exec "$PWD/navidrome"
    ;;
  ready)
    curl --fail --silent --show-error --max-time 2 --output /dev/null http://localhost:4533/ping
    curl --fail --silent --show-error --max-time 2 --output /dev/null http://localhost:4533/app/
    ;;
  *) exit 2 ;;
esac
