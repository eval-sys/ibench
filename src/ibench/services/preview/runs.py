"""Read portable run summaries without traversing jobs or exposing agent configuration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def task_runs(root: Path, task_id: str, case_ids: list[str]) -> dict[str, Any]:
    cases: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in case_ids}
    warnings = []
    for directory in sorted((root / "runs").glob("*")):
        if not directory.is_dir() or not (directory / "run.json").is_file():
            continue
        try:
            run = _read(directory / "run.json")
            if run.get("schema_version") != "ibench-run/v2" or run.get("kind") != "run":
                continue
            agents = (run.get("solver") or {}).get("agents", [])
            result_path = directory / "results.json"
            result = _read(result_path) if result_path.exists() else {}
            if result and (result.get("schema_version") != "ibench-results/v2" or result.get("kind") != "run"):
                raise ValueError("unsupported results format")
            frozen_task = next((task for task in run["release"]["tasks"] if task["id"] == task_id), None)
            if frozen_task is None:
                continue
            selected = {case["case_id"] for case in frozen_task["cases"]} & cases.keys()
            trials = [trial for trial in result.get("trials", []) if trial["task_id"] == frozen_task["id"]]
            for attempt, trial in enumerate(trials or [{}], 1):
                agent = agents[0] if len(agents) == 1 else {}
                # Multiple-agent jobs identify the actual solver on the trial.
                if len(agents) > 1 and trial.get("solver_trial"):
                    config = (directory / trial["solver_trial"] / "config.json").resolve()
                    if config.is_relative_to(directory.resolve()):
                        agent = _read(config).get("agent", {})
                verdicts = {entry["value"]["case_id"]: entry["value"] for entry in trial.get("verdicts", [])}
                phase = result.get("phase", run.get("phase"))
                error = trial.get("error")
                if trial.get("status") != "scored":
                    error = error or result.get("error") or run.get("error")
                for case_id in selected:
                    verdict = verdicts.get(case_id, {})
                    if error or trial.get("status") == "failed":
                        status = "error"
                    elif trial.get("status") == "scored":
                        status = {"repaired": "passed", "not_repaired": "failed"}.get(
                            verdict.get("verdict"), "unjudged",
                        )
                    else:
                        status = "unjudged" if phase == "completed" else "pending"
                    cases[case_id].append({
                        "run": directory.name,
                        "model": agent.get("model_name") or "Unknown model",
                        "agent": agent.get("name") or agent.get("import_path") or "Unknown agent",
                        "effort": agent.get("kwargs", {}).get("reasoning_effort"),
                        "profile": run.get("profile"),
                        "attempt": attempt,
                        "status": status,
                        "phase": phase,
                        "verdict": verdict.get("verdict"),
                        "summary": verdict.get("summary") or "",
                        "error": str(error) if error else "",
                        "solver_error": trial.get("solver_error") or "",
                    })
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            # Atomic writes are usual; tolerate partial copies and malformed runs too.
            warnings.append(f"{directory.name}: run data is unreadable or incomplete; retrying on next refresh.")
    return {"cases": cases, "warnings": warnings}


def model_scores(root: Path, task_ids: set[str]) -> dict[str, Any]:
    models, warnings = [], []
    for path in sorted((root / "runs").glob("*/run.json")):
        try:
            run = _read(path)
            if run.get("schema_version") != "ibench-run/v2" or run.get("kind") != "run":
                continue
            result_path = path.with_name("results.json")
            result = _read(result_path) if result_path.exists() else {}
            if result and (result.get("schema_version") != "ibench-results/v2" or result.get("kind") != "run"):
                raise ValueError("unsupported results format")
            if not any(task["id"] in task_ids for task in run["release"]["tasks"]):
                continue
            models.append({
                "model": run["solver"]["agents"][0].get("model_name") or "Unknown model",
                "score": sum((trial.get("rewards") or {}).get("reward", 0)
                             for trial in result.get("trials", []) if trial["task_id"] in task_ids),
                "total": len(task_ids),
            })
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            warnings.append(f"{path.parent.name}: run data is unreadable or incomplete; retrying on next refresh.")
    return {"models": models, "warnings": warnings}
