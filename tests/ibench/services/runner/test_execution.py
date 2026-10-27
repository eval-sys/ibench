from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from harbor.job import Job
from harbor.models.job.config import JobConfig
from harbor.models.task.task import Task
from harbor.models.trial.result import AgentInfo, ExceptionInfo, StepResult, TrialResult
from harbor.models.verifier.result import VerifierResult
from typer.testing import CliRunner

from ibench.cli import app
from ibench.models import ReleaseManifest
from ibench.modules.harbor import configure_job
from ibench.services.release.check import check_release
from ibench.services.runner import read_run, resume_run, run_release, score_run
from ibench.services.runner.oracle import run_oracle

RELEASE_ROOT = Path(__file__).parents[4]
TASK_ID = "github__Afilmory__Afilmory__pull__243"


@pytest.fixture
def release(tmp_path: Path) -> Path:
    root = tmp_path / "release"
    manifest = ReleaseManifest.model_validate_json((RELEASE_ROOT / "tasks/release.json").read_bytes())
    task = next(task for task in manifest.tasks if task.id == TASK_ID)
    manifest = manifest.model_copy(update={"tasks": [task]})
    shutil.copytree(RELEASE_ROOT / "tasks" / TASK_ID, root / "tasks" / TASK_ID)
    (root / "tasks" / TASK_ID / "reference.patch").unlink(missing_ok=True)
    (root / "tasks/release.json").write_text(manifest.model_dump_json())
    return root


class TrialExecution:
    """Replace only container execution; exercise actual SDK planning, files and resume."""

    def __init__(self) -> None:
        self.executed: list[tuple[str, str]] = []
        self.interrupt: str | None = None
        self.patch: bytes | None = b"candidate change\n"
        self.patches: dict[str, bytes] = {}
        self.reward: float = 1
        self.missing_reward = False
        self.partial_trial = False
        self.solver_error: str | None = None

    async def run(self, job: Job, *args) -> list[TrialResult]:
        results = []
        remaining = job._remaining_trial_configs
        for index, config in enumerate(remaining):
            task = Task(config.task.path)
            phase = task.config.steps[0].name
            directory = config.trials_dir / config.trial_name
            directory.mkdir()
            (directory / "config.json").write_text(config.model_dump_json())
            now = datetime.now(UTC)
            verifier = VerifierResult(
                rewards={"reward": 1}
                if phase == "solve"
                else {"protocol": 1, "repair": self.reward, "reward": self.reward}
            )
            if phase == "score" and self.missing_reward:
                verifier = VerifierResult(rewards=None)
            result = TrialResult(
                task_name=task.name,
                trial_name=config.trial_name,
                trial_uri=directory.as_uri(),
                task_id=config.task.get_task_id(),
                task_checksum="sdk-test",
                config=config,
                agent_info=AgentInfo(name="nop", version="test"),
                started_at=now,
                finished_at=now,
                verifier_result=verifier,
                step_results=[StepResult(step_name=phase, verifier_result=verifier)],
            )
            if phase == "solve" and self.solver_error:
                target = result.step_results[0] if self.solver_error == "step" else result
                target.exception_info = ExceptionInfo.from_exception(RuntimeError("solver failed"))
            if phase == "solve" and self.patch is not None:
                patch = directory / "steps/solve/artifacts/candidate.patch"
                patch.parent.mkdir(parents=True)
                patch.write_bytes(self.patches.get(task.name, self.patch))
            if phase == "score":
                artifact = directory / "artifacts/logs/artifacts/tasks" / TASK_ID
                artifact.mkdir(parents=True)
                (artifact / "verdict.json").write_text(json.dumps({"reward": self.reward}))
                (artifact / "after.webm").write_bytes(b"test video evidence")
            (directory / "result.json").write_text(result.model_dump_json())
            results.append(result)
            self.executed.append((phase, config.trial_name))
            if self.interrupt == phase:
                self.interrupt = None
                if len(remaining) > index + 1:
                    cancelled_config = remaining[index + 1]
                    cancelled_dir = cancelled_config.trials_dir / cancelled_config.trial_name
                    cancelled_dir.mkdir()
                    cancelled = result.model_copy(
                        update={
                            "trial_name": cancelled_config.trial_name,
                            "config": cancelled_config,
                            "exception_info": ExceptionInfo.from_exception(asyncio_cancelled()),
                        }
                    )
                    (cancelled_dir / "config.json").write_text(cancelled_config.model_dump_json())
                    (cancelled_dir / "result.json").write_text(cancelled.model_dump_json())
                    (cancelled_dir / "partial-evidence.txt").write_text("keep this evidence")
                    if self.partial_trial:
                        (cancelled_dir / "result.json").unlink()
                raise RuntimeError("simulated process interruption")
        return results


