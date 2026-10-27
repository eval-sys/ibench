from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid5

from harbor.models.job.config import JobConfig
from harbor.models.job.lock import JobLock, TrialLock
from harbor.models.job.result import JobResult, JobStats
from harbor.models.trajectories import Trajectory
from harbor.models.verifier.result import VerifierResult

from ibench.modules.harbor import trial_error, trial_rewards, trials
from ibench.modules.run_paths import read_trial, write_json
from ibench.services.runner import read_run


@dataclass
class UploadPlan:
    run: Path
    name: str
    config: JobConfig
    result: JobResult
    lock: JobLock
    records: list[tuple[Path, dict]]

    def summary(self) -> dict:
        repairs = [upload_rewards(entry)["repair"] for _, entry in self.records]
        return {
            "run": str(self.run), "name": self.name, "trials": len(repairs),
            "repaired": repairs.count(1), "not_repaired": repairs.count(0),
        }


def upload_plan(run: Path) -> UploadPlan:
    """Bind each solver attempt to its recorded scorer outcome without writing the run."""
    run = run.resolve()
    state = read_run(run)
    if state.kind != "run" or state.phase != "completed" or state.solver is None:
        raise ValueError(f"Upload requires a completed solver run: {run}")
    if len(state.solver.agents) != 1:
        raise ValueError("Upload requires exactly one solver agent")
    agent = state.solver.agents[0]
    model = (agent.model_name or "").rsplit("/", 1)[-1].lower()
    model = {"claude-opus-5-5": "opus-5.5"}.get(model, model)
    harness = agent.name or (agent.import_path or "").rsplit(":", 1)[-1].lower()
    effort = agent.kwargs.get("reasoning_effort") or agent.env.get("KIMI_MODEL_THINKING_EFFORT")
    if not model or not harness or not effort:
        raise ValueError("Upload naming requires a solver model, harness and reasoning effort")
    version = state.release.version.removesuffix(".0")
    name = f"ibench-v{version}-{model}-{effort}-{harness}"
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", name):
        raise ValueError(f"Invalid upload job name: {name}")

    job = run / "jobs/solve"
    config = JobConfig.model_validate_json((job / "config.json").read_bytes())
    result = JobResult.model_validate_json((job / "result.json").read_bytes())
    lock = JobLock.model_validate_json((job / "lock.json").read_bytes())
    report = json.loads((run / "results.json").read_bytes())
    if report.get("schema_version") != "ibench-results/v2" or report.get("phase") != "completed":
        raise ValueError("Upload requires completed ibench-results/v2 results")
    outcomes = {}
    for entry in report["trials"]:
        if not entry.get("solver_trial"):
            raise ValueError("Score outcome is missing its solver trial")
        key = (run / entry["solver_trial"]).resolve()
        if key in outcomes:
            raise ValueError(f"Duplicate solver outcome: {key}")
        outcomes[key] = entry
    records = []
    for directory, trial in trials(job):
        entry = outcomes.pop(directory.resolve(), None)
        if entry is None or trial.config.task.path is None or entry["task_id"] != trial.config.task.path.name:
            raise ValueError(f"Missing or mismatched score outcome: {directory}")
        TrialLock.model_validate_json((directory / "lock.json").read_bytes())
        Trajectory.model_validate_json((directory / "steps/solve/agent/trajectory.json").read_bytes())
        if not trial.finished_at:
            raise ValueError(f"Solver trial is unfinished: {directory}")
        if entry.get("status") == "scored":
            score = read_trial(run / entry["score_trial"] / "result.json")
            expected = next((item for item in state.inputs if item.solver_trial == directory), None)
            if (
                expected is None or score.config.task.path != expected.score_task
                or not score.finished_at or trial_error(score)
                or trial_rewards(score, "score") != entry.get("rewards")
                or entry["rewards"].get("repair") not in (0, 1)
            ):
                raise ValueError(f"Invalid or stale scorer outcome: {directory}")
        elif entry.get("status") != "failed" or not entry.get("error") or entry.get("rewards"):
            raise ValueError(f"Unresolved score outcome: {directory}")
        records.append((directory, entry))
    if outcomes or not records or len(records) != result.n_total_trials or len(lock.trials) != len(records):
        raise ValueError("Solver job, lock and score outcome counts do not match")
    return UploadPlan(run, name, config, result, lock, records)


