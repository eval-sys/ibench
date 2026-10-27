from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from harbor.models.task.config import TaskConfig
from pydantic import ValidationError

from ibench.models import CaseManifest, CaseRubric, Model, ReleaseManifest, ReleaseTask, UserTask

SOLVE_INSTRUCTION_PLACEHOLDER = b"IBENCH_SOLVE_INSTRUCTION_PLACEHOLDER_V1\n"
CASE_CONTEXT_ROOT = PurePosixPath("/workspace/case-context")
SCORE_RUNTIME_BINDINGS = ("candidate", "candidate.patch")


@dataclass(frozen=True)
class CheckResult:
    release: ReleaseManifest | None
    issues: tuple[str, ...]


def _load_json(path: Path, model: type[Model]) -> Model:
    try:
        return model.model_validate_json(path.read_bytes())
    except FileNotFoundError as error:
        raise ValueError("file is missing") from error
    except (UnicodeDecodeError, ValidationError, json.JSONDecodeError) as error:
        raise ValueError(str(error)) from error


def _workspace_path(value: str, root: Path) -> Path:
    path = PurePosixPath(value)
    try:
        relative = path.relative_to(CASE_CONTEXT_ROOT)
    except ValueError as error:
        raise ValueError(f"path must be below {CASE_CONTEXT_ROOT}") from error
    if not relative.parts or ".." in relative.parts:
        raise ValueError(f"path must name a file or directory below {CASE_CONTEXT_ROOT}")
    return root.joinpath(*relative.parts)


def _check_harbor_task(path: Path, expected_step: str) -> TaskConfig:
    config_path = path / "task.toml"
    try:
        config = TaskConfig.model_validate_toml(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError("task.toml is missing") from error
    except (UnicodeDecodeError, ValidationError, ValueError) as error:
        raise ValueError(f"invalid Harbor task.toml: {error}") from error
    steps = [step.name for step in config.steps]
    if steps != [expected_step]:
        raise ValueError(f"expected one Harbor step named {expected_step!r}, found {steps!r}")
    return config


def _check_task(task_root: Path, task: ReleaseTask) -> list[str]:
    issues: list[str] = []
    for role in ("solve", "score"):
        try:
            _check_harbor_task(task_root / role, role)
        except ValueError as error:
            issues.append(f"{role}: {error}")

    slots = {"solve/steps/solve/instruction.md": SOLVE_INSTRUCTION_PLACEHOLDER}
    for relative, expected in slots.items():
        path = task_root / relative
        if not path.is_file() or path.read_bytes() != expected:
            issues.append(f"{relative}: invalid template placeholder")

    score_workdir = task_root / "score/steps/score/workdir"
    for name in SCORE_RUNTIME_BINDINGS:
        path = score_workdir / name
        if path.exists() or path.is_symlink():
            issues.append(f"score/steps/score/workdir/{name}: runtime binding must not be published")

    context = score_workdir / "case-context"
    try:
        manifest = _load_json(context / "manifest.json", CaseManifest)
    except ValueError as error:
        issues.append(f"score case manifest: {error}")
        return issues

    assert isinstance(manifest, CaseManifest)
    if manifest.task_id != task_root.name:
        issues.append("score case manifest task_id does not match its release directory")
    if task.cases and {case.case_id for case in task.cases} != {case.case_id for case in manifest.cases}:
        issues.append("release case IDs differ from score manifest")
    try:
        validate_script = _workspace_path(manifest.validate_path, context)
    except ValueError as error:
        issues.append(f"score case manifest: {error}")
    else:
        if not validate_script.is_file() or validate_script.stat().st_size == 0:
            issues.append(f"score case manifest: missing or empty {validate_script.relative_to(context)}")

    for index, case in enumerate(manifest.cases):
        label = f"case {index} ({case.case_id})"
        try:
            case_root = _workspace_path(case.input, context)
            capture = _workspace_path(case.capture, context)
        except ValueError as error:
            issues.append(f"{label}: {error}")
            continue
        try:
            _load_json(case_root / "user-task.json", UserTask)
        except ValueError as error:
            issues.append(f"{label} user-task.json: {error}")
        try:
            rubric = _load_json(case_root / "rubric.json", CaseRubric)
        except ValueError as error:
            issues.append(f"{label} rubric.json: {error}")
        else:
            assert isinstance(rubric, CaseRubric)
            if rubric.case_id != case.case_id:
                issues.append(f"{label} rubric case_id does not match the manifest")
        required = (
            capture,
            *(case_root / f"fixtures/{phase}/action.mjs" for phase in ("before", "reference-after")),
            case_root / "evidence/before.webm",
            case_root / "evidence/reference-after.webm",
        )
        for path in required:
            if not path.is_file() or path.stat().st_size == 0:
                issues.append(f"{label}: missing or empty {path.relative_to(context)}")
    return issues


def check_release(root: Path, selections: tuple[str, ...] | None = None) -> CheckResult:
    root = root.resolve()
    tasks_root = root / "tasks"
    try:
        manifest = _load_json(tasks_root / "release.json", ReleaseManifest)
    except ValueError as error:
        return CheckResult(release=None, issues=(f"tasks/release.json: {error}",))

    assert isinstance(manifest, ReleaseManifest)
    if selections is not None:
        selected = []
        for selection in selections:
            matches = [task for task in manifest.tasks if selection in (task.id, task.name)]
            if len(matches) != 1:
                return CheckResult(release=manifest, issues=(f"task selection is missing or ambiguous: {selection}",))
            if matches[0] not in selected:
                selected.append(matches[0])
        if not selected:
            return CheckResult(release=manifest, issues=("select at least one task",))
        manifest = manifest.model_copy(update={"tasks": selected})
    declared = {task.id for task in manifest.tasks}
    present = {path.name for path in tasks_root.iterdir() if path.is_dir()}
    issues = [f"tasks/{task_id}: listed but missing" for task_id in sorted(declared - present)]
    if selections is None:
        issues.extend(f"tasks/{task_id}: directory is not listed" for task_id in sorted(present - declared))
    for task in manifest.tasks:
        if task.id in present:
            issues.extend(f"tasks/{task.id}: {issue}" for issue in _check_task(tasks_root / task.id, task))
    return CheckResult(release=manifest, issues=tuple(issues))
