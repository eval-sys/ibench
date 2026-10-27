#!/usr/bin/env bash
set -euo pipefail

fixture_tmp_dir="$(mktemp -d)"
trap 'rm -rf -- "$fixture_tmp_dir"' EXIT

api_base="${APP_URL:-http://localhost:3000}/api/main/methods"
cookie_jar="$fixture_tmp_dir/cookies.txt"
login_response="$fixture_tmp_dir/login.json"
http_status="$(curl --silent --show-error \
  --request POST "$api_base/login-with-password" \
  --header 'content-type: application/json' \
  --header 'accept: application/transit+json' \
  --cookie-jar "$cookie_jar" \
  --data '{"email":"inspect.editor.11699@example.com","password":"WorkspacePass123!"}' \
  --output "$login_response" \
  --write-out '%{http_code}')"

case "$http_status" in
  200)
    curl --fail-with-body --silent --show-error \
      --request POST "$api_base/delete-profile" \
      --header 'content-type: application/json' \
      --header 'accept: application/transit+json' \
      --cookie "$cookie_jar" \
      --data '{}' \
      --output /dev/null
    ;;
  400|401)
    ;;
  *)
    printf 'Unexpected login status during cleanup: %s\n' "$http_status" >&2
    exit 1
    ;;
esac