def asyncio_cancelled():
    from asyncio import CancelledError

    return CancelledError("interrupted")


@pytest.fixture
def execution(monkeypatch: pytest.MonkeyPatch) -> TrialExecution:
    execution = TrialExecution()

    async def run(job, *args):
        return await execution.run(job, *args)

    monkeypatch.setattr(Job, "_run_trials_with_queue", run)
    return execution


def settings(attempts: int = 1, *, agent: str = "nop") -> JobConfig:
    return JobConfig(agents=[{"name": agent}], n_attempts=attempts, quiet=True)


def test_solver_only_then_resume_uses_frozen_tasks(release: Path, tmp_path: Path, execution: TrialExecution) -> None:
    (release / "tasks" / TASK_ID / "reference.patch").write_bytes(b"oracle reference\n")
    output = tmp_path / "run"
    result = run_release(
        release, output, solver=settings(2), scorer=settings(), profile="intent-actions", solver_only=True
    )
    assert result.phase == "pending" and result.success
    assert [phase for phase, _ in execution.executed] == ["solve", "solve"]
    prompt = output / "compiled/solve" / TASK_ID / "steps/solve/instruction.md"
    assert "Intention:" in prompt.read_text() and "Actions:" in prompt.read_text()
    assert len(result.trials) == 2
    assert not (release / "tasks" / TASK_ID / "score/steps/score/workdir/candidate.patch").exists()
    shutil.move(release, tmp_path / "moved-release")
    completed = resume_run(output)
    assert completed.success and completed.phase == "completed"
    assert [phase for phase, _ in execution.executed] == ["solve", "solve", "score", "score"]
    assert len({trial["score_task"] for trial in completed.trials}) == 2
    for trial in completed.trials:
        assert Path(trial["candidate_patch"]).read_bytes() == execution.patch
        assert (Path(trial["score_task"]) / "steps/score/workdir/candidate.patch").read_bytes() == execution.patch
        assert trial["verdicts"] and any(path.endswith(".webm") for path in trial["artifacts"])
    count = len(execution.executed)
    assert resume_run(output).success
    assert len(execution.executed) == count


@pytest.mark.parametrize("phase,partial", [("solve", False), ("score", False), ("score", True)])
def test_resume_reuses_completed_trials_and_restarts_cancelled_trials(
    release: Path,
    tmp_path: Path,
    execution: TrialExecution,
    phase: str,
    partial: bool,
) -> None:
    output = tmp_path / "run"
    execution.interrupt = phase
    execution.partial_trial = partial
    with pytest.raises(RuntimeError, match="simulated"):
        run_release(release, output, solver=settings(2), scorer=settings())
    state = json.loads((output / "run.json").read_bytes())
    assert state["phase"] == phase and "simulated" in state["error"]
    assert not json.loads((output / "results.json").read_bytes())["success"]
    result = resume_run(output)
    assert result.success
    assert [entry[0] for entry in execution.executed].count("solve") == 2
    assert [entry[0] for entry in execution.executed].count("score") == 2
    assert not (output / "interrupted").exists()
    assert not list((output / "jobs").rglob("partial-evidence.txt"))
    assert json.loads((output / "run.json").read_bytes())["error"] is None


