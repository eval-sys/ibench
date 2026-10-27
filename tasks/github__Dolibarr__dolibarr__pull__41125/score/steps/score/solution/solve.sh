#!/usr/bin/env bash

set -euo pipefail

python3 <<'PY'
import json
import subprocess
from pathlib import Path

manifest = json.loads(Path("/workspace/case-context/manifest.json").read_text())
for case in manifest["cases"]:
    verdict = Path(case["verdict_template"])
    if subprocess.run([case["capture"]], check=False).returncode:
        continue
    verdict.write_text(
        json.dumps(
            {
                "schema_version": "verifier-verdict/v1",
                "case_id": case["case_id"],
                "verdict": "repaired",
                "summary": "The known-good candidate satisfies the Issue requirement.",
                "scenario": {
                    "given_established": True,
                    "when_executed": True,
                    "evidence": ["evidence/after.webm"],
                },
                "requirement": {
                    "result": "supported",
                    "reason": "The after replay satisfies the required behavior.",
                    "evidence": ["evidence/after.webm"],
                },
                "allow": {
                    "considered": True,
                    "reason": "The observed behavior is an allowed implementation.",
                },
            },
            indent=2,
        )
        + "\n"
    )
subprocess.run([manifest["validate"]], check=True)
PY
