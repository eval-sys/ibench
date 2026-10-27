#!/usr/bin/env bash

set -euo pipefail

workspace=/workspace/app
base_commit_sha=4843875f26f48343b08814e3282b3c4565a78c58
patch=/logs/verifier/candidate.patch
artifact=/tmp/candidate.patch
reward=/logs/verifier/reward.json
prepared=/logs/artifacts/solver/runtime/prepared-commit-sha.txt

# The patch is the solver Trial's formal artifact. Generate it in the trusted
# verifier rather than asking the solver agent to report its own work.
mkdir -p "$(dirname "$patch")" "$(dirname "$reward")"
if [[ -n "$artifact" ]]; then
  cp "$artifact" "$patch"
else
  # Select only paths committed by the solver, then diff them against the upstream
  # base so the patch still applies before scoring preparation/install.
  python3 - "$workspace" "$base_commit_sha" "$prepared" "$patch" <<'PYTHON'
import os
import subprocess
import sys
from pathlib import Path

workspace, base, prepared_file, patch_file = sys.argv[1:]
prepared = Path(prepared_file).read_text().strip()
command = ["git", "--literal-pathspecs", "-C", workspace]
changed = subprocess.check_output([*command, "diff", "--name-only", "--no-renames", "-z", prepared, "HEAD", "--"])
paths = [os.fsdecode(path) for path in changed.split(b"\0") if path]
with Path(patch_file).open("wb") as output:
    if paths:
        subprocess.run([*command, "diff", "--binary", base, "HEAD", "--", *paths], stdout=output, check=True)
PYTHON
fi
printf '%s\n' '{"reward":1}' > "$reward"
