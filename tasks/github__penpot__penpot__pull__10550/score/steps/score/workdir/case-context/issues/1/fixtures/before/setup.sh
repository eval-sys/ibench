#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$script_dir/cleanup.sh"

fixture_tmp_dir="$(mktemp -d)"
cleanup_tmp_dir() {
  rm -r -- "$fixture_tmp_dir"
}
trap cleanup_tmp_dir EXIT

cookie_file="$fixture_tmp_dir/cookies.txt"
prepare_response="$fixture_tmp_dir/prepare-register.json"
curl --fail-with-body --silent --show-error \
  --header 'Content-Type: application/transit+json' \
  --header 'Accept: application/transit+json' \
  --data '{"~:fullname":"Path Designer","~:email":"path.badge@example.com","~:password":"PathBadge10550!"}' \
  http://localhost:3000/api/main/methods/prepare-register-profile \
  --output "$prepare_response"

registration_token="$(jq -er '
  (. as $response
    | first(range(0; length) | select($response[.] == "~:token"))) as $index
  | .[$index + 1]
  | select(type == "string" and length > 0)
' "$prepare_response")"

jq -n --arg token "$registration_token" '{"~:token": $token}' \
  > "$fixture_tmp_dir/register-profile.json"

curl --fail-with-body --silent --show-error \
  --cookie-jar "$cookie_file" \
  --header 'Content-Type: application/transit+json' \
  --header 'Accept: application/transit+json' \
  --data-binary "@$fixture_tmp_dir/register-profile.json" \
  http://localhost:3000/api/main/methods/register-profile \
  --output "$fixture_tmp_dir/registered-profile.json"

login_response="$fixture_tmp_dir/login.json"
curl --fail-with-body --silent --show-error \
  --cookie "$cookie_file" \
  --cookie-jar "$cookie_file" \
  --header 'Content-Type: application/transit+json' \
  --header 'Accept: application/transit+json' \
  --data '{"~:email":"path.badge@example.com","~:password":"PathBadge10550!"}' \
  http://localhost:3000/api/main/methods/login-with-password \
  --output "$login_response"

project_id="$(jq -er '
  (. as $response
    | first(range(0; length) | select($response[.] == "~:default-project-id"))) as $index
  | .[$index + 1]
  | sub("^~u"; "")
' "$login_response")"

curl --fail-with-body --silent --show-error \
  --cookie "$cookie_file" \
  --header 'Content-Type: application/transit+json' \
  --header 'Accept: application/transit+json' \
  --data '{"~:props":{"~:onboarding-viewed":true,"~:workspace-visited":true}}' \
  http://localhost:3000/api/main/methods/update-profile-props \
  --output "$fixture_tmp_dir/profile-props.json"

jq -n --arg project_id "$project_id" '{
  "~:project-id": ("~u" + $project_id),
  "~:name": "Path Badge Canvas",
  "~:features": {
    "~#set": [
      "fdata/path-data",
      "design-tokens/v1",
      "variants/v1",
      "layout/grid",
      "fdata/objects-map",
      "components/v2",
      "fdata/shape-data-type"
    ]
  }
}' > "$fixture_tmp_dir/create-file.json"

curl --fail-with-body --silent --show-error \
  --cookie "$cookie_file" \
  --header 'Content-Type: application/transit+json' \
  --header 'Accept: application/transit+json' \
  --data-binary "@$fixture_tmp_dir/create-file.json" \
  http://localhost:3000/api/main/methods/create-file \
  --output "$fixture_tmp_dir/created-file.json"

jq -e '
  index("~:name") as $index
  | $index != null and .[$index + 1] == "Path Badge Canvas"
' "$fixture_tmp_dir/created-file.json" > /dev/null
