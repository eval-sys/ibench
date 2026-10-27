#!/usr/bin/env bash
set -euo pipefail

api=http://127.0.0.1:8000

instance_ready() {
  curl -fsS "$api/api/instances/" | python3 -c \
    'import json, sys; raise SystemExit(json.load(sys.stdin).get("instance", {}).get("is_setup_done") is not True)'
}

if instance_ready; then
  exit 0
fi

cookie_jar="$(mktemp)"
trap 'rm -f "$cookie_jar"' EXIT
csrf_token="$(
  curl -fsS -c "$cookie_jar" "$api/auth/get-csrf-token/" \
    | python3 -c 'import json, sys; print(json.load(sys.stdin)["csrf_token"])'
)"
status="$(
  curl -sS -o /dev/null -w '%{http_code}' \
    -b "$cookie_jar" -c "$cookie_jar" \
    -H "Referer: $api/" \
    -H "X-CSRFToken: $csrf_token" \
    --data-urlencode "email=${DEV_ENV_ADMIN_EMAIL:?}" \
    --data-urlencode "password=${DEV_ENV_ADMIN_PASSWORD:?}" \
    --data-urlencode "first_name=${DEV_ENV_ADMIN_FIRST_NAME:?}" \
    --data-urlencode "last_name=${DEV_ENV_ADMIN_LAST_NAME:?}" \
    --data-urlencode "company_name=${DEV_ENV_ADMIN_COMPANY:?}" \
    --data-urlencode is_telemetry_enabled=False \
    "$api/api/instances/admins/sign-up/"
)"
test "$status" = 302
instance_ready
