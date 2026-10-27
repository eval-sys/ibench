from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from ibench.models import ReleaseTask
from ibench.modules.harbor import configure_job
from ibench.services.release.compiler import load_release, prepare_reference
from ibench.services.runner.execution import run_calibration


@dataclass(frozen=True)
class OracleResult:
    job_path: Path
    reward: float | int


def prepare_oracle_task(root: Path, task_id: str, destination: Path) -> ReleaseTask:
    task = load_release(root, (task_id,)).tasks[0]
    prepare_reference(root, task, destination)
    return task


def run_oracle(
    root: Path,
    task_id: str,
    *,
    agent: str,
    model: str | None,
    jobs_dir: Path,
    environment: str | None,
    config_path: Path | None = None,
) -> OracleResult:
    scorer = configure_job(config_path, agent=agent, model=model, environment=environment, scoring=True)
    output = jobs_dir.resolve() / f"oracle-{task_id}-{uuid4().hex[:8]}"
    result = run_calibration(root, task_id, output, scorer=scorer)
    rewards = result.trials[0].get("rewards", {})
    if not result.success or rewards.get("reward") != 1:
        raise ValueError(f"oracle calibration failed with rewards {rewards!r}; inspect {output}")
    return OracleResult(job_path=output / "jobs/score", reward=rewards["reward"])
