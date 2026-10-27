from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from ibench.services.preview import create_preview_app
from ibench.services.preview.runs import model_scores, task_runs

CASES = ["github/owner/repo/pull/1/issue/1", "github/owner/repo/pull/1/issue/2"]


def write_run(root: Path, *, phase: str = "completed", kind: str = "run") -> Path:
    directory = root / "runs/model-high"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "run.json").write_text(json.dumps({
        "schema_version": "ibench-run/v2", "kind": kind, "phase": phase, "profile": "intent",
        "release": {"tasks": [{"id": "task", "cases": [{"case_id": case} for case in CASES]}]},
        "solver": {"agents": [{"name": "codex", "model_name": "model", "env": {"SECRET": "private"},
                               "kwargs": {"reasoning_effort": "high"}}]},
    }))
    return directory


def write_results(directory: Path, trials: list[dict], phase: str = "completed") -> None:
    (directory / "results.json").write_text(json.dumps({
        "schema_version": "ibench-results/v2", "kind": "run", "phase": phase, "trials": trials,
    }))


def test_case_verdicts_are_independent_of_task_reward_and_attempts(tmp_path: Path) -> None:
    directory = write_run(tmp_path)
    trial = {"task_id": "task", "status": "scored", "rewards": {"reward": 0}, "verdicts": [
        {"value": {"case_id": CASES[0], "verdict": "repaired", "summary": "Fixed"}},
        {"value": {"case_id": CASES[1], "verdict": "not_repaired", "summary": "Still broken"}},
    ]}
    write_results(directory, [trial, {**trial, "status": "failed", "error": "Score timed out"}])
    result = task_runs(tmp_path, "task", CASES)
    assert [row["status"] for row in result["cases"][CASES[0]]] == ["passed", "error"]
    assert [row["status"] for row in result["cases"][CASES[1]]] == ["failed", "error"]
    assert [row["attempt"] for row in result["cases"][CASES[0]]] == [1, 2]
    assert result["cases"][CASES[0]][0]["summary"] == "Fixed"
    assert "private" not in json.dumps(result)
    assert task_runs(tmp_path, "unrelated", CASES)["cases"] == {case: [] for case in CASES}


def test_discovery_reads_new_changed_removed_and_incomplete_runs(tmp_path: Path) -> None:
    assert not any(task_runs(tmp_path, "task", CASES)["cases"].values())
    directory = write_run(tmp_path, phase="solve")
    assert task_runs(tmp_path, "task", CASES)["cases"][CASES[0]][0]["status"] == "pending"
    write_results(directory, [{"task_id": "task", "status": "scored", "rewards": {"reward": 1}}])
    assert task_runs(tmp_path, "task", CASES)["cases"][CASES[0]][0]["status"] == "unjudged"
    (directory / "results.json").write_text('{"trials":')
    result = task_runs(tmp_path, "task", CASES)
    assert result["warnings"] and not any(result["cases"].values())
    (directory / "results.json").unlink()
    (directory / "run.json").unlink()
    assert not any(task_runs(tmp_path, "task", CASES)["cases"].values())


def test_oracle_runs_and_cases_outside_snapshot_are_excluded(tmp_path: Path) -> None:
    write_run(tmp_path, kind="oracle")
    assert not any(task_runs(tmp_path, "task", CASES)["cases"].values())
    write_run(tmp_path)
    result = task_runs(tmp_path, "task", ["new-case"])
    assert result == {"cases": {"new-case": []}, "warnings": []}


def test_runs_endpoint_discovers_files_after_app_start(tmp_path: Path) -> None:
    (tmp_path / "tasks").symlink_to(Path(__file__).parents[4] / "tasks")
    client = TestClient(create_preview_app(tmp_path))
    task = client.get("/api/release").json()["tasks"][0]
    url = f"/api/tasks/{task['name']}/runs"
    assert client.get(url).json() == {"cases": {case: [] for case in task["case_ids"]}, "warnings": []}
    assert client.get("/api/scores").json() == {"models": [], "warnings": []}
    directory = write_run(tmp_path, phase="solve")
    metadata = json.loads((directory / "run.json").read_text())
    metadata["release"]["tasks"] = [{"id": task["id"], "cases": [{"case_id": task["case_ids"][0]}]}]
    (directory / "run.json").write_text(json.dumps(metadata))
    assert client.get(url).json()["cases"][task["case_ids"][0]][0]["status"] == "pending"
    total = len(client.get("/api/release").json()["tasks"])
    assert client.get("/api/scores").json()["models"] == [{"model": "model", "score": 0, "total": total}]
    write_results(directory, [{"task_id": task["id"], "status": "scored", "rewards": {"reward": 1}, "verdicts": [
        {"value": {"case_id": task["case_ids"][0], "verdict": "repaired"}},
    ]}])
    assert client.get("/api/scores").json()["models"] == [{"model": "model", "score": 1, "total": total}]
    assert client.get("/api/tasks/unknown/runs").status_code == 404


def test_scores_read_task_rewards_without_deriving_them_from_case_verdicts(tmp_path: Path) -> None:
    directory = write_run(tmp_path)
    metadata = json.loads((directory / "run.json").read_text())
    metadata["release"]["tasks"].append({"id": "other-task", "cases": [{"case_id": "third-case"}]})
    (directory / "run.json").write_text(json.dumps(metadata))
    trials = [
        {"task_id": "task", "status": "scored", "rewards": {"reward": 0}, "verdicts": [
            {"value": {"case_id": CASES[0], "verdict": "repaired"}},
            {"value": {"case_id": CASES[1], "verdict": "not_repaired"}},
        ]},
        {"task_id": "other-task", "status": "scored", "rewards": {"reward": 1}},
        {"task_id": "excluded-task", "status": "scored", "rewards": {"reward": 1}},
    ]
    write_results(directory, trials)
    tasks = {"task", "other-task"}
    assert model_scores(tmp_path, tasks)["models"] == [{"model": "model", "score": 1, "total": 2}]
    trials[1]["rewards"]["reward"] = 0
    write_results(directory, trials)
    assert model_scores(tmp_path, tasks)["models"] == [{"model": "model", "score": 0, "total": 2}]
