#!/usr/bin/env bash
set -euo pipefail
case "$1" in
  setup)
    test ! -e ext
    env GRIST_EDITION=community GRIST_SKIP_EXT_AUTOSETUP=1 yarn install --frozen-lockfile --production=false --network-timeout 600000
    yarn run install:python
    yarn run build:prod
    git diff --exit-code -- yarn.lock sandbox/requirements.txt
    mkdir -p "$GRIST_DATA_DIR" "$GRIST_INST_DIR"
    ;;
  start)
    cd /workspace/app
    exec yarn run start:prod
    ;;
  ready)
    curl --fail --silent --show-error --max-time 2 "$OIDC_ISSUER_URL/keys" | jq -e '.keys | length > 0' >/dev/null
    curl --fail --silent --show-error --max-time 10 'http://localhost:8484/status?db=1&ready=1' >/dev/null
    ;;
  *) exit 2 ;;
esac
