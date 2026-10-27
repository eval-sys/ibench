from __future__ import annotations

import asyncio
import fcntl
import json
import shutil
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from harbor.models.job.config import JobConfig
from harbor.models.job.result import JobResult
from harbor.models.trial.config import TaskConfig as JobTaskConfig
from pydantic import Field

from ibench.models import Model, ReleaseManifest
from ibench.modules.harbor import require_finished, run_job, trial_error, trial_rewards, trials
from ibench.modules.run_paths import map_paths, relative_path, write_json
from ibench.services.release.compiler import (
    bind_candidate,
    compile_task,
    load_release,
    prepare_reference,
    prepare_solve,
)


class ScoreInput(Model):
    task_id: str
    score_task: Path
    solver_trial: Path | None = None
    solver_error: str | None = None
    candidate_patch: Path | None = None
    candidate_commit: str | None = None


class SkippedSolve(Model):
    task_id: str
    solver_trial: Path
    status: Literal["failed"] = "failed"
    error: str


class RunState(Model):
    schema_version: Literal["ibench-run/v2"] = "ibench-run/v2"
    kind: Literal["run", "oracle"]
    phase: Literal["solve", "bind", "pending", "score-reset", "score", "completed"]
    release: ReleaseManifest
    profile: str
    solver: JobConfig | None = None
    scorer: JobConfig
    solver_job: Path | None = None
    score_tasks: dict[str, list[Path]] = Field(default_factory=dict)
    inputs: list[ScoreInput] = Field(default_factory=list)
    skipped: list[SkippedSolve] = Field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class RunResult:
    output: Path
    phase: str
    success: bool
    trials: list[dict]


def _write_json(path: Path, value: dict) -> None:
    write_json(path, map_paths(value, lambda p: relative_path(p, path.parent)))


def _save(output: Path, state: RunState) -> None:
    portable = map_paths(state, lambda p: relative_path(p, output))
    write_json(output / "run.json", portable.model_dump(mode="json"))


def read_run(output: Path) -> RunState:
    output = output.resolve()
    path = output / "run.json"
    if not path.is_file():
        raise ValueError(f"not an IBench run directory: {output}")
    raw = json.loads(path.read_bytes())
    if raw.get("schema_version") != "ibench-run/v2":
        raise ValueError("legacy run layout requires migration to ibench-run/v2")
    state = RunState.model_validate(raw)
    return map_paths(state, lambda p: p if p.is_absolute() else output / p)


def _configure(config: JobConfig, output: Path, phase: str, paths: list[Path]) -> JobConfig:
    bound = config.model_copy(deep=True)
    bound.job_name = phase
    bound.jobs_dir = output / "jobs"
    bound.tasks = [JobTaskConfig(path=path) for path in paths]
    bound.datasets = []
    bound.source_jobs = []
    # Harbor collects /logs/artifacts by convention, including nested task evidence.
    if phase == "score":
        if bound.agents[0].name == "oracle":
            raise ValueError("Harbor's oracle agent bypasses the real score agent")
        bound.n_attempts = 1
    return bound


def _initialize(output: Path, root: Path) -> None:
    if output.is_relative_to((root / "tasks").resolve()):
        raise ValueError("runtime output must not be written below the published tasks directory")
    if output.exists():
        raise ValueError(f"run output already exists; use ibench resume or choose a new output: {output}")
    output.mkdir(parents=True)


