"""Check the release scorer's mechanical delivery contract."""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import NoReturn, cast

import pytest

OUTPUT = Path(os.environ.get("IBENCH_SCORE_OUTPUT_ROOT", "/logs/artifacts/score"))
INPUT = Path(os.environ.get("IBENCH_SCORE_INPUT_ROOT", "/workspace/case-context"))
WORKSPACE = Path(os.environ["IBENCH_SCORE_WORKSPACE"])
REWARD = Path(os.environ.get("IBENCH_SCORE_REWARD_FILE", "/logs/verifier/reward.json"))
ISSUE_RESULTS = Path(os.environ.get("IBENCH_SCORE_ISSUE_RESULTS_FILE", "/logs/verifier/issue-results.json"))
VERDICTS = {"repaired", "not_repaired"}
REPLAY_MODULES = ("action.mjs", "cleanup.mjs", "setup.mjs")
REPLAY_SQL = ("cleanup.sql", "setup.sql")
REPLAY_SHELL = ("cleanup.sh", "setup.sh")
REPLAY_FILES = (*REPLAY_MODULES, *REPLAY_SQL, *REPLAY_SHELL, "presentation.json")
RESULTS: dict[str, dict[str, object]] = {}
TASK_ID = os.environ.get("IBENCH_SCORE_TASK_ID", "").strip()
LOCK_PATHS = json.loads(os.environ["IBENCH_SCORE_LOCK_PATHS"])
PROTOCOL_ONLY = os.environ.get("IBENCH_SCORE_PROTOCOL_ONLY") == "1"


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def object_(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        fail(f"{name} must be an object")
    return cast(dict[str, object], value)


def string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{name} must be a non-empty string")
    return value.strip()


def strings(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
        fail(f"{name} must be a non-empty list of strings")
    return cast(list[str], value)


def run(*command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def validate_video(video: Path) -> None:
    if not video.is_file() or not video.stat().st_size:
        fail("after video is missing")
    result = run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video))
    try:
        raw_duration = object_(object_(json.loads(result.stdout), "ffprobe").get("format"), "format")["duration"]
        if not isinstance(raw_duration, str | int | float):
            fail("ffprobe duration must be numeric")
        duration = float(raw_duration)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        fail(result.stderr.strip() or "after video is unreadable")
    if result.returncode or not math.isfinite(duration) or round(duration * 1000) < 500:
        fail("after video must be at least 500ms")


def validate_workspace() -> str | None:
    commit_sha = run("git", "-C", str(WORKSPACE), "rev-parse", "HEAD")
    status = run("git", "-C", str(WORKSPACE), "status", "--porcelain")
    expected = OUTPUT / "runtime/candidate-commit-sha.txt"
    if commit_sha.returncode or status.returncode or not expected.is_file():
        return "candidate workspace is unreadable"
    if commit_sha.stdout.strip() != expected.read_text().strip() or status.stdout:
        return "scoring agent changed the candidate workspace"
    for relative in LOCK_PATHS:
        lockfile = WORKSPACE / relative
        delivered = OUTPUT / "runtime/locks" / relative
        if not lockfile.is_file() or not delivered.is_file() or lockfile.read_bytes() != delivered.read_bytes():
            return f"candidate lock changed during scoring: {relative}"
    return None


def manifest_cases() -> list[tuple[str, Path]]:
    manifest = object_(json.loads((INPUT / "manifest.json").read_text()), "manifest")
    if manifest.get("schema_version") != "ibench-score-manifest/v1" or manifest.get("task_id") != TASK_ID:
        fail("manifest task identity mismatch")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        fail("manifest cases must be a non-empty list")
    result = []
    for raw in cast(list[object], cases):
        item = object_(raw, "manifest case")
        case_id = string(item.get("case_id"), "case_id")
        issue = case_id.rsplit("/", 1)[-1]
        if not issue.isdigit():
            fail("case ID must end with an Issue number")
        result.append((case_id, OUTPUT / "issues" / issue))
    if len({case_id for case_id, _ in result}) != len(result):
        fail("manifest contains duplicate case IDs")
    return result


def validate_case(case_id: str, output: Path) -> tuple[str, str]:
    replay = output / "replay"
    missing = [name for name in REPLAY_FILES if not (replay / name).is_file()]
    if missing:
        fail(f"replay bundle is incomplete: {', '.join(missing)}")
    try:
        presentation = object_(json.loads((replay / "presentation.json").read_text()), "presentation")
    except json.JSONDecodeError as error:
        fail(f"presentation.json is invalid: {error}")
    fixture_mode = presentation.get("fixture_mode", "database-and-browser")
    if fixture_mode not in ("database-and-browser", "script-and-browser", "browser-only"):
        fail("presentation has invalid fixture_mode")
    required_content = (*REPLAY_MODULES, "presentation.json")
    if fixture_mode == "database-and-browser":
        required_content += REPLAY_SQL
    elif fixture_mode == "script-and-browser":
        required_content += REPLAY_SHELL
    if empty := [name for name in required_content if not (replay / name).stat().st_size]:
        fail(f"replay bundle is empty: {', '.join(empty)}")
    for name in REPLAY_MODULES:
        module = replay / name
        if "FIXTURE_NOT_IMPLEMENTED" in module.read_text(encoding="utf-8"):
            fail(f"replay {name} is not implemented")
        syntax = run("node", "--check", str(module))
        if syntax.returncode:
            fail(syntax.stderr.strip() or f"replay {name} has invalid JavaScript")
        imported = run(
            "node",
            "--input-type=module",
            "-e",
            'const m=await import(process.argv[1]); if(typeof m.default!=="function") process.exit(1)',
            module.resolve().as_uri(),
        )
        if imported.returncode:
            fail(imported.stderr.strip() or f"replay {name} must export a default function")
    for name in REPLAY_SHELL:
        script = replay / name
        if fixture_mode == "script-and-browser":
            if "FIXTURE_NOT_IMPLEMENTED" in script.read_text(encoding="utf-8"):
                fail(f"replay {name} is not implemented")
            syntax = run("bash", "-n", str(script))
            if syntax.returncode:
                fail(syntax.stderr.strip() or f"replay {name} has invalid shell syntax")
    verdict = object_(json.loads((output / "verdict.json").read_text()), "verdict")
    if verdict.get("schema_version") != "verifier-verdict/v1":
        fail("invalid verdict schema version")
    if verdict.get("case_id") != case_id:
        fail("verdict case ID mismatch")
    kind = string(verdict.get("verdict"), "verdict")
    if kind not in VERDICTS:
        fail("invalid verdict")
    summary = string(verdict.get("summary"), "summary")
    scenario = object_(verdict.get("scenario"), "scenario")
    if scenario.get("given_established") is not True or scenario.get("when_executed") is not True:
        fail("a binary verdict requires Given and When to be established")
    strings(scenario.get("evidence"), "scenario.evidence")
    requirement = object_(verdict.get("requirement"), "requirement")
    expected = "supported" if kind == "repaired" else "refuted"
    if requirement.get("result") != expected:
        fail("verdict and requirement result disagree")
    string(requirement.get("reason"), "requirement.reason")
    strings(requirement.get("evidence"), "requirement.evidence")
    allow = object_(verdict.get("allow"), "allow")
    if allow.get("considered") is not True:
        fail("a binary verdict requires Allow to be considered")
    string(allow.get("reason"), "allow.reason")
    validate_video(output / "evidence/after.webm")
    screenshot = output / "evidence/final.png"
    if not screenshot.is_file() or not screenshot.stat().st_size:
        fail("final screenshot is missing or empty")
    capture = object_(json.loads((output / "evidence/manifest.json").read_text()), "replay manifest")
    cases = capture.get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        fail("candidate replay manifest must contain one Issue")
    recorded = object_(cases[0], "replay case")
    if recorded.get("issue_id") != case_id or recorded.get("status") != "replay_passed":
        fail("candidate replay failed or has the wrong Issue identity")
    return kind, summary


CASES = manifest_cases()
WORKSPACE_ERROR = validate_workspace()


def record(case_id: str, output: Path, *, verdict: str | None, summary: str | None, error: str | None) -> None:
    RESULTS[output.name] = {
        "case_id": case_id,
        "protocol_valid": error is None,
        "verdict": verdict,
        "summary": summary,
        "error": error,
    }


@pytest.fixture(scope="session", autouse=True)
def aggregate_results() -> Iterator[None]:
    yield
    issue_results = []
    for case_id, output in CASES:
        issue_results.append(
            RESULTS.get(output.name)
            or {
                "case_id": case_id,
                "protocol_valid": False,
                "verdict": None,
                "summary": None,
                "error": "pytest did not record an Issue result",
            }
        )
    ISSUE_RESULTS.write_text(json.dumps(issue_results, separators=(",", ":")) + "\n")
    (OUTPUT / "report.md").write_text(
        "# Candidate repair verdicts\n\n"
        + "\n".join(
            f"- `{item['case_id']}`: **{item['verdict'] or 'verifier_failed'}** - {item['summary'] or item['error']}"
            for item in issue_results
        )
        + "\n"
    )
    score = int(all(item.get("verdict") == "repaired" for item in issue_results))
    protocol = int(all(item["protocol_valid"] for item in issue_results))
    REWARD.write_text(json.dumps({"reward": score, "protocol": protocol, "repair": score}) + "\n")


def issue_test(case: tuple[str, Path]) -> Callable[[], None]:
    def test() -> None:
        case_id, output = case
        try:
            if WORKSPACE_ERROR:
                fail(WORKSPACE_ERROR)
            kind, summary = validate_case(case_id, output)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            record(case_id, output, verdict=None, summary=None, error=str(error))
            pytest.fail(f"invalid scorer delivery: {error}", pytrace=False)
        record(case_id, output, verdict=kind, summary=summary, error=None)
        if not PROTOCOL_ONLY:
            assert kind == "repaired", summary

    return test


for _case in CASES:
    _test = issue_test(_case)
    _task = re.sub(r"[^a-zA-Z0-9]+", "_", TASK_ID).strip("_")
    _test.__name__ = f"test_{_task}_{_case[1].name.replace('-', '_')}"
    globals()[_test.__name__] = _test
