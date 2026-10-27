#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start, or ready}" in
setup)
  bun install --frozen-lockfile
  bash -ec 'mkdir -p /var/lib/metabase/plugins'
  bash -ec 'INTERACTIVE=false CI=true MB_EDITION=oss bin/build.sh'
  ;;
start)
  exec bash -ec 'java -Xmx4096m -jar target/uberjar/metabase.jar'
  ;;
ready)
  bash -ec 'pg_isready -q -h postgresql -U metabase -d metabase'
  bash -ec 'curl -fsS http://localhost:3000/api/health | jq -e '"'"'.status == "ok"'"'"' > /dev/null'
  properties="$(curl -fsS http://localhost:3000/api/session/properties)"
  if [[ "$(jq -r '.["has-user-setup"]' <<<"$properties")" != true ]]; then
    curl -fsS http://localhost:3000/api/setup \
      -H 'Content-Type: application/json' \
      --data "$(
        jq -cn \
          --arg token "$(jq -er '.["setup-token"]' <<<"$properties")" \
          --arg email "${DEV_ENV_ADMIN_EMAIL:?}" \
          --arg password "${DEV_ENV_ADMIN_PASSWORD:?}" \
          '{
            token: $token,
            user: {
              first_name: "Bobby",
              last_name: "Tables",
              email: $email,
              password: $password
            },
            prefs: {
              site_name: "Epic Team",
              allow_tracking: false
            },
            database: null
          }'
      )" >/dev/null
  fi
  session_id="$(
    curl -fsS http://localhost:3000/api/session \
      -H 'Content-Type: application/json' \
      --data "$(jq -cn --arg username "$DEV_ENV_ADMIN_EMAIL" --arg password "$DEV_ENV_ADMIN_PASSWORD" '{username: $username, password: $password}')" \
      | jq -er '.id'
  )"
  curl -fsS http://localhost:3000/api/user/current \
    -H "X-Metabase-Session: $session_id" \
    | jq -e --arg email "$DEV_ENV_ADMIN_EMAIL" '.email == $email and .is_superuser == true' >/dev/null
  curl -fsS http://mailpit:8025/api/v1/info | jq -e '.Database' >/dev/null
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
