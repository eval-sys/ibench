#!/usr/bin/env bash
set -euo pipefail

base_url="${APP_URL:?}"
admin_email="${DEV_ENV_ADMIN_EMAIL:?}"
admin_password="${DEV_ENV_ADMIN_PASSWORD:?}"
database_name='LB PR80439 Alert Source'
question_name='PR 80439 Alert Target Check'

properties="$(curl -fsS "$base_url/api/session/properties")"
if [[ "$(jq -r '.["has-user-setup"]' <<<"$properties")" != 'true' ]]; then
  exit 0
fi

login_payload="$(
  jq -cn \
    --arg username "$admin_email" \
    --arg password "$admin_password" \
    '{username: $username, password: $password}'
)"
if ! login_response="$(
  curl -fsS \
    -X POST "$base_url/api/session" \
    -H 'Content-Type: application/json' \
    --data "$login_payload" 2>/dev/null
)"; then
  exit 0
fi

session_id="$(jq -er '.id' <<<"$login_response")"
auth_header="X-Metabase-Session: $session_id"

while read -r card_id; do
  [[ -z "$card_id" ]] || curl -fsS \
    -X DELETE "$base_url/api/card/$card_id" \
    -H "$auth_header" >/dev/null
done < <(
  curl -fsS "$base_url/api/card?f=all" -H "$auth_header" |
    jq -r --arg name "$question_name" '.[] | select(.name == $name) | .id'
)

while read -r database_id; do
  [[ -z "$database_id" ]] || curl -fsS \
    -X DELETE "$base_url/api/database/$database_id" \
    -H "$auth_header" >/dev/null
done < <(
  curl -fsS "$base_url/api/database" -H "$auth_header" |
    jq -r --arg name "$database_name" '.data[] | select(.name == $name) | .id'
)

curl -fsS -X DELETE "$base_url/api/email" -H "$auth_header" >/dev/null