def test_score_in_place_uses_frozen_inputs_and_preserves_solver(
    release: Path, tmp_path: Path, execution: TrialExecution
) -> None:
    output = tmp_path / "run"
    run_release(release, output, solver=settings(), scorer=settings(), solver_only=True)
    shutil.move(release, tmp_path / "moved-release")
    result = score_run(output, scorer=settings())
    assert result.success
    assert [phase for phase, _ in execution.executed] == ["solve", "score"]
    assert result.trials[0]["solver_trial"].startswith(str(output / "jobs/solve"))
    assert read_run(output).kind == "run"
    assert {p.name for p in output.iterdir()} == {"run.json", "results.json", "compiled", "jobs", ".run.lock"}
    solver_results = {p: p.read_bytes() for p in (output / "jobs/solve").rglob("*") if p.is_file()}
    with pytest.raises(ValueError, match="already exists"):
        score_run(output)
    score_run(output, overwrite=True)
    assert [phase for phase, _ in execution.executed] == ["solve", "score", "score"]
    assert all(p.read_bytes() == data for p, data in solver_results.items())


@pytest.mark.parametrize("location", [None, "trial", "step"])
def test_regular_solver_with_empty_patch_skips_scoring(
    release: Path, tmp_path: Path, execution: TrialExecution, location: str | None,
) -> None:
    execution.solver_error, execution.patch = location, b""
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="no trusted candidate patches"):
        run_release(release, output, solver=settings(agent="codex"), scorer=settings())
    assert [phase for phase, _ in execution.executed] == ["solve"]
    state = read_run(output)
    assert not state.inputs
    assert len(state.skipped) == 1
    assert state.skipped[0].error == (
        "RuntimeError: solver failed" if location else "solver produced an empty patch"
    )
    result = json.loads((output / "results.json").read_bytes())
    assert result["trials"][0]["status"] == "failed"
    assert not result["success"]


@pytest.mark.parametrize("location", ["trial", "step"])
def test_failed_solver_with_committed_patch_is_scored(
    release: Path, tmp_path: Path, execution: TrialExecution, location: str,
) -> None:
    execution.solver_error = location
    result = run_release(release, tmp_path / "run", solver=settings(agent="codex"), scorer=settings())
    assert result.success
    assert [phase for phase, _ in execution.executed] == ["solve", "score"]
    assert result.trials[0]["status"] == "scored"
    assert result.trials[0]["solver_error"] == "RuntimeError: solver failed"
    assert Path(result.trials[0]["candidate_patch"]).read_bytes() == execution.patch


@pytest.mark.parametrize("location", [None, "trial", "step"])
def test_nop_empty_patch_scores_base_commit_and_reward_zero_is_a_valid_result(
    release: Path,
    tmp_path: Path,
    execution: TrialExecution,
    location: str | None,
) -> None:
    execution.solver_error = location
    execution.patch, execution.reward = b"", 0
    result = run_release(release, tmp_path / "run", solver=settings(), scorer=settings())
    assert result.success
    trial = result.trials[0]
    assert trial["status"] == "scored" and trial["rewards"] == {"protocol": 1, "repair": 0, "reward": 0}
    assert Path(trial["candidate_patch"]).read_bytes() == b""
    workdir = Path(trial["score_task"]) / "steps/score/workdir"
    manifest = ReleaseManifest.model_validate_json((release / "tasks/release.json").read_bytes())
    assert (workdir / "candidate").read_text().strip() == manifest.tasks[0].base_commit_sha
    assert not (workdir / "candidate.patch").exists()


