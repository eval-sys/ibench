from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from harbor.models.task.config import TaskConfig
from jinja2 import Environment, StrictUndefined

from ibench.models import CaseManifest, ReleaseManifest, ReleaseTask, UserTask
from ibench.services.release.check import CASE_CONTEXT_ROOT, SOLVE_INSTRUCTION_PLACEHOLDER, check_release


def load_release(root: Path, selections: tuple[str, ...] | None = None) -> ReleaseManifest:
    checked = check_release(root, selections)
    if checked.issues:
        raise ValueError("release is invalid:\n" + "\n".join(f"- {issue}" for issue in checked.issues))
    assert checked.release is not None
    return checked.release


def snapshot_release(root: Path, manifest: ReleaseManifest, destination: Path) -> None:
    destination.mkdir(parents=True)
    for task in manifest.tasks:
        shutil.copytree(root / "tasks" / task.id, destination / "tasks" / task.id)
    (destination / "tasks/release.json").write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")


def compile_prompt(task_root: Path, profile: str) -> str:
    if profile not in ("intent", "intent-actions"):
        raise ValueError(f"unknown instruction profile: {profile}")
    context = task_root / "score/steps/score/workdir/case-context"
    manifest = CaseManifest.model_validate_json((context / "manifest.json").read_bytes())
    sections = []
    for case in manifest.cases:
        source = context / Path(case.input).relative_to(CASE_CONTEXT_ROOT) / "user-task.json"
        prompt = UserTask.model_validate_json(source.read_bytes())
        section = f"- {prompt.intent}"
        if profile == "intent-actions":
            actions = "\n".join(f"{number}. {action}" for number, action in enumerate(prompt.actions, start=1))
            section = f"Intention:\n{section}\n\nActions:\n{actions}"
        sections.append(section)
    tasks = "\n\n".join(sections) if profile == "intent-actions" else "Intention:\n" + "\n".join(sections)
    template = Path(__file__).with_name("solver-instruction.md.j2").read_text(encoding="utf-8")
    return Environment(undefined=StrictUndefined, keep_trailing_newline=True).from_string(template).render(tasks=tasks)


def compile_task(
    source: Path,
    destination: Path,
    *,
    name: str,
    instruction: str | None = None,
    patch: bytes | None = None,
    commit: str | None = None,
    unbound: bool = False,
) -> Path:
    """Bind a template atomically, preserving an existing identical binding."""
    if sum(value is not None for value in (instruction, patch, commit)) != (0 if unbound else 1):
        raise ValueError("a task must have exactly one binding, or explicitly be unbound")
    if destination.exists():
        # A previous attempt may have finished compiling just before interruption.
        config = TaskConfig.model_validate_toml((destination / "task.toml").read_text())
        if config.task is None or config.task.name != name:
            raise ValueError(f"compiled task identity changed: {destination}")
        if instruction is not None and (destination / "steps/solve/instruction.md").read_text() != instruction:
            raise ValueError(f"compiled instruction changed: {destination}")
        workdir = destination / "steps/score/workdir"
        if patch is not None and (workdir / "candidate.patch").read_bytes() != patch:
            raise ValueError(f"compiled candidate patch changed: {destination}")
        if commit is not None and (workdir / "candidate").read_text() != commit + "\n":
            raise ValueError(f"compiled candidate commit changed: {destination}")
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".compile-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "task"
        shutil.copytree(source, staging)
        config_path = staging / "task.toml"
        config = TaskConfig.model_validate_toml(config_path.read_text(encoding="utf-8"))
        if config.task is None:
            raise ValueError(f"missing Harbor task metadata: {source}")
        config.task.name = name
        config_path.write_text(config.model_dump_toml(), encoding="utf-8")
        if instruction is not None:
            slot = staging / "steps/solve/instruction.md"
            if slot.read_bytes() != SOLVE_INSTRUCTION_PLACEHOLDER:
                raise ValueError(f"invalid solver instruction placeholder: {source}")
            slot.write_text(instruction, encoding="utf-8")
        if patch is not None:
            (staging / "steps/score/workdir/candidate.patch").write_bytes(patch)
        if commit is not None:
            (staging / "steps/score/workdir/candidate").write_text(commit + "\n", encoding="utf-8")
        staging.rename(destination)
    return destination


def bind_candidate(
    destination: Path, *, patch: bytes | None = None, commit: str | None = None, replace: bool = False,
) -> None:
    """Bind a frozen score input; interrupted identical binds are safe to repeat."""
    if (patch is not None) + (commit is not None) != 1:
        raise ValueError("a score task must have exactly one patch or commit")
    workdir = destination / "steps/score/workdir"
    target = workdir / ("candidate.patch" if patch is not None else "candidate")
    other = workdir / ("candidate" if patch is not None else "candidate.patch")
    content = patch if patch is not None else (commit + "\n").encode()
    if not replace and (other.exists() or (target.exists() and target.read_bytes() != content)):
        raise ValueError(f"compiled candidate binding changed: {destination}")
    other.unlink(missing_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(target)


def prepare_solve(root: Path, task: ReleaseTask, destination: Path, profile: str) -> Path:
    task_root = root / "tasks" / task.id
    return compile_task(
        task_root / "solve", destination, name=f"ibench/{task.name}", instruction=compile_prompt(task_root, profile)
    )


def prepare_reference(root: Path, task: ReleaseTask, destination: Path) -> Path:
    task_root = root / "tasks" / task.id
    reference = task_root / "reference.patch"
    patch = reference.read_bytes() if reference.exists() else None
    return compile_task(
        task_root / "score", destination, name=f"ibench/{task.name}-oracle",
        patch=patch, commit=task.merge_commit_sha if patch is None else None,
    )
