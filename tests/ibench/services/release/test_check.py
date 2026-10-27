from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ibench.cli import app
from ibench.services.release.check import check_release
from ibench.services.release.compiler import load_release, snapshot_release
from ibench.services.runner.oracle import prepare_oracle_task

RELEASE_ROOT = Path(__file__).parents[4]


def test_check_accepts_the_release() -> None:
    result = CliRunner().invoke(app, ["check", str(RELEASE_ROOT)])

    assert result.exit_code == 0, result.output


def test_check_rejects_a_task_directory_missing_from_the_manifest(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    manifest = json.loads((RELEASE_ROOT / "tasks/release.json").read_text(encoding="utf-8"))
    (tasks / "release.json").write_text(json.dumps(manifest), encoding="utf-8")
    for task in manifest["tasks"]:
        (tasks / task["id"]).symlink_to(RELEASE_ROOT / "tasks" / task["id"], target_is_directory=True)
    (tasks / "unpublished-task").mkdir()

    result = CliRunner().invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 1


@pytest.mark.parametrize("binding", ["candidate", "candidate.patch"])
def test_check_rejects_runtime_binding_in_published_task(tmp_path: Path, binding: str) -> None:
    shutil.copytree(RELEASE_ROOT / "tasks", tmp_path / "tasks")
    manifest = json.loads((tmp_path / "tasks/release.json").read_text(encoding="utf-8"))
    task_id = manifest["tasks"][0]["id"]
    workdir = tmp_path / "tasks" / task_id / "score/steps/score/workdir"
    (workdir / binding).write_text("runtime input", encoding="utf-8")

    result = CliRunner().invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 1


def test_check_rejects_a_case_without_its_rubric(tmp_path: Path) -> None:
    shutil.copytree(RELEASE_ROOT / "tasks", tmp_path / "tasks")
    rubric = next((tmp_path / "tasks").glob("*/score/steps/score/workdir/case-context/issues/*/rubric.json"))
    rubric.unlink()

    result = CliRunner().invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 1


def test_oracle_binds_score_task_to_merge_commit(tmp_path: Path) -> None:
    manifest = json.loads((RELEASE_ROOT / "tasks/release.json").read_text(encoding="utf-8"))
    released_task = next(
        task for task in manifest["tasks"]
        if not (RELEASE_ROOT / "tasks" / task["id"] / "reference.patch").exists()
    )
    destination = tmp_path / "score"

    task = prepare_oracle_task(RELEASE_ROOT, released_task["id"], destination)

    assert task.merge_commit_sha == released_task["merge_commit_sha"]
    assert (destination / "steps/score/workdir/candidate").read_text(encoding="utf-8") == (
        f"{released_task['merge_commit_sha']}\n"
    )
    assert not (destination / "steps/score/workdir/candidate.patch").exists()


def test_oracle_rejects_harbor_oracle_agent() -> None:
    manifest = json.loads((RELEASE_ROOT / "tasks/release.json").read_text(encoding="utf-8"))

    result = CliRunner().invoke(
        app,
        ["oracle", manifest["tasks"][0]["id"], "--agent", "oracle", "--path", str(RELEASE_ROOT)],
    )

    assert result.exit_code == 1


@pytest.mark.parametrize("metadata", ["valid", "wrong_case", "duplicate"])
def test_release_case_metadata_is_checked_and_preserved(tmp_path: Path, metadata: str) -> None:
    manifest = json.loads((RELEASE_ROOT / "tasks/release.json").read_bytes())
    task = manifest["tasks"][0]
    manifest["tasks"] = [task]
    source = RELEASE_ROOT / "tasks" / task["id"]
    score = json.loads((source / "score/steps/score/workdir/case-context/manifest.json").read_bytes())
    task["cases"] = [
        {"case_id": case["case_id"], "selection": "candidate", "requires_video_rerecording": True}
        for case in score["cases"]
    ]
    if metadata == "wrong_case":
        task["cases"][0]["case_id"] = "unpublished-case"
    elif metadata == "duplicate":
        task["cases"].append(task["cases"][0].copy())
    tasks = tmp_path / "source/tasks"
    tasks.mkdir(parents=True)
    (tasks / task["id"]).symlink_to(source, target_is_directory=True)
    (tasks / "release.json").write_text(json.dumps(manifest))

    checked = check_release(tasks.parent)
    if metadata != "valid":
        assert checked.issues
        return
    assert checked.issues == ()
    snapshot = tmp_path / "snapshot"
    snapshot_release(tasks.parent, checked.release, snapshot)
    restored = load_release(snapshot)
    assert [case.model_dump() for case in restored.tasks[0].cases] == task["cases"]