@pytest.mark.parametrize("phase", ["pending", "solve", "score", "completed"])
def test_run_can_move_and_resume_from_another_cwd(
    release: Path, tmp_path: Path, execution: TrialExecution, monkeypatch: pytest.MonkeyPatch, phase: str,
) -> None:
    output = tmp_path / "run"
    if phase in ("solve", "score"):
        execution.interrupt = phase
        with pytest.raises(RuntimeError, match="simulated"):
            run_release(release, output, solver=settings(2), scorer=settings())
    else:
        run_release(release, output, solver=settings(2), scorer=settings(), solver_only=phase == "pending")
    before = len(execution.executed)
    moved = tmp_path / "moved"
    output.rename(moved)
    shutil.rmtree(release)
    monkeypatch.chdir(tmp_path)
    result = resume_run(moved)
    assert result.success and result.phase == "completed"
    assert len(result.trials) == 2
    assert all(Path(x["candidate_patch"]).is_file() for x in result.trials)
    assert all(Path(x["score_trial"]).is_relative_to(moved) for x in result.trials)
    assert [p for p, _ in execution.executed].count("solve") == 2
    assert [p for p, _ in execution.executed].count("score") == 2
    if phase == "completed":
        assert len(execution.executed) == before
    disk = json.loads((moved / "results.json").read_text())
    assert disk["solver_job"] == "jobs/solve"
    assert all(not Path(x["candidate_patch"]).is_absolute() for x in disk["trials"])


def test_resume_keeps_input_lock_checks_after_relocation(
    release: Path, tmp_path: Path, execution: TrialExecution,
) -> None:
    execution.interrupt = "solve"
    output = tmp_path / "run"
    with pytest.raises(RuntimeError, match="simulated"):
        run_release(release, output, solver=settings(2), scorer=settings())
    moved = tmp_path / "moved"
    output.rename(moved)
    prompt = moved / "compiled/solve" / TASK_ID / "steps/solve/instruction.md"
    prompt.write_text(prompt.read_text() + "changed input\n")
    with pytest.raises(FileExistsError, match="lock"):
        resume_run(moved)


def test_cli_score_inherits_scorer_and_requires_explicit_overwrite(
    release: Path, tmp_path: Path, execution: TrialExecution,
) -> None:
    output = tmp_path / "run"
    scorer = settings()
    scorer.n_concurrent_trials = 3
    run_release(release, output, solver=settings(), scorer=scorer, solver_only=True)
    cli = CliRunner()
    assert cli.invoke(app, ["score", str(output)]).exit_code == 0
    assert read_run(output).scorer.n_concurrent_trials == 3
    assert cli.invoke(app, ["score", str(output)]).exit_code == 1
    assert cli.invoke(app, ["score", str(output), "--overwrite", "--n-concurrent", "2"]).exit_code == 0
    assert read_run(output).scorer.n_concurrent_trials == 2
    assert [p for p, _ in execution.executed] == ["solve", "score", "score"]


