"""Standalone capture verifier, copied into a Harbor trial (no IBench imports)."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

REPLAY_FILES = (
    "action.mjs",
    "setup.mjs",
    "setup.sh",
    "setup.sql",
    "cleanup.mjs",
    "cleanup.sh",
    "cleanup.sql",
    "presentation.json",
)


def check_capture(plan: dict) -> None:
    output = Path("/logs/artifacts/tasks") / plan["task_id"]
    expected = (output / "runtime/candidate-commit-sha.txt").read_text().strip()
    if subprocess.check_output(["git", "-C", "/workspace/app", "rev-parse", "HEAD"], text=True).strip() != expected:
        raise ValueError("prepared checkout changed during replay")
    if subprocess.check_output(["git", "-C", "/workspace/app", "status", "--porcelain"], text=True).strip():
        raise ValueError("replay changed the candidate source tree")
    for case in plan["cases"]:
        fixture = Path(case["replay_root"])
        frozen = Path("/workspace/audit-input/scripts") / case["key"]
        if any((fixture / name).read_bytes() != (frozen / name).read_bytes() for name in REPLAY_FILES):
            raise ValueError(f"replay scripts changed: {case['case_id']}")
        evidence = fixture.parent / "evidence"
        manifest = json.loads((evidence / "manifest.json").read_bytes())
        if (
            manifest.get("schema_version") != "evidence-replay-driver/v3"
            or manifest.get("task") != plan["task_id"]
            or manifest.get("commit_id") != expected
            or manifest.get("browser_version") in (None, "", "unavailable")
        ):
            raise ValueError("capture provenance mismatch")
        entries = manifest.get("cases", [])
        if len(entries) != 1 or entries[0].get("issue_id") != case["case_id"]:
            raise ValueError("capture case identity mismatch")
        entry = entries[0]
        if entry.get("status") != "replay_passed":
            raise ValueError(entry.get("failure_summary") or entry.get("status") or "missing replay status")
        capture = entry["capture"]
        if capture.get("schema_version") != "evidence-replay-capture/v1":
            raise ValueError("unsupported capture manifest")
        for key in ("record_started_at_ms", "record_stopped_at_ms", "record_elapsed_ms", "video_duration_ms"):
            if not isinstance(capture.get(key), int | float) or not math.isfinite(capture[key]):
                raise ValueError(f"missing capture timing: {key}")
        presentation = json.loads((frozen / "presentation.json").read_bytes())
        if capture.get("entry_path") != presentation["entry_path"]:
            raise ValueError("recorded entry path mismatch")
        if capture["record_stopped_at_ms"] <= capture["record_started_at_ms"] or capture["video_duration_ms"] < 500:
            raise ValueError("capture is too short")
        video = evidence / "after.webm"
        probe = json.loads(
            subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    str(video),
                ],
                text=True,
            )
        )
        duration = float(probe["format"]["duration"])
        if not math.isfinite(duration) or duration < 0.5:
            raise ValueError("video is unreadable or shorter than 500ms")
        subprocess.check_output(
            [
                "ffmpeg",
                "-v",
                "error",
                "-xerror",
                "-i",
                str(evidence / "final.png"),
                "-frames:v",
                "1",
                "-f",
                "null",
                "-",
            ],
            stderr=subprocess.STDOUT,
        )


if __name__ == "__main__":
    try:
        check_capture(json.loads(Path(sys.argv[1]).read_bytes()))
    except Exception as error:
        print(f"Capture verification failed: {error}", file=sys.stderr)
        Path("/logs/verifier/reward.json").write_text('{"capture": 0}\n')
        raise SystemExit(1) from error
    Path("/logs/verifier/reward.json").write_text('{"capture": 1}\n')
    print("Capture verified; Require has not been judged.")
