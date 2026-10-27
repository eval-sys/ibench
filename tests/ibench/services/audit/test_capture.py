import builtins
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ibench.services.audit import capture


@pytest.mark.parametrize("corrupt", [False, True])
def test_capture_decodes_image_without_pillow(tmp_path: Path, monkeypatch, corrupt: bool) -> None:
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg is required by the recording environment")

    def local(path):
        return tmp_path / str(path).lstrip("/")

    task = local("/logs/artifacts/tasks/sample")
    (task / "runtime").mkdir(parents=True)
    (task / "runtime/candidate-commit-sha.txt").write_text("prepared\n")
    fixture = task / "issues/1/replay"
    frozen = local("/workspace/audit-input/scripts/issues/1")
    evidence = fixture.parent / "evidence"
    for directory in (fixture, frozen, evidence):
        directory.mkdir(parents=True)
    for name in capture.REPLAY_FILES:
        content = '{"entry_path": "/example"}' if name == "presentation.json" else "fixture\n"
        (fixture / name).write_text(content)
        (frozen / name).write_text(content)
    (evidence / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "evidence-replay-driver/v3",
                "task": "sample",
                "commit_id": "prepared",
                "browser_version": "agent-browser test",
                "cases": [
                    {
                        "issue_id": "example",
                        "status": "replay_passed",
                        "capture": {
                            "schema_version": "evidence-replay-capture/v1",
                            "entry_path": "/example",
                            "record_started_at_ms": 1000,
                            "record_stopped_at_ms": 2000,
                            "record_elapsed_ms": 1000,
                            "video_duration_ms": 1000,
                        },
                    }
                ],
            }
        )
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=white:s=16x16:r=1",
            "-t",
            "1",
            "-c:v",
            "libvpx-vp9",
            str(evidence / "after.webm"),
        ],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(evidence / "after.webm"), "-frames:v", "1", str(evidence / "final.png")],
        check=True,
    )
    if corrupt:
        (evidence / "final.png").write_bytes(b"not an image")

    original_output = subprocess.check_output
    original_import = builtins.__import__

    def output(command, **kwargs):
        if command[0] == "git":
            return "prepared\n" if "rev-parse" in command else ""
        return original_output(command, **kwargs)

    def without_pillow(name, *args, **kwargs):
        if name == "PIL" or name.startswith("PIL."):
            raise ModuleNotFoundError("No module named 'PIL'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(capture, "Path", local)
    monkeypatch.setattr(subprocess, "check_output", output)
    monkeypatch.setattr(builtins, "__import__", without_pillow)
    plan = {
        "task_id": "sample",
        "cases": [
            {"case_id": "example", "key": "issues/1", "replay_root": "/logs/artifacts/tasks/sample/issues/1/replay"}
        ],
    }
    if corrupt:
        with pytest.raises(subprocess.CalledProcessError):
            capture.check_capture(plan)
    else:
        capture.check_capture(plan)
