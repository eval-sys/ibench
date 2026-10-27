#!/usr/bin/env bash
set -euo pipefail

runtime=/tmp/gitea-runtime
case "${1:?setup, start or ready}" in
  setup)
    pnpm install --frozen-lockfile
    go mod download
    TAGS=bindata make build
    git diff --exit-code -- pnpm-lock.yaml go.mod go.sum
    rm -rf "$runtime"
    install -d -o git -g git "$runtime/custom/conf"
    cat > "$runtime/custom/conf/app.ini" <<EOF
APP_NAME = Gitea
RUN_USER = git
RUN_MODE = prod
WORK_PATH = $runtime

[database]
DB_TYPE = sqlite3
PATH = $runtime/data/gitea.db

[repository]
ROOT = $runtime/repositories

[server]
HTTP_ADDR = 0.0.0.0
HTTP_PORT = 3000
ROOT_URL = http://localhost:3000/
STATIC_ROOT_PATH = $PWD
DISABLE_SSH = true

[security]
INSTALL_LOCK = false

[service]
ENABLE_CAPTCHA = false

[mailer]
ENABLED = false

[actions]
ENABLED = false

[cron]
ENABLED = false

[log]
MODE = console
LEVEL = Info
EOF
    chown -R git:git "$runtime"
    ;;
  start)
    exec runuser -u git -- "$PWD/gitea" --work-path "$runtime" --config "$runtime/custom/conf/app.ini" web
    ;;
  ready)
    curl --fail --silent --show-error http://localhost:3000/api/healthz |
      python3 -c 'import json,sys; assert json.load(sys.stdin)["status"] == "pass"'
    curl --fail --silent --show-error --output /dev/null http://localhost:3000/
    ;;
  *) exit 2 ;;
esac
