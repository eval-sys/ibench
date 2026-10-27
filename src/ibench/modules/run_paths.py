from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote, urlparse

from harbor.models.job.config import JobConfig
from harbor.models.job.lock import JobLock, TrialLock
from harbor.models.job.result import JobResult
from harbor.models.trial.config import TrialConfig
from harbor.models.trial.result import TrialResult
from pydantic import BaseModel


def map_paths(value, transform: Callable[[Path], Path]):
    """Transform typed host paths without rewriting prompts, env values or URLs."""
    if isinstance(value, Path):
        return transform(value)
    if isinstance(value, BaseModel):
        updates = {name: map_paths(getattr(value, name), transform) for name in type(value).model_fields}
        if isinstance(value, TrialResult) and urlparse(value.trial_uri).scheme == "file":
            updates["trial_uri"] = transform(Path(unquote(urlparse(value.trial_uri).path))).as_uri()
        return value.model_copy(update=updates)
    if isinstance(value, dict):
        return {key: map_paths(item, transform) for key, item in value.items()}
    if isinstance(value, list):
        return [map_paths(item, transform) for item in value]
    return value


def relative_path(path: Path, root: Path) -> Path:
    return path.relative_to(root) if path.is_absolute() and path.is_relative_to(root) else path


def rebase_path(path: Path, old_root: Path, root: Path) -> Path:
    if not path.is_absolute():
        return root / path
    return root / path.relative_to(old_root) if path.is_relative_to(old_root) else path


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_trial(path: Path) -> TrialResult:
    result = TrialResult.model_validate_json(path.read_bytes())
    root = path.parent.parent.parent.parent.resolve()
    old_root = result.config.trials_dir.parent.parent
    return map_paths(result, lambda p: rebase_path(p, old_root, root))


def _path_updates(raw, before, after):
    if before == after:
        return raw
    if isinstance(raw, dict):
        return {
            key: _path_updates(value, before[key], after[key]) if key in before and key in after else value
            for key, value in raw.items()
        }
    if isinstance(raw, list):
        return [_path_updates(x, a, b) for x, a, b in zip(raw, before, after, strict=True)]
    return after


def relocate_job(job_path: Path) -> None:
    """Rebind native metadata before SDK reconciliation, retaining input digests."""
    config_path = job_path / "config.json"
    if not config_path.exists():
        return
    config = JobConfig.model_validate_json(config_path.read_bytes())
    root = job_path.parent.parent.resolve()
    old_root = config.jobs_dir.parent
    def transform(path: Path) -> Path:
        return rebase_path(path, old_root, root)

    files: list[tuple[Path, type[BaseModel]]] = [
        (job_path / "lock.json", JobLock), (job_path / "result.json", JobResult),
    ]
    for directory in sorted(p for p in job_path.iterdir() if p.is_dir()):
        files.extend([
            (directory / "config.json", TrialConfig),
            (directory / "result.json", TrialResult),
            (directory / "lock.json", TrialLock),
        ])
    files.append((config_path, JobConfig))  # Keep the old-root anchor until last.
    # Validate every metadata file before changing any of them. Repeating after
    # an interruption is safe: already relocated absolute paths stay unchanged.
    changes = []
    for path, model in files:
        if path.exists():
            raw = json.loads(path.read_bytes())
            original = model.model_validate(raw)
            rebound = map_paths(original, transform)
            before, after = original.model_dump(mode="json"), rebound.model_dump(mode="json")
            if before != after:
                changes.append((path, _path_updates(raw, before, after)))
    for path, value in changes:
        write_json(path, value)
