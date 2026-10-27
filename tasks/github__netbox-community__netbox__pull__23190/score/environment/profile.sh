#!/usr/bin/env bash
set -euo pipefail
case "${1:?setup, start or ready}" in
  setup)
    python3 -m venv venv
    if [[ ${DEV_ENV_LOCK_MODE:-restore} == resolve && ! -f .netbox-requirements.lock ]]; then
      uv pip compile --python venv/bin/python --generate-hashes requirements.txt -o .netbox-requirements.lock
    fi
    uv pip sync --python venv/bin/python --require-hashes .netbox-requirements.lock
    cat > netbox/netbox/configuration.py <<'PYCONFIG'
"""Local OSS runtime; accounts and data come from upstream demo SQL."""

import os

ALLOWED_HOSTS = ["*"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["PGDATABASE"],
        "USER": "netbox",
        "PASSWORD": os.environ["PGPASSWORD"],
        "HOST": os.environ["PGHOST"],
        "PORT": 5432,
        "CONN_MAX_AGE": 300,
    }
}
REDIS = {
    "tasks": {"HOST": os.environ["REDIS_HOST"], "PORT": 6379, "DATABASE": 0, "SSL": False},
    "caching": {"HOST": os.environ["REDIS_HOST"], "PORT": 6379, "DATABASE": 1, "SSL": False},
}
SECRET_KEY = "local-development-netbox-secret-key-with-fifty-characters"
API_TOKEN_PEPPERS = {1: "local-development-netbox-api-pepper-with-fifty-characters"}
DEBUG = False
PLUGINS = []
RELEASE_CHECK_URL = None
PYCONFIG
    if [[ ${DEV_ENV_LOCK_MODE:-restore} == resolve ]]; then
      # The native resolution intentionally pins 14.2.0, but Yarn 1 refuses
      # its own saved lock against the manifest's incompatible ^15.0.1 range.
      # Transport this dependency-only manifest repair alongside the locks.
      node - <<'JS'
const fs = require('fs');
const file = 'netbox/project-static/package.json';
const manifest = JSON.parse(fs.readFileSync(file, 'utf8'));
if (manifest.dependencies['markdown-it'] === '^15.0.1' && manifest.resolutions['**/markdown-it'] === '^14.2.0') {
  manifest.dependencies['markdown-it'] = '^14.2.0';
  fs.writeFileSync(file, JSON.stringify(manifest, null, 2) + '\n');
}
JS
    fi
    yarn --cwd netbox/project-static install --frozen-lockfile --non-interactive
    # Native bundle.cjs catches build errors; eliminate stale checked-in output.
    rm -rf netbox/project-static/dist
    yarn --cwd netbox/project-static bundle
    for asset in netbox.js netbox.css netbox-external.css cable_trace.css rack_elevation.css \
                 graphiql/react.production.min.js graphiql/react-dom.production.min.js graphiql/graphiql.min.js; do
      test -s "netbox/project-static/dist/$asset"
    done
    # Native install infrastructure roles, not application accounts or substitute data.
    if [[ $(psql -Atc "SELECT count(*) FROM pg_roles WHERE rolname='netbox'") == 0 ]]; then
      psql -v ON_ERROR_STOP=1 -c "CREATE ROLE netbox LOGIN PASSWORD 'profile-development'"
      psql -v ON_ERROR_STOP=1 -c 'ALTER DATABASE netbox OWNER TO netbox'
      psql -v ON_ERROR_STOP=1 -c 'GRANT ALL ON SCHEMA public TO netbox'
    fi
    if [[ $(psql -Atc "SELECT to_regclass('public.django_migrations') IS NOT NULL") == f ]]; then
      minor=$(venv/bin/python -c 'import yaml; print(".".join(yaml.safe_load(open("netbox/release.yaml"))["version"].split(".")[:2]))')
      # The published 4.7 dump has non-restorable ltree triggers (#23130).
      # Upstream supports native 4.6 -> 4.7 upgrades; use that complete demo
      # and let the checkout's own migrations initialize ltree correctly.
      if [[ $minor == 4.7 ]]; then minor=4.6; fi
      demo=https://raw.githubusercontent.com/netbox-community/netbox-demo-data/faeae5904a29ce6ad519a3de270ca218a7b050f9
      curl -fsSL "$demo/sql/netbox-demo-v$minor.sql" -o /tmp/netbox-demo.sql
      psql -v ON_ERROR_STOP=1 -f /tmp/netbox-demo.sql
      mkdir -p /logs/artifacts
      curl -fsSL "$demo/LICENSE.md" -o /logs/artifacts/netbox-demo-LICENSE.md
      rm /tmp/netbox-demo.sql
    fi
    venv/bin/python netbox/manage.py upgrade --no-input
    ;;
  start)
    mkdir -p /logs/artifacts
    export NETBOX_ROOT=$PWD
    envsubst '${NETBOX_ROOT}' < /opt/netbox-runtime/nginx.conf > /tmp/netbox-nginx.conf
    pids=()
    trap 'kill "${pids[@]}" 2>/dev/null || true; wait || true' EXIT INT TERM
    nginx -c /tmp/netbox-nginx.conf -g 'daemon off;' &
    pids+=("$!")
    venv/bin/python netbox/manage.py rqworker high default low > /logs/artifacts/netbox-worker.log 2>&1 &
    pids+=("$!")
    venv/bin/gunicorn --pythonpath netbox --bind 127.0.0.1:8001 --workers 2 --threads 2 \
      --timeout 120 netbox.wsgi > /logs/artifacts/netbox-gunicorn.log 2>&1 &
    pids+=("$!")
    wait -n "${pids[@]}"
    ;;
  ready)
    pg_isready -q
    test "$(redis-cli -h "$REDIS_HOST" ping)" = PONG
    test "$(redis-cli -h "$REDIS_HOST" scard rq:workers)" -ge 1
    curl -fsS --max-time 2 http://localhost:8080/login/ > /dev/null
    curl -fsS --max-time 2 http://localhost:8080/static/netbox.js > /dev/null
    ;;
  *) exit 2 ;;
esac