def test_score_reset_interruption_clears_old_verdicts_and_resumes(
    release: Path, tmp_path: Path, execution: TrialExecution, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ibench.services.runner import execution as runner

    output = tmp_path / "run"
    run_release(release, output, solver=settings(), scorer=settings())
    original = runner.bind_candidate

    def interrupted(*args, **kwargs):
        raise RuntimeError("reset interrupted")

    monkeypatch.setattr(runner, "bind_candidate", interrupted)
    with pytest.raises(RuntimeError, match="reset interrupted"):
        score_run(output, overwrite=True)
    disk = json.loads((output / "results.json").read_text())
    assert read_run(output).phase == "score-reset"
    assert not disk["success"] and not (output / "jobs/score").exists()
    assert all(not x.get("verdicts") for x in disk["trials"])
    monkeypatch.setattr(runner, "bind_candidate", original)
    assert resume_run(output).success
    assert [p for p, _ in execution.executed] == ["solve", "score", "score"]


def test_legacy_run_requires_explicit_migration(tmp_path: Path) -> None:
    (tmp_path / "run.json").write_text(json.dumps({"schema_version": "ibench-run/v1"}))
    with pytest.raises(ValueError, match="requires migration"):
        read_run(tmp_path)


def test_missing_trusted_patch_is_failure_not_silent_success(
    release: Path, tmp_path: Path, execution: TrialExecution
) -> None:
    execution.patch = None
    with pytest.raises(ValueError, match="no trusted candidate patches"):
        run_release(release, tmp_path / "run", solver=settings(), scorer=settings())
    result = json.loads((tmp_path / "run/results.json").read_bytes())
    assert not result["success"] and "missing" in result["trials"][0]["error"]
    assert all(phase == "solve" for phase, _ in execution.executed)


def test_multiple_tasks_and_attempts_bind_their_own_candidates(
    release: Path, tmp_path: Path, execution: TrialExecution,
) -> None:
    second_id = "github__Afilmory__Afilmory__pull__274"
    manifest = ReleaseManifest.model_validate_json((RELEASE_ROOT / "tasks/release.json").read_bytes())
    second = next(task for task in manifest.tasks if task.id == second_id)
    selected = ReleaseManifest.model_validate_json((release / "tasks/release.json").read_bytes())
    selected.tasks.append(second)
    shutil.copytree(RELEASE_ROOT / "tasks" / second_id, release / "tasks" / second_id)
    (release / "tasks/release.json").write_text(selected.model_dump_json())
    execution.patches = {f"ibench/{t.name}":t.id.encode() for t in selected.tasks}
    result = run_release(release, tmp_path / "run", solver=settings(2), scorer=settings())
    assert result.success and len(result.trials) == 4
    assert len({x["score_task"] for x in result.trials}) == 4
    for entry in result.trials:
        expected = entry["task_id"].encode()
        assert Path(entry["candidate_patch"]).read_bytes() == expected
        assert (Path(entry["score_task"]) / "steps/score/workdir/candidate.patch").read_bytes() == expected


def test_missing_score_reward_is_failure(release: Path, tmp_path: Path, execution: TrialExecution) -> None:
    execution.missing_reward = True
    result = run_release(release, tmp_path / "run", solver=settings(), scorer=settings())
    assert not result.success
    assert result.trials[0]["status"] == "failed" and result.trials[0]["error"] == "score reward is missing"


def test_resume_after_interruption_during_patch_binding(
    release: Path,
    tmp_path: Path,
    execution: TrialExecution,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ibench.services.runner import execution as runner

    original = runner.bind_candidate
    interrupted = False

    def compile_once(*args, **kwargs):
        nonlocal interrupted
        result = original(*args, **kwargs)
        if not interrupted:
            interrupted = True
            raise RuntimeError("binding interrupted after atomic copy")
        return result

    monkeypatch.setattr(runner, "bind_candidate", compile_once)
    output = tmp_path / "run"
    with pytest.raises(RuntimeError, match="binding interrupted"):
        run_release(release, output, solver=settings(2), scorer=settings())
    assert json.loads((output / "run.json").read_bytes())["phase"] == "bind"
    result = resume_run(output)
    assert result.success and len(result.trials) == 2
    assert [phase for phase, _ in execution.executed] == ["solve", "solve", "score", "score"]


def test_rejects_runtime_output_in_publication(release: Path, execution: TrialExecution) -> None:
    with pytest.raises(ValueError, match="published tasks"):
        run_release(release, release / "tasks/runtime", solver=settings(), scorer=settings())
    assert execution.executed == []


def test_selected_task_validation_does_not_hide_its_errors(release: Path) -> None:
    manifest = json.loads((release / "tasks/release.json").read_bytes())
    manifest["tasks"].append({**manifest["tasks"][0], "id": "missing-task", "name": "missing-task"})
    (release / "tasks/release.json").write_text(json.dumps(manifest))
    assert check_release(release).issues
    assert not check_release(release, (TASK_ID,)).issues
    rubric = next((release / "tasks" / TASK_ID).rglob("rubric.json"))
    value = json.loads(rubric.read_bytes())
    value.pop("requirement_rationale")
    rubric.write_text(json.dumps(value))
    assert check_release(release, (TASK_ID,)).issues


def test_cli_selects_task_name_and_instruction_profile(
    release: Path, tmp_path: Path, execution: TrialExecution
) -> None:
    manifest = json.loads((release / "tasks/release.json").read_bytes())
    manifest["tasks"][0]["name"] = "landscape-map"
    (release / "tasks/release.json").write_text(json.dumps(manifest))
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--path",
            str(release),
            "--output",
            str(tmp_path / "run"),
            "--task",
            "landscape-map",
            "--profile",
            "intent",
            "--solver-only",
            "--solver-agent",
            "nop",
            "--score-agent",
            "nop",
        ],
    )
    assert result.exit_code == 0, result.output
    instruction = (tmp_path / "run/compiled/solve" / TASK_ID / "steps/solve/instruction.md").read_text()
    assert "Intention:" in instruction and "Actions:" not in instruction


