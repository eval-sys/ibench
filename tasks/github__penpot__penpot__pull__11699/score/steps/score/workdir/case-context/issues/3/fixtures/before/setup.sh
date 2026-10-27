#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$script_dir/cleanup.sh"

fixture_tmp_dir="$(mktemp -d)"
trap 'rm -rf -- "$fixture_tmp_dir"' EXIT

api_base="${APP_URL:-http://localhost:3000}/api/main/methods"
prepare_response="$fixture_tmp_dir/prepare.json"
curl --fail-with-body --silent --show-error \
  --request POST "$api_base/prepare-register-profile" \
  --header 'content-type: application/json' \
  --header 'accept: application/transit+json' \
  --data '{"email":"history.editor.11699@example.com","password":"WorkspacePass123!","fullname":"Workspace Editor"}' \
  --output "$prepare_response"

registration_token="$(jq -er '. as $a | ([range(0; length) | select($a[.] == "~:token")][0]) as $i | $a[$i + 1]' "$prepare_response")"
register_body="$(jq -nc --arg token "$registration_token" '{token: $token}')"
register_response="$fixture_tmp_dir/register.json"
cookie_jar="$fixture_tmp_dir/cookies.txt"
curl --fail-with-body --silent --show-error \
  --request POST "$api_base/register-profile" \
  --header 'content-type: application/json' \
  --header 'accept: application/transit+json' \
  --cookie-jar "$cookie_jar" \
  --data "$register_body" \
  --output "$register_response"

project_id="$(jq -er '. as $a | ([range(0; length) | select($a[.] == "~:default-project-id")][0]) as $i | $a[$i + 1] | sub("^~u"; "")' "$register_response")"

curl --fail-with-body --silent --show-error \
  --request POST "$api_base/update-profile-props" \
  --header 'content-type: application/transit+json' \
  --header 'accept: application/transit+json' \
  --cookie "$cookie_jar" \
  --data '["^ ","~:props",["^ ","~:onboarding-viewed",true,"~:onboarding-questions-answered",true,"~:workspace-visited",true,"~:renderer","~:svg"]]' \
  --output /dev/null

file_body="$(jq -nc --arg project_id "$project_id" --arg name 'Version Preview Study' '{"project-id": $project_id, name: $name}')"
file_response="$fixture_tmp_dir/file.json"
curl --fail-with-body --silent --show-error \
  --request POST "$api_base/create-file" \
  --header 'content-type: application/json' \
  --header 'accept: application/transit+json' \
  --cookie "$cookie_jar" \
  --data "$file_body" \
  --output "$file_response"

file_id="$(jq -er '. as $a | ([range(0; length) | select($a[.] == "~:id")][0]) as $i | $a[$i + 1] | sub("^~u"; "")' "$file_response")"
snapshot_body="$(jq -nc --arg file_id "$file_id" --arg label 'Before current edit' '{"file-id": $file_id, label: $label}')"
curl --fail-with-body --silent --show-error \
  --request POST "$api_base/create-file-snapshot" \
  --header 'content-type: application/json' \
  --header 'accept: application/transit+json' \
  --cookie "$cookie_jar" \
  --data "$snapshot_body" \
  --output /dev/null
