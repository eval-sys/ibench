#!/usr/bin/env bash
set -euo pipefail

setup_url=http://localhost:5001/console/api/setup
for attempt in {1..120}; do
  if setup_state="$(curl -fsS --max-time 10 "$setup_url")"; then
    break
  fi
  sleep 1
done

test "${setup_state:-}" != ""
case "$(jq -r '.step' <<< "$setup_state")" in
not_started)
  setup_payload="$(jq -nc \
    --arg email "${DIFY_ADMIN_EMAIL:?}" \
    --arg name "${DIFY_ADMIN_NAME:?}" \
    --arg password "${DIFY_ADMIN_PASSWORD:?}" \
    '{email: $email, name: $name, password: $password, language: "en-US"}')"
  response_file="$(mktemp)"
  status="$(curl -sS --max-time 30 -o "$response_file" -w '%{http_code}' \
    -H 'Content-Type: application/json' -d "$setup_payload" "$setup_url")"
  test "$status" = 201
  jq -e '.result == "success"' "$response_file" > /dev/null
  rm -f "$response_file"
  ;;
finished) ;;
*)
  printf 'unexpected Dify setup state: %s\n' "$setup_state" >&2
  exit 1
  ;;
esac

curl -fsS --max-time 10 "$setup_url" | jq -e '.step == "finished"' > /dev/null
