from __future__ import annotations

import json
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

from harbor.models.task.config import TaskConfig
from harbor.trial.trial import Trial

from ibench.modules.harbor import trial_error, trial_rewards
from ibench.services.audit import capture
from ibench.services.audit.inputs import AuditInput, prepare_audit, write_json


def prepare_recording(audit: AuditInput) -> None:
    """Use the published driver and capture wrapper without editing their logic."""
    step = audit.compiled / "steps/score"
    inputs = step / "workdir/audit-input"
    shutil.copytree(audit.scripts, inputs / "scripts")
    plan = {"task_id": audit.task.id, "cases": [{**c.model_dump(), "key": audit.case_key(c)} for c in audit.cases]}
    write_json(inputs / "plan.json", plan)
    solution = step / "solution"
    if solution.exists():
        shutil.rmtree(solution)
    solution.mkdir()
    commands = ["#!/usr/bin/env bash", "set -uo pipefail", "status=0"]
    for case in audit.cases:
        source = f"/workspace/audit-input/scripts/{audit.case_key(case)}"
        commands.extend(
            [
                f"cp -- {shlex.quote(source)}/* {shlex.quote(case.replay_root)}/ || status=1",
                f"bash {shlex.quote(case.capture)} || status=1",
            ]
        )
    commands.extend(["chmod -R a+rwX /logs/artifacts", 'exit "$status"'])
    (solution / "solve.sh").write_text("\n".join(commands) + "\n", encoding="utf-8")
    tests = audit.compiled / "tests"
    shutil.rmtree(tests)
    tests.mkdir()
    shutil.copyfile(Path(capture.__file__), tests / "verify.py")
    (tests / "test.sh").write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\npython3 /tests/verify.py /workspace/audit-input/plan.json\n",
        encoding="utf-8",
    )
    config_path = audit.compiled / "task.toml"
    config = TaskConfig.model_validate_toml(config_path.read_text())
    config.steps[0].verifier.timeout_sec = 120
    config_path.write_text(config.model_dump_toml(), encoding="utf-8")


@dataclass(frozen=True)
class ReplayResult:
    output: Path
    trial_path: Path
    success: bool
    cases: tuple[dict, ...]
    error: str | None


async def run_replay(
    root: Path,
    selection: str,
    output: Path,
    *,
    revision: str = "merged",
    patch: Path | None = None,
    fixture: str = "reference-after",
    scripts: Path | None = None,
    cases: tuple[str, ...] | None = None,
) -> ReplayResult:
    audit = prepare_audit(
        root, selection, output, revision=revision, patch=patch, fixture=fixture, scripts=scripts, cases=cases
    )
    prepare_recording(audit)
    trial = await Trial.create(audit.trial_config())
    result = await trial.run()
    artifacts = trial.paths.trial_dir / "steps/score/artifacts/logs/artifacts/tasks" / audit.task.id
    observed = []
    for case in audit.cases:
        evidence = artifacts / audit.case_key(case) / "evidence"
        path = evidence / "manifest.json"
        try:
            manifest = json.loads(path.read_bytes()) if path.exists() else None
            if manifest is not None and not isinstance(manifest, dict):
                manifest = {"error": "capture manifest must be an object"}
        except (ValueError, OSError) as error:
            manifest = {"error": str(error)}
        observed.append({"case_id": case.case_id, "evidence": str(evidence), "manifest": manifest})
    error = trial_error(result)
    success = error is None and trial_rewards(result, "score").get("capture") == 1
    if not success and error is None:
        error = next(
            (
                case.get("failure_summary")
                for item in observed
                for case in (item["manifest"] or {}).get("cases", [])
                if case.get("failure_summary")
            ),
            f"capture verification failed; inspect {trial.paths.trial_dir / 'steps/score/verifier'}",
        )
    summary = {
        "success": success,
        "error": error,
        "trial": str(trial.paths.trial_dir),
        "cases": observed,
        "scope": "capture/protocol only; Require has not been judged",
    }
    write_json(audit.output / "results.json", summary)
    return ReplayResult(audit.output, trial.paths.trial_dir, success, tuple(observed), error)
