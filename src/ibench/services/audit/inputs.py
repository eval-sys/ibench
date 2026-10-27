from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from harbor.models.trial.config import TrialConfig

from ibench.models import Case, CaseManifest, ReleaseTask
from ibench.services.audit.capture import REPLAY_FILES
from ibench.services.release.check import CASE_CONTEXT_ROOT
from ibench.services.release.compiler import compile_task, load_release, snapshot_release


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_scripts(source: Path) -> None:
    for name in REPLAY_FILES:
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing regular replay file: {path}")
    presentation = json.loads((source / "presentation.json").read_bytes())
    if (
        not isinstance(presentation, dict)
        or not isinstance(presentation.get("entry_path"), str)
        or not presentation["entry_path"].strip()
    ):
        raise ValueError(f"presentation entry_path is missing: {source}")
    if presentation.get("fixture_mode", "database-and-browser") not in (
        "database-and-browser",
        "script-and-browser",
        "browser-only",
    ):
        raise ValueError(f"unsupported replay fixture_mode: {source}")


def copy_scripts(source: Path, destination: Path) -> None:
    """Freeze the complete contract; never infer absent fixtures or follow links."""
    validate_scripts(source)
    destination.mkdir(parents=True)
    for name in REPLAY_FILES:
        shutil.copyfile(source / name, destination / name)


@dataclass(frozen=True)
class AuditInput:
    root: Path
    output: Path
    task: ReleaseTask
    cases: tuple[Case, ...]
    compiled: Path
    revision: str

    @property
    def scripts(self) -> Path:
        return self.output / "scripts"

    def case_key(self, case: Case) -> str:
        return Path(case.input).relative_to(str(CASE_CONTEXT_ROOT)).as_posix()

    def trial_config(self, *, debug: bool = False) -> TrialConfig:
        return TrialConfig(
            task={"path": self.compiled},
            trials_dir=self.output / "trials",
            trial_name=f"{'debug' if debug else 'replay'}-{uuid4().hex[:10]}",
            agent={"import_path": "ibench.agents.sleep:SleepAgent", "override_timeout_sec": 86400}
            if debug
            else {"name": "oracle"},
            environment={"import_path": "ibench.services.audit.debug:DebugDockerEnvironment"}
            if debug
            else {"type": "docker"},
            verifier={"disable": debug},
        )


def prepare_audit(
    root: Path,
    selection: str,
    output: Path,
    *,
    revision: str = "merged",
    patch: Path | None = None,
    fixture: str = "reference-after",
    scripts: Path | None = None,
    cases: tuple[str, ...] | None = None,
) -> AuditInput:
    root, output = root.resolve(), output.resolve()
    release = load_release(root, (selection,))
    task = release.tasks[0]
    if output.is_relative_to(root / "tasks"):
        raise ValueError("runtime output must not be written below the published tasks directory")
    if output.exists():
        raise ValueError(f"output already exists; choose a new attempt directory: {output}")
    if fixture not in ("before", "reference-after"):
        raise ValueError("fixture must be before or reference-after")
    commit = {"base": task.base_commit_sha, "merged": task.merge_commit_sha}.get(revision, revision)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("revision must be base, merged, or a full commit SHA")
    if patch is not None and revision != "base":
        raise ValueError("--patch requires --revision base")
    patch_bytes = patch.read_bytes() if patch else None
    if scripts and (scripts / "collection.json").exists():
        collection = json.loads((scripts / "collection.json").read_bytes())
        if collection.get("task_id") != task.id:
            raise ValueError("collected scripts belong to another task")
    context = root / "tasks" / task.id / "score/steps/score/workdir/case-context"
    manifest = CaseManifest.model_validate_json((context / "manifest.json").read_bytes())
    selected = tuple(c for c in manifest.cases if cases is None or c.case_id in cases)
    missing = set(cases or ()) - {c.case_id for c in selected}
    if missing or not selected:
        raise ValueError(f"unknown or empty case selection: {sorted(missing)}")
    # Validate caller-owned scripts before creating any runtime output.
    for case in selected:
        relative = Path(case.input).relative_to(str(CASE_CONTEXT_ROOT))
        source = scripts.resolve() / relative if scripts else context / relative / "fixtures" / fixture
        validate_scripts(source)
    output.mkdir(parents=True)
    snapshot_release(root, release, output / "snapshot")
    compiled = compile_task(
        output / "snapshot/tasks" / task.id / "score",
        output / "compiled",
        name=f"ibench/{task.name}",
        **({"patch": patch_bytes} if patch_bytes else {"commit": commit}),
    )
    if patch is not None:
        (output / "candidate.patch").write_bytes(patch_bytes)
    audit = AuditInput(root, output, task, selected, compiled, commit)
    for case in selected:
        relative = Path(audit.case_key(case))
        source = (
            scripts.resolve() / relative
            if scripts
            else output
            / "snapshot/tasks"
            / task.id
            / "score/steps/score/workdir/case-context"
            / relative
            / "fixtures"
            / fixture
        )
        copy_scripts(source, audit.scripts / relative)
    write_json(
        output / "audit.json",
        {
            "task_id": task.id,
            "revision": commit,
            "patch": patch is not None,
            "fixture": fixture,
            "cases": [c.model_dump() for c in selected],
        },
    )
    return audit
