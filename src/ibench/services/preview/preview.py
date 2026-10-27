from __future__ import annotations

import json
import math
import subprocess
import threading
import webbrowser
from difflib import SequenceMatcher, unified_diff
from fractions import Fraction
from functools import lru_cache
from html import escape
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from harbor.models.task.config import TaskConfig
from pydantic import ValidationError
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

from ibench.models import CaseManifest, CaseRubric, ReleaseManifest, UserTask, VideoGuide
from ibench.services.preview.runs import model_scores, task_runs
from ibench.services.release.check import _load_json, _workspace_path, check_release

ASSET_ROOT = Path(__file__).parent / "viewer"
FIXTURE_SUFFIXES = {".js", ".json", ".mjs", ".sh", ".sql"}
MEDIA_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".webm"}


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected an object in {path}")
    return value


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return ""


def _highlight(path: Path, content: str) -> str:
    try:
        lexer = get_lexer_for_filename(path.name, content)
    except ClassNotFound:
        return escape(content)
    return highlight(content, lexer, HtmlFormatter(nowrap=True)).rstrip()


def _fixture_order(path: Path) -> tuple[int, str]:
    order = {
        "action.mjs": 0,
        "setup.mjs": 1,
        "setup.sh": 2,
        "setup.sql": 3,
        "cleanup.mjs": 4,
        "cleanup.sh": 5,
        "cleanup.sql": 6,
        "presentation.json": 7,
    }
    return order.get(path.name, len(order)), path.as_posix()


def _fixture_role(name: str) -> str:
    if name == "action.mjs":
        return "when"
    if name.startswith("setup."):
        return "given"
    return "support"


def _replay_files(task_root: Path, case_root: Path) -> dict[str, Any]:
    before_root = case_root / "fixtures/before"
    after_root = case_root / "fixtures/reference-after"
    relative_paths = {
        path.relative_to(root)
        for root in (before_root, after_root)
        if root.is_dir()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in FIXTURE_SUFFIXES
    }
    files = []
    for relative in sorted(relative_paths, key=_fixture_order):
        before_path = before_root / relative
        after_path = after_root / relative
        before = _text(before_path)
        after = _text(after_path)
        opcodes = SequenceMatcher(None, before.splitlines(), after.splitlines(), autojunk=False).get_opcodes()
        additions = sum(new_last - new_first for tag, _, _, new_first, new_last in opcodes if tag != "equal")
        deletions = sum(old_last - old_first for tag, old_first, old_last, _, _ in opcodes if tag != "equal")
        patch = ""
        if before != after:
            patch = (
                "\n".join(
                    unified_diff(
                        before.splitlines(),
                        after.splitlines(),
                        fromfile=f"reproduction/{relative.as_posix()}",
                        tofile=f"published-judge/{relative.as_posix()}",
                        lineterm="",
                    )
                )
                + "\n"
            )
        files.append(
            {
                "name": relative.as_posix(),
                "role": _fixture_role(relative.name),
                "changed": before != after,
                "additions": additions,
                "deletions": deletions,
                "patch": patch,
                "before": {
                    "path": before_path.relative_to(task_root).as_posix(),
                    "content": before,
                    "highlighted": _highlight(relative, before),
                },
                "after": {
                    "path": after_path.relative_to(task_root).as_posix(),
                    "content": after,
                    "highlighted": _highlight(relative, after),
                },
            }
        )
    changed = [item for item in files if item["changed"]]
    return {
        "total_file_count": len(files),
        "changed_file_count": len(changed),
        "unchanged_file_count": len(files) - len(changed),
        "additions": sum(item["additions"] for item in changed),
        "deletions": sum(item["deletions"] for item in changed),
        "files": files,
    }


def _media_url(task_id: str, task_root: Path, path: Path) -> str | None:
    if not path.is_file():
        return None
    return (
        f"/api/media/{quote(task_id, safe='')}/{quote(path.relative_to(task_root).as_posix())}"
        f"?v={path.stat().st_mtime_ns}"
    )


def _video_guide(presentation: dict[str, Any]) -> dict[str, Any] | None:
    # Optional viewing metadata must not break previews of existing fixtures.
    try:
        return VideoGuide.model_validate(presentation.get("video_guide")).model_dump()
    except ValidationError:
        return None