@pytest.mark.parametrize("reference", [None, b"manual reference patch\n"])
def test_oracle_uses_score_sdk_and_records_reference_binding(
    release: Path, tmp_path: Path, execution: TrialExecution, reference: bytes | None,
) -> None:
    if reference is not None:
        (release / "tasks" / TASK_ID / "reference.patch").write_bytes(reference)
    result = run_oracle(release, TASK_ID, agent="nop", model=None, jobs_dir=tmp_path / "jobs", environment="docker")
    assert result.reward == 1 and execution.executed[0][0] == "score"
    output = result.job_path.parent.parent
    state = read_run(output)
    binding = state.inputs[0]
    workdir = binding.score_task / "steps/score/workdir"
    if reference is None:
        assert binding.candidate_commit == state.release.tasks[0].merge_commit_sha
        assert binding.candidate_patch is None
        assert (workdir / "candidate").read_text() == binding.candidate_commit + "\n"
        assert not (workdir / "candidate.patch").exists()
    else:
        assert binding.candidate_commit is None
        assert binding.candidate_patch == workdir / "candidate.patch"
        assert binding.candidate_patch.read_bytes() == reference
        assert not (workdir / "candidate").exists()


def test_oracle_failure_stays_failed_on_resume(release: Path, tmp_path: Path, execution: TrialExecution) -> None:
    execution.reward = 0
    with pytest.raises(ValueError, match="calibration failed"):
        run_oracle(release, TASK_ID, agent="nop", model=None, jobs_dir=tmp_path / "jobs", environment="docker")
    output = next((tmp_path / "jobs").iterdir())
    assert not resume_run(output).success


def test_native_sdk_config_preserves_options_and_env_templates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IBENCH_TEST_KEY", "fake-secret-for-config-test")
    path = tmp_path / "config.json"
    config = JobConfig(agents=[{"name": "nop", "env": {"API_KEY": "${IBENCH_TEST_KEY}"}}], n_concurrent_trials=3)
    path.write_text(config.model_dump_json())
    loaded = configure_job(path, n_attempts=2, retries=1)
    assert loaded.n_concurrent_trials == 3 and loaded.n_attempts == 2 and loaded.retry.max_retries == 1
    assert "fake-secret-for-config-test" not in loaded.model_dump_json()
    assert loaded.agents[0].env["API_KEY"] == "${IBENCH_TEST_KEY}"


def test_codex_api_aliases_are_templates_and_endpoint_is_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_API_BASE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("CODEX_API_KEY", "fake-secret")
    monkeypatch.setenv("CODEX_BASE_URL", "https://example.invalid/v1")
    config = configure_job(agent="codex", scoring=True)
    agent = config.agents[0]
    assert agent.env["OPENAI_API_KEY"] == "${CODEX_API_KEY}"
    assert agent.env["OPENAI_BASE_URL"] == "${CODEX_BASE_URL}"
    assert "example.invalid" in agent.extra_allowed_hosts
    assert "fake-secret" not in config.model_dump_json()


def test_config_rejects_credentials_that_cannot_be_restored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IBENCH_API_KEY", raising=False)
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"agents": [{"name": "nop", "env": {"IBENCH_API_KEY": "fake-secret"}}]}))
    with pytest.raises(ValueError, match="environment templates"):
        configure_job(path)


@pytest.mark.parametrize(
    "options", [{"agents": [{"name": "oracle"}]}, {"verifier": {"disable": True}}, {"install_only": True}]
)
def test_score_rejects_options_that_bypass_real_judging(tmp_path: Path, options: dict) -> None:
    path = tmp_path / "config.json"
    path.write_text(JobConfig(**options).model_dump_json())
    with pytest.raises(ValueError):
        configure_job(path, scoring=True)