def _link_or_copy(source, destination):
    try:
        return os.link(source, destination)
    except OSError:
        return shutil.copy2(source, destination)


def _public_config(value):
    """Omit execution-only endpoint fields, independent of their host names."""
    if isinstance(value, dict):
        return {
            key: _public_config(item) for key, item in value.items()
            if key not in {"extra_allowed_hosts", "env", "base_url", "baseURL", "api_base"}
        }
    if isinstance(value, list):
        return [_public_config(item) for item in value]
    return value


def upload_rewards(entry: dict) -> dict:
    if entry["status"] == "scored":
        rewards = dict(entry["rewards"])
        return {**rewards, "reward": rewards["repair"]}
    return {"reward": 0, "repair": 0, "protocol": 0}


def prepare_upload(plan: UploadPlan, output: Path) -> Path:
    """Create a native Harbor upload job without changing the source run."""
    # Uploaded objects are immutable. Version the published representation and
    # score bindings so retries reuse IDs, while changed scores get fresh objects.
    identity = json.dumps({
        "format": "ibench-harbor-upload/v4",
        "scores": sorted(
            (source.name, entry["status"], upload_rewards(entry))
            for source, entry in plan.records
        ),
    }, sort_keys=True)
    job_id = uuid5(plan.result.id, identity)
    job = output / plan.name
    shutil.copytree(plan.run / "jobs/solve", job, copy_function=_link_or_copy)
    config = plan.config.model_copy(deep=True)
    config.job_name, config.jobs_dir = plan.name, output
    write_json(job / "config.json", config.model_dump(mode="json"))
    exported = []
    for source, entry in plan.records:
        directory = job / source.name
        rewards = upload_rewards(entry)
        trial = read_trial(source / "result.json")
        solver_id = trial.id
        trial.id = uuid5(job_id, str(solver_id))
        trial.verifier_result = VerifierResult(rewards=rewards)
        trial.config.trials_dir = job
        trial.trial_uri = directory.resolve().as_uri()
        for step in trial.step_results or []:
            if step.step_name == "solve":
                step.verifier_result = trial.verifier_result.model_copy(deep=True)
        write_json(directory / "result.json", trial.model_dump(mode="json"))
        write_json(directory / "config.json", trial.config.model_dump(mode="json"))
        for verifier in [directory / "verifier", directory / "steps/solve/verifier"]:
            verifier.mkdir(parents=True, exist_ok=True)
            write_json(verifier / "reward.json", rewards)
        # The uploader's direct trajectory path is still agent/trajectory.json.
        agent = directory / "agent"
        agent.mkdir(exist_ok=True)
        (agent / "trajectory.json").unlink(missing_ok=True)
        # Distinct inodes keep both entries regular files in Harbor's tar archive.
        # Hub's step reader does not resolve tar hardlinks to the root entry.
        shutil.copyfile(source / "steps/solve/agent/trajectory.json", agent / "trajectory.json")
        exported.append(trial)
    result = plan.result.model_copy(deep=True)
    result.id = job_id
    result.n_total_trials = len(exported)
    result.trial_results = exported if result.trial_results else []
    result.stats = JobStats.from_trial_results(exported, n_total_trials=len(exported))
    write_json(job / "result.json", result.model_dump(mode="json"))
    lock = plan.lock.model_copy(deep=True)
    lock.trials = [
        TrialLock.model_validate_json((job / trial.trial_name / "lock.json").read_bytes()) for trial in exported
    ]
    write_json(job / "lock.json", lock.model_dump(mode="json"))
    for directory in [job, *(job / trial.trial_name for trial in exported)]:
        for name in ("config.json", "result.json", "lock.json"):
            path = directory / name
            write_json(path, _public_config(json.loads(path.read_bytes())))
    return job
