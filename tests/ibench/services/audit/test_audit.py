from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from harbor.models.task.task import Task
from harbor.models.trial.config import TrialConfig
from typer.testing import CliRunner

from ibench.agents.sleep import SleepAgent
from ibench.cli import app
from ibench.services.audit.debug import DebugSession
from ibench.services.audit.inputs import copy_scripts, prepare_audit
from ibench.services.audit.replay import prepare_recording

ROOT = Path(__file__).parents[4]
TASK = "github__Afilmory__Afilmory__pull__274"


def test_saved_action_bytes_survive_input_changes(tmp_path: Path) -> None:
    audit = prepare_audit(ROOT, TASK, tmp_path / "recording")
    source = audit.scripts / "issues/2"
    edited = tmp_path / "edited/issues/2"
    copy_scripts(source, edited)
    action = b'export default async function action() { console.log("edited"); }\n'
    (edited / "action.mjs").write_bytes(action)
    second = prepare_audit(ROOT, TASK, tmp_path / "edited-run", scripts=edited.parents[1])
    (edited / "action.mjs").unlink()
    prepare_recording(second)
    assert (second.scripts / "issues/2/action.mjs").read_bytes() == action
    compiled = Task(second.compiled)
    assert compiled.config.steps[0].name == "score"
    # Stable public contract: recording uses the published driver, independent of a judge.
    assert compiled.paths.step_solution_dir("score").joinpath("solve.sh").is_file()
    assert (second.compiled / "environment/replay/replay.mjs").read_bytes() == (
        ROOT / "tasks" / TASK / "score/environment/replay/replay.mjs"
    ).read_bytes()
    assert json.loads((second.output / "audit.json").read_text())["revision"] == second.task.merge_commit_sha
    TrialConfig.model_validate_json(second.trial_config().model_dump_json())
    assert not (ROOT / "tasks" / TASK / "score/steps/score/workdir/candidate").exists()


@pytest.mark.parametrize("bad", ["missing", "symlink", "presentation"])
def test_bad_fixtures_block_before_creating_run(tmp_path: Path, bad: str) -> None:
    source = ROOT / "tasks" / TASK / "score/steps/score/workdir/case-context/issues/2/fixtures/reference-after"
    fixture = tmp_path / "scripts/issues/2"
    shutil.copytree(source, fixture)
    if bad == "presentation":
        (fixture / "presentation.json").write_text("{}")
    else:
        (fixture / "setup.sh").unlink()
        if bad == "symlink":
            (fixture / "setup.sh").symlink_to(source / "setup.sh")
    with pytest.raises(ValueError):
        prepare_audit(ROOT, TASK, tmp_path / "run", scripts=fixture.parents[1])
    assert not (tmp_path / "run").exists()


def test_attempts_cannot_overwrite_evidence_and_patch_requires_base(tmp_path: Path) -> None:
    output = tmp_path / "run"
    prepare_audit(ROOT, TASK, output)
    (output / "evidence.txt").write_text("keep me")
    with pytest.raises(ValueError, match="already exists"):
        prepare_audit(ROOT, TASK, output)
    assert (output / "evidence.txt").read_text() == "keep me"
    patch = tmp_path / "candidate.patch"
    patch.write_bytes(b"")
    with pytest.raises(ValueError, match="requires"):
        prepare_audit(ROOT, TASK, tmp_path / "bad", patch=patch)
    with pytest.raises(ValueError, match="unknown or empty"):
        prepare_audit(ROOT, TASK, tmp_path / "bad", cases=("missing",))
    baseline = prepare_audit(ROOT, TASK, tmp_path / "baseline", revision="base", patch=patch)
    assert (baseline.output / "candidate.patch").read_bytes() == b""
    assert (baseline.compiled / "steps/score/workdir/candidate").read_text().strip() == baseline.task.base_commit_sha
    assert not (baseline.compiled / "steps/score/workdir/candidate.patch").exists()
    # Different parent directories with the same name must never share a Docker project.
    assert prepare_audit(ROOT, TASK, tmp_path / "other/run").trial_config().trial_name != (
        prepare_audit(ROOT, TASK, tmp_path / "third/run").trial_config().trial_name
    )


def test_sleep_agent_holds_until_release_and_saves_prompt(tmp_path: Path) -> None:
    class Environment:
        async def upload_file(self, source, target):
            shutil.copyfile(source, tmp_path / "uploaded.md")

    async def exercise():
        agent = SleepAgent(logs_dir=tmp_path)
        operation = asyncio.create_task(agent.run("inspect this task", Environment(), None))
        await agent.ready.wait()
        assert not operation.done()
        assert (tmp_path / "uploaded.md").read_text() == "inspect this task"
        agent.release.set()
        await operation

    asyncio.run(exercise())


def test_session_exit_saves_exact_edits_before_cleanup(tmp_path: Path) -> None:
    audit = prepare_audit(ROOT, TASK, tmp_path / "debug")
    environment_root = tmp_path / "environment"
    agent = SleepAgent(logs_dir=tmp_path)

    class Environment:
        def path(self, path):
            return environment_root / path.lstrip("/")

        async def upload_file(self, source, target):
            destination = self.path(target)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        async def upload_dir(self, source, target):
            shutil.copytree(source, self.path(target))

        async def download_dir(self, source, target):
            shutil.copytree(self.path(source), target)

        async def exec(self, *args, **kwargs):
            return SimpleNamespace(stdout="prepared-checkout\n", stderr=None, return_code=0)

        async def close(self):
            shutil.rmtree(environment_root)

    environment = Environment()

    class NativeExecution:
        async def run(self):
            await agent.run("inspect", environment, None)
            return SimpleNamespace(exception_info=None, step_results=[])

    native = NativeExecution()
    native.agent, native.agent_environment = agent, environment

    async def exercise():
        async with DebugSession(audit, native) as session:
            assert session.status == "ready"
            edited = environment.path(audit.cases[0].replay_root) / "action.mjs"
            edited.write_bytes(b'export default async function action() { console.log("edit"); }\n')
        assert session.status == "closed"
        assert not environment_root.exists()
        saved = audit.output / "edited-scripts/issues/2/action.mjs"
        assert saved.read_bytes() == b'export default async function action() { console.log("edit"); }\n'
        assert json.loads((audit.output / "edited-scripts/collection.json").read_text())["task_id"] == TASK
        assert (audit.scripts / "issues/2/action.mjs").read_bytes() != saved.read_bytes()

    asyncio.run(exercise())


def test_cli_rejects_incomplete_scripts_without_starting_environment(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "replay",
            TASK,
            "--path",
            str(ROOT),
            "--scripts",
            str(tmp_path),
            "-o",
            str(tmp_path / "run"),
        ],
    )
    assert result.exit_code == 1 and "missing regular replay file" in result.output
    assert not (tmp_path / "run").exists()