@lru_cache(maxsize=256)
def _video_fps(path: Path, mtime_ns: int) -> float | None:
    # Key by file revision so replacing a recording also refreshes its clock.
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=avg_frame_rate,r_frame_rate", "-of", "json", str(path)],
            capture_output=True, text=True, check=True, timeout=3,
        )
        stream = json.loads(result.stdout)["streams"][0]
        for key in ("avg_frame_rate", "r_frame_rate"):
            try:
                rate = float(Fraction(stream.get(key, "0/1")))
            except (ValueError, ZeroDivisionError):
                continue
            if math.isfinite(rate) and rate > 0:
                return rate
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError, TypeError):
        pass
    return None


def _case_preview(task_id: str, task_root: Path, context: Path, case: Any) -> dict[str, Any]:
    case_root = _workspace_path(case.input, context)
    user_task = _load_json(case_root / "user-task.json", UserTask)
    rubric = _load_json(case_root / "rubric.json", CaseRubric)
    assert isinstance(user_task, UserTask)
    assert isinstance(rubric, CaseRubric)
    presentation = (
        _json(case_root / "fixtures/reference-after/presentation.json")
        if (case_root / "fixtures/reference-after/presentation.json").is_file()
        else {}
    )
    before_presentation = case_root / "fixtures/before/presentation.json"
    definition = rubric.definition
    before = case_root / "evidence/before.webm"
    after = case_root / "evidence/reference-after.webm"
    return {
        "case_id": case.case_id,
        "label": presentation.get("title") or case.case_id.rsplit("/", 1)[-1],
        "intent": user_task.intent,
        "actions": user_task.actions,
        "given": definition.given,
        "when": definition.when,
        "observed": definition.observed,
        "require": definition.require,
        "allow": definition.allow,
        "theory": [item.model_dump() for item in definition.theory],
        "reference_observation": rubric.reference_observation,
        "requirement_rationale": rubric.requirement_rationale,
        "presentation_steps": presentation.get("steps", []),
        "before_video_guide": _video_guide(_json(before_presentation)) if before_presentation.is_file() else None,
        "after_video_guide": _video_guide(presentation),
        "before_url": _media_url(task_id, task_root, before),
        "after_url": _media_url(task_id, task_root, after),
        "before_video_fps": _video_fps(before, before.stat().st_mtime_ns) if before.is_file() else None,
        "after_video_fps": _video_fps(after, after.stat().st_mtime_ns) if after.is_file() else None,
        "replay": _replay_files(task_root, case_root),
    }


def _checked_release(root: Path) -> ReleaseManifest:
    result = check_release(root)
    if result.issues:
        details = "\n".join(f"- {issue}" for issue in result.issues)
        raise ValueError(f"release check failed:\n{details}")
    assert isinstance(result.release, ReleaseManifest)
    return result.release


def _task_preview(root: Path, task: Any) -> dict[str, Any]:
    task_root = root / "tasks" / task.id
    context = task_root / "score/steps/score/workdir/case-context"
    manifest = _load_json(context / "manifest.json", CaseManifest)
    assert isinstance(manifest, CaseManifest)
    return {
        **task.model_dump(),
        "cases": [_case_preview(task.id, task_root, context, case) for case in manifest.cases],
    }


def _task_definition_summary(task_root: Path, merge_commit_sha: str) -> dict[str, Any]:
    config_path = task_root / "solve/task.toml"
    config = TaskConfig.model_validate_toml(config_path.read_text(encoding="utf-8"))
    metadata = config.metadata or {}
    environment = config.environment
    return {
        "difficulty": metadata.get("difficulty"),
        "category": metadata.get("category"),
        "tags": config.task.keywords if config.task else [],
        "agent_timeout_sec": config.agent.timeout_sec,
        "verifier_timeout_sec": config.verifier.timeout_sec,
        "os": environment.os.value if environment.os else None,
        "cpus": environment.cpus,
        "memory_mb": environment.memory_mb,
        "storage_mb": environment.storage_mb,
        "gpus": environment.gpus,
        "has_solution": bool(merge_commit_sha),
        "has_docker_compose": (task_root / "solve/environment/docker-compose.yaml").is_file(),
    }


