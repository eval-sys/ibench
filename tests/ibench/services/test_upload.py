import hashlib
import json
import tarfile
from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

import pytest
from harbor.models.job.config import JobConfig
from harbor.models.job.lock import JobLock, TrialLock
from harbor.models.job.result import JobResult, JobStats
from harbor.models.trajectories import Trajectory
from harbor.models.trial.config import TrialConfig
from harbor.models.trial.result import AgentInfo, StepResult, TrialResult
from harbor.models.verifier.result import VerifierResult
from harbor.upload.uploader import _create_trial_archive, _load_job_from_disk
from typer.testing import CliRunner

from ibench.cli import app
from ibench.models import ReleaseManifest
from ibench.modules.run_paths import write_json
from ibench.services.runner.execution import RunState, ScoreInput, _save
from ibench.services.upload import prepare_upload, upload_plan


@pytest.fixture
def run(tmp_path):
    run = tmp_path / "run"
    task_id = "test-task"
    settings = JobConfig(agents=[{"name": "codex", "model_name": "gpt-6-astra", "kwargs": {
        "reasoning_effort": "high",
    }}])
    release = ReleaseManifest(
        schema_version="ibench-release/v1", name="ibench", version="0.1.0",
        instruction_profiles=["intent"], default_instruction_profile="intent",
        tasks=[{"id": task_id, "name": "map", "title": "Map", "base_commit_sha": "a" * 40,
                "merge_commit_sha": "b" * 40}],
    )
    state = RunState(kind="run", phase="completed", release=release, profile="intent",
                     solver=settings, scorer=settings)
    results = []
    solvers = []
    locks = []
    for attempt, repair in [(1, 1), (2, 0)]:
        native = {}
        for phase in ["solve", "score"]:
            directory = run / "jobs" / phase / f"attempt-{attempt}"
            directory.mkdir(parents=True)
            task = run / "compiled" / phase / (task_id if phase == "solve" else f"{task_id}--{attempt}")
            config = TrialConfig(task={"path": task}, agent=settings.agents[0],
                                 trials_dir=directory.parent, trial_name=directory.name)
            verifier = VerifierResult(rewards={"reward": 1} if phase == "solve" else {
                "reward": 0, "repair": repair, "protocol": 0,
            })
            now = datetime.now(UTC)
            trial = TrialResult(task_name="ibench/map", trial_name=directory.name,
                                trial_uri=directory.as_uri(), task_id=config.task.get_task_id(),
                                task_checksum="a" * 64, config=config,
                                agent_info=AgentInfo(name="codex", version="test"),
                                verifier_result=verifier,
                                step_results=[StepResult(step_name=phase, verifier_result=verifier)],
                                started_at=now, finished_at=now)
            write_json(directory / "result.json", trial.model_dump(mode="json"))
            write_json(directory / "config.json", config.model_dump(mode="json"))
            native[phase] = (directory, trial)
        directory, solver = native["solve"]
        agent = directory / "steps/solve/agent"
        agent.mkdir(parents=True)
        artifacts = directory / "steps/solve/artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "candidate.patch").write_text(f"diff --git a/file-{attempt} b/file-{attempt}\n")
        (agent / "trajectory.json").write_text(Trajectory.model_validate({
            "schema_version": "ATIF-v1.7", "session_id": str(uuid4()),
            "agent": {"name": "codex", "version": "test"},
            "steps": [{"step_id": 1, "source": "user", "message": f"Solver attempt {attempt}"}],
        }).model_dump_json())
        lock = TrialLock(task={"name": task_id, "type": "local", "digest": "sha256:" + "a" * 64},
                         agent=settings.agents[0], environment={}, verifier={})
        write_json(directory / "lock.json", lock.model_dump(mode="json"))
        solvers.append(solver)
        locks.append(lock)
        scorer_dir, scorer = native["score"]
        state.inputs.append(ScoreInput(task_id=task_id, solver_trial=directory, score_task=scorer.config.task.path))
        results.append({"task_id": task_id, "solver_trial": str(directory.relative_to(run)),
                        "score_trial": str(scorer_dir.relative_to(run)), "status": "scored",
                        "rewards": scorer.verifier_result.rewards})
    _save(run, state)
    write_json(run / "results.json", {"schema_version": "ibench-results/v2", "phase": "completed", "trials": results})
    job = run / "jobs/solve"
    write_json(job / "config.json", settings.model_dump(mode="json"))
    write_json(job / "lock.json", JobLock(n_concurrent_trials=2, retry={}, trials=locks).model_dump(mode="json"))
    write_json(job / "result.json", JobResult(
        id=uuid4(), started_at=now, finished_at=now, n_total_trials=2,
        stats=JobStats.from_trial_results(solvers), trial_results=solvers,
    ).model_dump(mode="json"))
    return run


