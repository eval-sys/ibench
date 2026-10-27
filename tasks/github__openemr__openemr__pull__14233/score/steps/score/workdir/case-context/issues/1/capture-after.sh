#!/usr/bin/env bash
set -euo pipefail

output=/logs/artifacts/tasks/github__openemr__openemr__pull__14233/issues/1/evidence
replay=/opt/replay/replay.mjs
fixture=/logs/artifacts/tasks/github__openemr__openemr__pull__14233/issues/1/replay
video_name=after.webm
replay_input='{
  "task": "github__openemr__openemr__pull__14233",
  "repository": "openemr/openemr",
  "pull_request_number": 14233,
  "commit_id": "87e84e9bdcc465d61795d1eaebfb843141b89135",
  "default_viewport": "1280x720",
  "issues": [
    {
      "issue_id": "github/openemr/openemr/pull/14233/issue/1",
      "directory": ".",
      "entry_path": null,
      "viewport": "1280x720"
    }
  ]
}
'
workspace=/workspace/app
rm -rf -- "$output"
mkdir -p "$output"
input="$(mktemp -d)"
trap 'rm -rf -- "$input"; chmod -R a+rwX "$output" 2>/dev/null || true' EXIT

for _ in $(seq 1 15); do
  if bash -ec "$DEV_ENV_READY" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if [ "${ready:-0}" != 1 ]; then
  printf '%s\n' '{"status":"environment_failed","summary":"a dependency failed before replay capture"}' \
    > "$output/status.json"
  exit 1
fi

# Adapt the editable fixture bundle to the shared replay input contract.
ln -s "$fixture" "$input/issues"
ln -s "$replay" "$input/replay.mjs"
python3 - "$input" "$fixture" "$replay_input" "$workspace" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

input_root, fixture, replay_input, workspace = sys.argv[1:]
presentation = json.loads((Path(fixture) / "presentation.json").read_text())
config = json.loads(replay_input)
# Capture the prepared candidate's HEAD, not the historical baseline revision.
config["commit_id"] = subprocess.check_output(["git", "-C", workspace, "rev-parse", "HEAD"], text=True).strip()
config["issues"][0]["entry_path"] = presentation.get("entry_path")
(Path(input_root) / "input.json").write_text(json.dumps(config))
PY
node "$(dirname "$replay")/run-replay.mjs" "$input" "$output"
python3 - "$output" "$video_name" <<'PY'
import json
import sys
from pathlib import Path

output = Path(sys.argv[1])
case = json.loads((output / "manifest.json").read_text())["cases"][0]
if case["status"] != "replay_passed":
    raise SystemExit(case["failure_summary"] or case["status"])
(output / "replay.webm").rename(output / sys.argv[2])
PY
