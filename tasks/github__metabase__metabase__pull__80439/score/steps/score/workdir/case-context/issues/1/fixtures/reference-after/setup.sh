#!/usr/bin/env bash
set -euo pipefail

base_url="${APP_URL:?}"
admin_email="${DEV_ENV_ADMIN_EMAIL:?}"
admin_password="${DEV_ENV_ADMIN_PASSWORD:?}"
database_name='LB PR80439 Alert Source'
question_name='PR 80439 Alert Target Check'

properties="$(curl -fsS "$base_url/api/session/properties")"
if [[ "$(jq -r '.["has-user-setup"]' <<<"$properties")" != 'true' ]]; then
  setup_token="$(jq -er '.["setup-token"] | select(type == "string" and length > 0)' <<<"$properties")"
  setup_payload="$(
    jq -cn \
      --arg token "$setup_token" \
      --arg email "$admin_email" \
      --arg password "$admin_password" \
      '{
        token: $token,
        user: {
          first_name: "Lobebench",
          last_name: "Admin",
          email: $email,
          password: $password
        },
        prefs: {
          site_name: "Lobebench Metabase",
          site_locale: "en"
        }
      }'
  )"
  curl -fsS \
    -X POST "$base_url/api/setup" \
    -H 'Content-Type: application/json' \
    --data "$setup_payload" >/dev/null
fi

login_payload="$(
  jq -cn \
    --arg username "$admin_email" \
    --arg password "$admin_password" \
    '{username: $username, password: $password}'
)"
session_id="$(
  curl -fsS \
    -X POST "$base_url/api/session" \
    -H 'Content-Type: application/json' \
    --data "$login_payload" |
    jq -er '.id'
)"
auth_header="X-Metabase-Session: $session_id"

# Recreate the named state so setup is independently idempotent.
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

curl -fsS \
  -X PUT "$base_url/api/setting" \
  -H "$auth_header" \
  -H 'Content-Type: application/json' \
  --data '{
    "email-smtp-host": "mailpit",
    "email-smtp-port": 1025,
    "email-smtp-security": "none",
    "slack-token": null
  }' >/dev/null

database_payload="$(
  jq -cn \
    --arg name "$database_name" \
    '{
      name: $name,
      engine: "sqlite",
      details: {
        db: "/workspace/app/resources/sqlite-fixture.db",
        "read-only?": true
      },
      is_full_sync: false,
      is_on_demand: true
    }'
)"
database_id="$(
  curl -fsS \
    -X POST "$base_url/api/database" \
    -H "$auth_header" \
    -H 'Content-Type: application/json' \
    --data "$database_payload" |
    jq -er '.id'
)"

question_payload="$(
  jq -cn \
    --arg name "$question_name" \
    --argjson database "$database_id" \
    '{
      name: $name,
      description: "Question used to reproduce the empty alert recipient behavior",
      display: "table",
      visualization_settings: {},
      collection_id: null,
      dataset_query: {
        database: $database,
        type: "native",
        native: {
          query: "SELECT 1 AS alert_value",
          "template-tags": {}
        }
      }
    }'
)"
question_id="$(
  curl -fsS \
    -X POST "$base_url/api/card" \
    -H "$auth_header" \
    -H 'Content-Type: application/json' \
    --data "$question_payload" |
    jq -er '.id'
)"

curl -fsS \
  -X POST "$base_url/api/card/$question_id/query" \
  -H "$auth_header" \
  -H 'Content-Type: application/json' \
  --data '{}' |
  jq -e '.status == "completed" and .data.rows == [[1]]' >/dev/null

current_user="$(curl -fsS "$base_url/api/user/current" -H "$auth_header")"
if [[ "$(jq -r '.is_qbnewb' <<<"$current_user")" == 'true' ]]; then
  user_id="$(jq -er '.id' <<<"$current_user")"
  curl -fsS \
    -X PUT "$base_url/api/user/$user_id/modal/qbnewb" \
    -H "$auth_header" >/dev/null
fi