def digest(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def test_upload_preserves_solver_trace_and_matches_each_attempt_to_scorer(run, tmp_path):
    before = digest(run)
    plan = upload_plan(run)
    job = prepare_upload(plan, tmp_path / "upload")
    result, config, trials, directories = _load_job_from_disk(job)
    assert config.job_name == "ibench-v0.1-gpt-6-astra-high-codex"
    assert result.id != plan.result.id
    assert [t.verifier_result.rewards["reward"] for t in trials] == [1, 0]
    assert result.stats.evals["codex__adhoc"].reward_stats["reward"] == {
        1: ["attempt-1"], 0: ["attempt-2"],
    }
    for trial in trials:
        assert trial.verifier_result.rewards["protocol"] == 0
        assert trial.step_results[0].verifier_result == trial.verifier_result
        target = directories[trial.trial_name]
        original = run / "jobs/solve" / trial.trial_name / "steps/solve/agent/trajectory.json"
        assert (target / "agent/trajectory.json").read_bytes() == original.read_bytes()
        with tarfile.open(fileobj=BytesIO(_create_trial_archive(target)), mode="r:gz") as archive:
            assert archive.extractfile("agent/trajectory.json").read() == original.read_bytes()
            member = archive.getmember("steps/solve/agent/trajectory.json")
            assert member.isfile() and not member.islnk()
            assert archive.extractfile(member).read() == original.read_bytes()
        assert not (target / "artifacts/ibench-score.json").exists()
    assert digest(run) == before

    repeated = prepare_upload(plan, tmp_path / "retry")
    assert JobResult.model_validate_json((repeated / "result.json").read_bytes()).id == result.id
    report_path = run / "results.json"
    report = json.loads(report_path.read_bytes())
    report["trials"][0].update(status="failed", rewards={}, error="Scorer failed")
    write_json(report_path, report)
    updated = prepare_upload(upload_plan(run), tmp_path / "updated")
    assert JobResult.model_validate_json((updated / "result.json").read_bytes()).id != result.id


def test_endpoint_fields_are_removed_from_all_upload_metadata(run, tmp_path):
    endpoint = "https://private-provider.example/v1"
    for path in [run / "run.json", run / "jobs/solve/config.json"]:
        raw = json.loads(path.read_bytes())
        agent = raw["solver"]["agents"][0] if path.name == "run.json" else raw["agents"][0]
        agent.update(extra_allowed_hosts=["private-provider.example"], env={"OPENAI_BASE_URL": endpoint})
        agent["kwargs"]["config"] = {"model_providers": {"custom": {"base_url": endpoint}}}
        write_json(path, raw)
    for path in (run / "jobs/solve").glob("*/config.json"):
        raw = json.loads(path.read_bytes())
        raw["agent"]["extra_allowed_hosts"] = ["another-private-host.example"]
        write_json(path, raw)
        result_path = path.with_name("result.json")
        result = json.loads(result_path.read_bytes())
        result["config"] = raw
        write_json(result_path, result)
    for path in [run / "jobs/solve/lock.json", *(run / "jobs/solve").glob("*/lock.json")]:
        raw = json.loads(path.read_bytes())
        for item in raw.get("trials", [raw]):
            item["agent"]["extra_allowed_hosts"] = ["third-private-host.example"]
        write_json(path, raw)
    before = digest(run)
    job = prepare_upload(upload_plan(run), tmp_path / "upload")
    for path in [*job.glob("*.json"), *job.glob("*/*.json")]:
        text = path.read_text()
        assert "private-provider.example" not in text
        assert "another-private-host.example" not in text
        assert "third-private-host.example" not in text
        assert '"extra_allowed_hosts"' not in text
        assert '"base_url"' not in text
    assert digest(run) == before


@pytest.mark.parametrize("error", ["Scorer setup failed", "AgentTimeoutError", "PermissionError"])
def test_failed_attempt_is_zero_without_mutating_original_result(run, tmp_path, error):
    path = run / "results.json"
    report = json.loads(path.read_bytes())
    report["trials"][1].update(status="failed", rewards={}, error=error)
    write_json(path, report)
    before = digest(run)
    plan = upload_plan(run)
    assert plan.summary()["not_repaired"] == 1
    job = prepare_upload(plan, tmp_path / "upload")
    result, _, trials, _ = _load_job_from_disk(job)
    assert [t.verifier_result.rewards["reward"] for t in trials] == [1, 0]
    assert trials[1].verifier_result.rewards == {"reward": 0, "repair": 0, "protocol": 0}
    assert result.n_total_trials == len(JobLock.model_validate_json((job / "lock.json").read_bytes()).trials) == 2
    assert not (job / "attempt-2/artifacts/ibench-score.json").exists()
    assert digest(run) == before


@pytest.mark.parametrize("patch", [None, b"", b"\n "])
def test_empty_or_missing_patch_always_scores_zero(run, tmp_path, patch):
    path = run / "jobs/solve/attempt-2/steps/solve/artifacts/candidate.patch"
    if patch is None:
        path.unlink()
    else:
        path.write_bytes(patch)
    report_path = run / "results.json"
    report = json.loads(report_path.read_bytes())
    report["trials"][1].update(status="failed", rewards={}, error="AgentTimeoutError")
    write_json(report_path, report)
    before = digest(run)
    plan = upload_plan(run)
    assert plan.summary()["not_repaired"] == 1
    job = prepare_upload(plan, tmp_path / "upload")
    result, _, trials, _ = _load_job_from_disk(job)
    assert result.n_total_trials == 2
    trial = next(t for t in trials if t.trial_name == "attempt-2")
    assert trial.verifier_result.rewards == {"reward": 0, "repair": 0, "protocol": 0}
    assert trial.step_results[0].verifier_result == trial.verifier_result
    assert json.loads((job / "attempt-2/verifier/reward.json").read_bytes()) == trial.verifier_result.rewards
    assert digest(run) == before


def test_rejects_stale_score_and_duplicate_attempt_mapping(run):
    path = run / "results.json"
    report = json.loads(path.read_bytes())
    report["trials"][0]["rewards"]["repair"] = 0
    write_json(path, report)
    with pytest.raises(ValueError, match="stale scorer"):
        upload_plan(run)
    report["trials"][1]["solver_trial"] = report["trials"][0]["solver_trial"]
    write_json(path, report)
    with pytest.raises(ValueError, match="Duplicate solver"):
        upload_plan(run)


def test_cli_dry_run_is_private_and_does_not_upload_or_modify_sources(run, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Dry run contacted Harbor")

    monkeypatch.setattr("harbor.cli.upload.upload_command", forbidden)
    before = digest(run)
    result = CliRunner().invoke(app, ["upload", str(run), "--dry-run"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["visibility"] == "private" and report["trials"] == 2
    assert digest(run) == before