def build_preview(root: Path, task_id: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    release = _checked_release(root)
    selected = [task for task in release.tasks if task_id is None or task.id == task_id or task.name == task_id]
    if task_id is not None and not selected:
        raise ValueError(f"task is not listed in tasks/release.json: {task_id}")
    tasks = [_task_preview(root, task) for task in selected]
    return {
        "release": {
            "name": release.name,
            "version": release.version,
            "task_count": len(tasks),
            "case_count": sum(len(task["cases"]) for task in tasks),
        },
        "tasks": tasks,
    }


def _safe_media(root: Path, task_id: str, relative_path: str) -> Path:
    path = PurePosixPath(relative_path)
    if path.is_absolute() or ".." in path.parts or path.suffix.lower() not in MEDIA_SUFFIXES:
        raise HTTPException(status_code=404)
    task_root = (root / "tasks" / task_id).resolve()
    candidate = task_root.joinpath(*path.parts).resolve()
    if not candidate.is_relative_to(task_root) or not candidate.is_file():
        raise HTTPException(status_code=404)
    return candidate


def create_preview_app(root: Path, task_id: str | None = None) -> FastAPI:
    root = root.resolve()
    release = _checked_release(root)
    selected = [task for task in release.tasks if task_id is None or task.id == task_id or task.name == task_id]
    if task_id is not None and not selected:
        raise ValueError(f"task is not listed in tasks/release.json: {task_id}")
    tasks_by_name = {task.name: task for task in selected}
    summaries = []
    for task in selected:
        task_root = root / "tasks" / task.id
        context = task_root / "score/steps/score/workdir/case-context"
        manifest = _load_json(context / "manifest.json", CaseManifest)
        assert isinstance(manifest, CaseManifest)
        summaries.append(
            {
                **task.model_dump(),
                "repository": "/".join(manifest.cases[0].case_id.split("/")[1:3]),
                "case_count": len(manifest.cases),
                "case_ids": [case.case_id for case in manifest.cases],
                **_task_definition_summary(task_root, task.merge_commit_sha),
            }
        )
    release_index = {
        "release": {
            "name": release.name,
            "version": release.version,
            "task_count": len(summaries),
            "case_count": sum(task["case_count"] for task in summaries),
        },
        "tasks": summaries,
    }
    app = FastAPI(title="IBench Preview", docs_url=None, redoc_url=None)
    app.mount("/assets", StaticFiles(directory=ASSET_ROOT), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(ASSET_ROOT / "index.html")

    @app.get("/tasks/{task_name}", include_in_schema=False)
    def task_page(task_name: str) -> FileResponse:
        if task_name not in tasks_by_name:
            raise HTTPException(status_code=404)
        return FileResponse(ASSET_ROOT / "index.html")

    @app.get("/api/release")
    def get_release() -> dict[str, Any]:
        return release_index

    @app.get("/api/scores")
    def get_scores() -> dict[str, Any]:
        return model_scores(root, {task["id"] for task in summaries})

    @app.get("/api/tasks/{task_name}")
    def get_task(task_name: str) -> dict[str, Any]:
        task = tasks_by_name.get(task_name)
        if task is None:
            raise HTTPException(status_code=404)
        return _task_preview(root, task)

    @app.get("/api/tasks/{task_name}/runs")
    def get_task_runs(task_name: str) -> dict[str, Any]:
        task = tasks_by_name.get(task_name)
        if task is None:
            raise HTTPException(status_code=404)
        summary = next(item for item in summaries if item["id"] == task.id)
        return task_runs(root, task.id, summary["case_ids"])

    @app.get("/api/media/{requested_task_id}/{relative_path:path}", include_in_schema=False)
    def get_media(requested_task_id: str, relative_path: str) -> FileResponse:
        if requested_task_id not in {task.id for task in selected}:
            raise HTTPException(status_code=404)
        return FileResponse(_safe_media(root, requested_task_id, relative_path), headers={"Cache-Control": "no-cache"})

    return app


def serve_preview(root: Path, *, task_id: str | None, host: str, port: int, open_browser: bool) -> None:
    app = create_preview_app(root, task_id)
    url = f"http://{host}:{port}"
    if open_browser:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    print(f"IBench preview: {url}")
    uvicorn.run(app, host=host, port=port, log_level="warning")