def _bind_solver_trials(output: Path, state: RunState, *, replace: bool = False) -> None:
    assert state.solver_job is not None
    result = JobResult.model_validate_json((state.solver_job / "result.json").read_bytes())
    require_finished(result)
    records = trials(state.solver_job)
    if len(records) != result.n_total_trials:
        raise ValueError("solver job is missing trial results; refusing partial scoring")
    expected = {(output / "compiled/solve" / task.id).resolve(): task for task in state.release.tasks}
    inputs, skipped = [], []
    attempts: dict[str, int] = defaultdict(int)
    for directory, trial in records:
        task_path = trial.config.task.path
        task = expected.get(task_path.resolve()) if task_path is not None else None
        if task is None or trial.task_name != f"ibench/{task.name}":
            raise ValueError(f"solver trial does not belong to this run: {directory}")
        if not trial.finished_at:
            raise ValueError(f"solver trial is unfinished: {directory}")
        index = attempts[task.id]
        attempts[task.id] += 1
        destinations = state.score_tasks[task.id]
        if index >= len(destinations):
            raise ValueError(f"solver attempts exceed frozen score inputs: {task.id}")
        destination = destinations[index]
        patch = directory / "steps/solve/artifacts/candidate.patch"
        error = trial_error(trial)
        candidate = patch.read_bytes() if patch.is_file() else None
        collected = trial_rewards(trial, "solve").get("reward") == 1
        allow_empty = trial.config.agent.name == "nop" and trial.config.agent.import_path is None
        if candidate is None or not collected or (not candidate and not allow_empty):
            skipped.append(SkippedSolve(
                task_id=task.id,
                solver_trial=directory,
                error=error or ("trusted candidate.patch is missing" if candidate is None
                               else "patch collection failed" if not collected
                               else "solver produced an empty patch"),
            ))
            continue
        commit = task.base_commit_sha if not candidate else None
        bind_candidate(
            destination,
            patch=candidate if candidate else None,
            commit=commit,
            replace=replace,
        )
        inputs.append(
            ScoreInput(
                task_id=task.id,
                solver_trial=directory,
                solver_error=error,
                score_task=destination,
                candidate_patch=patch,
                candidate_commit=commit,
            )
        )
    state.inputs, state.skipped = inputs, skipped
    state.scorer = _configure(state.scorer, output, "score", [item.score_task for item in inputs])


def _collect(output: Path, state: RunState) -> RunResult:
    job_path = output / "jobs/score"
    scored = {}
    expected = {item.score_task.resolve() for item in state.inputs}
    for directory, trial in ([] if state.phase == "score-reset" else trials(job_path)):
        task_path = trial.config.task.path
        key = task_path.resolve() if task_path else None
        if key in scored or key not in expected:
            raise ValueError(f"unexpected or duplicate score trial: {directory}")
        scored[key] = (directory, trial)
    results = []
    for item in state.inputs:
        entry = item.model_dump(mode="python")
        entry.update(status="pending" if state.phase == "pending" else "missing", rewards={})
        if match := scored.get(item.score_task.resolve()):
            directory, trial = match
            rewards, error = trial_rewards(trial, "score"), trial_error(trial)
            error = error or (
                "score trial is unfinished"
                if not trial.finished_at
                else "score reward is missing"
                if not rewards
                else None
            )
            verdicts = [
                {"path": path, "value": json.loads(path.read_bytes())}
                for path in sorted(directory.rglob("verdict.json"))
                if "artifacts" in path.relative_to(directory).parts
            ]
            entry.update(
                status="scored" if trial.finished_at and rewards and not error else "failed",
                score_trial=directory,
                rewards=rewards,
                error=error,
                verdicts=verdicts,
                artifacts=[
                    path for path in sorted(directory.rglob("*")) if path.is_file() and "artifacts" in path.parts
                ],
            )
        results.append(entry)
    results.extend(item.model_dump(mode="python") for item in state.skipped)
    success = (
        bool(state.inputs)
        and state.phase in ("pending", "completed")
        and state.error is None
        and all(entry["status"] in ("scored", "pending") for entry in results)
    )
    if state.kind == "oracle":
        success = success and all(entry["rewards"].get("reward") == 1 for entry in results)
    _write_json(
        output / "results.json",
        {
            "schema_version": "ibench-results/v2",
            "kind": state.kind,
            "phase": state.phase,
            "profile": state.profile,
            "solver_job": state.solver_job,
            "score_job": job_path if state.phase not in ("pending", "score-reset") else None,
            "success": success,
            "error": state.error,
            "trials": results,
        },
    )
    records = json.loads(json.dumps(results, default=str))
    return RunResult(output=output, phase=state.phase, success=success, trials=records)


async def _drive(output: Path, state: RunState, solver_only: bool) -> RunResult:
    if state.phase == "solve":
        assert state.solver is not None
        require_finished(await run_job(state.solver))
        state.phase = "bind"
        _save(output, state)
    if state.phase in ("bind", "score-reset"):
        replacing = state.phase == "score-reset"
        if replacing:
            if (output / "jobs/score").exists():
                shutil.rmtree(output / "jobs/score")
            _collect(output, state)
        _bind_solver_trials(output, state, replace=replacing)
        state.phase = "pending"
        _save(output, state)
    if state.phase == "pending":
        result = _collect(output, state)
        if not state.inputs:
            raise ValueError(f"no trusted candidate patches; inspect {output / 'results.json'}")
        if solver_only:
            return result
        state.phase = "score"
        _save(output, state)
    if state.phase == "score":
        require_finished(await run_job(state.scorer))
        state.phase = "completed"
        _save(output, state)
    return _collect(output, state)


