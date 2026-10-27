#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "${script_dir}/cleanup.sh"

tmp_dir="$(mktemp -d)"
trap 'rm -rf -- "${tmp_dir:?}"' EXIT
cookie_jar="${tmp_dir}/cookies.txt"

prepare_response="$(
  curl --fail-with-body --silent --show-error \
    --header 'Content-Type: application/json' \
    --header 'Accept: application/json' \
    --data '{"fullname":"Layer Navigation User","email":"layer-navigation-case@example.com","password":"LayerNavigation123!"}' \
    http://localhost:3000/api/main/methods/prepare-register-profile
)"
registration_token="$(jq -er '.token' <<<"${prepare_response}")"
register_payload="$(jq -nc --arg token "${registration_token}" '{token: $token}')"

register_response="$(
  curl --fail-with-body --silent --show-error \
    --cookie-jar "${cookie_jar}" \
    --header 'Content-Type: application/json' \
    --header 'Accept: application/json' \
    --data "${register_payload}" \
    http://localhost:3000/api/main/methods/register-profile
)"
jq -e '.email == "layer-navigation-case@example.com"' <<<"${register_response}" >/dev/null

curl --fail-with-body --silent --show-error \
  --cookie "${cookie_jar}" \
  --header 'Content-Type: application/json' \
  --header 'Accept: application/json' \
  --data '{"props":{"onboardingViewed":true,"onboardingQuestionsAnswered":true,"v2InfoShown":true,"workspaceVisited":true,"releaseNotesViewed":"999.999"}}' \
  http://localhost:3000/api/main/methods/update-profile-props \
  >"${tmp_dir}/profile-props.json"

team_response="$(
  curl --fail-with-body --silent --show-error \
    --cookie "${cookie_jar}" \
    --header 'Content-Type: application/json' \
    --header 'Accept: application/json' \
    --data '{"id":"8a114270-0000-4000-8000-000000000010","name":"Layer Navigation"}' \
    http://localhost:3000/api/main/methods/create-team
)"
project_id="$(jq -er '.defaultProjectId' <<<"${team_response}")"
[[ "${project_id}" =~ ^[0-9a-f-]{36}$ ]]

file_payload="$(
  jq -nc --arg project_id "${project_id}" '[
    "^ ",
    "~:id", "~u8a114270-0000-4000-8000-000000000001",
    "~:page-id", "~u8a114270-0000-4000-8000-000000000002",
    "~:name", "Layer Navigation Study",
    "~:project-id", ("~u" + $project_id)
  ]'
)"
curl --fail-with-body --silent --show-error \
  --cookie "${cookie_jar}" \
  --header 'Content-Type: application/transit+json' \
  --header 'Accept: application/json' \
  --data "${file_payload}" \
  http://localhost:3000/api/main/methods/create-file \
  >"${tmp_dir}/create-file.json"
jq -e '
  .id == "8a114270-0000-4000-8000-000000000001" and
  .data.pages[0] == "8a114270-0000-4000-8000-000000000002"
' "${tmp_dir}/create-file.json" >/dev/null

node >"${tmp_dir}/update-file.json" <<'NODE'
const zero = '00000000-0000-0000-0000-000000000000';
const pageId = '8a114270-0000-4000-8000-000000000002';
const matrix = { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };

const changes = Array.from({ length: 40 }, (_, index) => {
  const number = index + 1;
  const suffix = String(number).padStart(12, '0');
  const id = `8a114270-1000-4000-8000-${suffix}`;
  const x = number === 1 ? 120 : 2200 + ((number - 2) % 5) * 180;
  const y = number === 1 ? 120 : 1600 + Math.floor((number - 2) / 5) * 150;
  const width = 120;
  const height = 90;

  return {
    type: 'add-obj',
    id,
    pageId,
    parentId: zero,
    frameId: zero,
    obj: {
      id,
      name: `Waypoint ${String(number).padStart(2, '0')}`,
      type: 'rect',
      x,
      y,
      width,
      height,
      selrect: { x, y, width, height, x1: x, y1: y, x2: x + width, y2: y + height },
      points: [
        { x, y },
        { x: x + width, y },
        { x: x + width, y: y + height },
        { x, y: y + height },
      ],
      transform: matrix,
      transformInverse: matrix,
      parentId: zero,
      frameId: zero,
      fills: [{ fillColor: number % 2 ? '#5B8DEF' : '#E06C75', fillOpacity: 1 }],
      strokes: [],
    },
  };
});

process.stdout.write(JSON.stringify({
  id: '8a114270-0000-4000-8000-000000000001',
  sessionId: '8a114270-0000-4000-8000-000000000003',
  revn: 0,
  vern: 0,
  changes,
}));
NODE

curl --fail-with-body --silent --show-error \
  --cookie "${cookie_jar}" \
  --header 'Content-Type: application/json' \
  --header 'Accept: application/json' \
  --data-binary "@${tmp_dir}/update-file.json" \
  'http://localhost:3000/api/main/methods/update-file?id=8a114270-0000-4000-8000-000000000001' \
  >"${tmp_dir}/update-response.json"
jq -e '.lagged[0].revn == 1 and (.lagged[0].changes | length) == 40' \
  "${tmp_dir}/update-response.json" >/dev/null
