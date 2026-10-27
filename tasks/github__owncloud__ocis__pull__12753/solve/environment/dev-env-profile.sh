#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app

case "${1:?setup, start or ready}" in
  setup)
    pnpm --dir web install --frozen-lockfile
    pnpm --dir web check:types
    pnpm --dir web build
    cp web/config/config.json.dist web/dist/config.json
    mkdir -p services/web/assets/core
    cp -a web/dist/. services/web/assets/core/
    # The upstream Make target misses sibling service and embedded Web changes.
    # Go's own cache still avoids recompiling unchanged packages.
    make -B -C ocis build GOTOOLCHAIN=local
    git diff --exit-code -- go.mod go.sum web/pnpm-lock.yaml
    ;;
  start)
    mkdir -p "$OCIS_CONFIG_DIR" "$OCIS_BASE_DATA_PATH"
    if [[ ! -f "$OCIS_CONFIG_DIR/ocis.yaml" ]]; then
      ./ocis/bin/ocis init --insecure true --admin-password admin
    fi
    # Native service configuration limits the UI to local, built-in applications.
    cat > "$OCIS_CONFIG_DIR/web.yaml" <<'YAML'
web:
  config:
    apps: [files, search, text-editor, pdf-viewer, admin-settings, epub-reader, preview]
YAML
    exec ./ocis/bin/ocis server
    ;;
  ready)
    curl --fail --silent --show-error http://localhost:9205/healthz > /dev/null
    curl --fail --silent --show-error http://localhost:9104/healthz > /dev/null
    curl --fail --silent --show-error --insecure https://localhost:9200/.well-known/openid-configuration \
      | jq -e '.issuer == "https://localhost:9200"' > /dev/null
    curl --fail --silent --show-error --insecure https://localhost:9200/config.json \
      | jq -e '.server == "https://localhost:9200"' > /dev/null
    ;;
  *) exit 2 ;;
esac