def _execute(
    output: Path, *, solver_only: bool = False, prepare: Callable[[RunState], None] | None = None,
) -> RunResult:
    with (output / ".run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError(f"this run is already active: {output}") from error
        state = read_run(output)
        if prepare is not None:
            prepare(state)
        state.error = None
        _save(output, state)
        try:
            return asyncio.run(_drive(output, state, solver_only))
        except BaseException as error:
            state.error = f"{type(error).__name__}: {error}"
            _save(output, state)
            try:
                _collect(output, state)
            except (ValueError, OSError):
                # Preserve the original error if incomplete artifacts cannot be indexed.
                pass
            raise


def run_release(
    root: Path,
    output: Path,
    *,
    solver: JobConfig,
    scorer: JobConfig,
    selections: tuple[str, ...] | None = None,
    profile: str | None = None,
    solver_only: bool = False,
) -> RunResult:
    root, output = root.resolve(), output.resolve()
    manifest = load_release(root, selections)
    profile = profile or manifest.default_instruction_profile
    if profile not in manifest.instruction_profiles:
        raise ValueError(f"instruction profile is not declared by the release: {profile}")
    solver = _configure(
        solver,
        output,
        "solve",
        [output / "compiled/solve" / task.id for task in manifest.tasks],
    )
    scorer = _configure(scorer, output, "score", [])
    _initialize(output, root)
    score_tasks = {}
    for task in manifest.tasks:
        prepare_solve(root, task, output / "compiled/solve" / task.id, profile)
        score_tasks[task.id] = [
            compile_task(
                root / "tasks" / task.id / "score",
                output / "compiled/score" / f"{task.id}--{attempt}",
                name=f"ibench/{task.name}-score-{attempt}",
                unbound=True,
            )
            for attempt in range(1, solver.n_attempts + 1)
        ]
    state = RunState(
        kind="run",
        phase="solve",
        release=manifest,
        profile=profile,
        solver=solver,
        scorer=scorer,
        solver_job=output / "jobs/solve",
        score_tasks=score_tasks,
    )
    _save(output, state)
    return _execute(output, solver_only=solver_only)


def score_run(output: Path, *, scorer: JobConfig | None = None, overwrite: bool = False) -> RunResult:
    output = output.resolve()

    def prepare(state: RunState) -> None:
        if state.kind != "run" or state.solver_job != output / "jobs/solve":
            raise ValueError("score requires a complete IBench run with its own jobs/solve")
        require_finished(JobResult.model_validate_json((state.solver_job / "result.json").read_bytes()))
        if (output / "jobs/score").exists() and not overwrite:
            raise ValueError("score job already exists; use resume or score --overwrite")
        state.scorer = _configure(scorer or state.scorer, output, "score", [])
        state.phase = "score-reset" if overwrite else "bind"

    return _execute(output, prepare=prepare)


def run_calibration(root: Path, task_id: str, output: Path, *, scorer: JobConfig) -> RunResult:
    root, output = root.resolve(), output.resolve()
    manifest = load_release(root, (task_id,))
    task = manifest.tasks[0]
    scorer = _configure(scorer, output, "score", [output / "compiled/score" / task.id])
    _initialize(output, root)
    destination = output / "compiled/score" / task.id
    prepare_reference(root, task, destination)
    patch = destination / "steps/score/workdir/candidate.patch"
    state = RunState(
        kind="oracle",
        phase="score",
        release=manifest,
        profile=manifest.default_instruction_profile,
        scorer=scorer,
        inputs=[ScoreInput(
            task_id=task.id, score_task=destination,
            candidate_patch=patch if patch.exists() else None,
            candidate_commit=None if patch.exists() else task.merge_commit_sha,
        )],
    )
    _save(output, state)
    return _execute(output)


def resume_run(output: Path, *, solver_only: bool = False) -> RunResult:
    output = output.resolve()
    read_run(output)
    return _execute(output, solver_only=solver_only)
