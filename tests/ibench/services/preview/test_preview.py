from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ibench.services.preview import build_preview, create_preview_app
from ibench.services.preview.preview import _media_url, _video_guide

RELEASE_ROOT = Path(__file__).parents[4]


def test_preview_contains_every_published_case() -> None:
    preview = build_preview(RELEASE_ROOT)
    expected_case_ids = []
    for task in preview["tasks"]:
        manifest_path = RELEASE_ROOT / "tasks" / task["id"] / "score/steps/score/workdir/case-context/manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_case_ids.extend(case["case_id"] for case in manifest["cases"])
    actual_case_ids = [case["case_id"] for task in preview["tasks"] for case in task["cases"]]

    assert preview["release"]["task_count"] == len(preview["tasks"])
    assert preview["release"]["case_count"] == len(expected_case_ids)
    assert actual_case_ids == expected_case_ids
    for task in preview["tasks"]:
        for published_case in task["cases"]:
            case_root = (
                RELEASE_ROOT / "tasks" / task["id"] / "score/steps/score/workdir/case-context/issues"
                / published_case["case_id"].rsplit("/", 1)[1]
            )
            for side, phase in (("before", "before"), ("after", "reference-after")):
                guide = published_case[f"{side}_video_guide"]
                presentation = json.loads((case_root / "fixtures" / phase / "presentation.json").read_text())
                assert guide == presentation.get("video_guide")
                if guide is None:
                    continue
                assert guide["summary"] and guide["chapters"], (task["name"], published_case["case_id"], side)
                times = [chapter["t"] for chapter in guide["chapters"]]
                assert times == sorted(times)
    case = preview["tasks"][0]["cases"][0]
    assert case["intent"]
    assert case["actions"]
    assert case["observed"]
    assert case["require"]
    assert case["reference_observation"]
    assert case["theory"]
    assert case["before_url"]
    assert case["after_url"]
    replay = case["replay"]
    assert replay["total_file_count"] == 8
    # Expert revisions change GT fixtures; verify the preview against the actual
    # published scripts rather than freezing the previous revision's diff count.
    task_root = RELEASE_ROOT / "tasks" / preview["tasks"][0]["id"]
    changed_files = set()
    for file in replay["files"]:
        contents = []
        for side in ("before", "after"):
            path = task_root / file[side]["path"]
            contents.append(path.read_text(encoding="utf-8") if path.is_file() else "")
            assert file[side]["content"] == contents[-1]
        if contents[0] != contents[1]:
            changed_files.add(file["name"])
    assert {file["name"] for file in replay["files"] if file["changed"]} == changed_files
    assert replay["changed_file_count"] == len(changed_files)
    assert replay["unchanged_file_count"] == len(replay["files"]) - len(changed_files)
    action = replay["files"][0]
    assert action["name"] == "action.mjs"
    assert action["role"] == "when"
    assert action["patch"].startswith("--- reproduction/action.mjs")
    assert "+" in action["patch"]
    assert "-" in action["patch"]
    assert "fixtures/before" in action["before"]["path"]
    assert "fixtures/reference-after" in action["after"]["path"]
    assert action["before"]["content"]
    assert action["after"]["content"]
    assert "<span" in action["before"]["highlighted"]
    assert "<span" in action["after"]["highlighted"]
    assert {file["role"] for file in replay["files"]} == {"when", "given", "support"}


def test_preview_serves_the_report_and_media() -> None:
    client = TestClient(create_preview_app(RELEASE_ROOT))

    assert client.get("/").status_code == 200
    assert client.get("/assets/vendor/diff2html.min.css").status_code == 200
    assert client.get("/assets/vendor/diff2html-ui-slim.min.js").status_code == 200
    release = client.get("/api/release").json()
    summary = next(task for task in release["tasks"] if task["id"] == "github__penpot__penpot__pull__10550")
    assert summary["repository"] == "penpot/penpot"
    assert summary["agent_timeout_sec"] == 3600
    assert summary["verifier_timeout_sec"] == 900
    assert summary["os"] == "linux"
    assert summary["cpus"] == 4
    assert summary["memory_mb"] == 8192
    assert summary["storage_mb"] == 20480
    assert summary["tags"] == ["ibench"]
    assert summary["has_solution"] is True
    assert summary["merge_commit_sha"]
    assert summary["has_docker_compose"] is True
    for released_task in release["tasks"]:
        task_name = released_task["name"]
        assert client.get(f"/tasks/{task_name}").status_code == 200
        task = client.get(f"/api/tasks/{task_name}").json()
        for case in task["cases"]:
            for media_url in (case["before_url"], case["after_url"]):
                response = client.get(media_url)
                assert response.status_code == 200
                assert response.headers["content-type"] == "video/webm"
                assert response.headers["cache-control"] == "no-cache"


def test_replacing_evidence_changes_its_url(tmp_path: Path) -> None:
    video = tmp_path / "before.webm"
    video.write_bytes(b"old video")
    modified = video.stat().st_mtime_ns
    before = _media_url("task", tmp_path, video)
    assert _media_url("task", tmp_path, video) == before

    video.write_bytes(b"new video")
    os.utime(video, ns=(modified + 1, modified + 1))
    assert _media_url("task", tmp_path, video) != before


def test_preview_rejects_media_path_traversal() -> None:
    client = TestClient(create_preview_app(RELEASE_ROOT))
    task_id = build_preview(RELEASE_ROOT)["tasks"][0]["id"]

    response = client.get(f"/api/media/{task_id}/%2E%2E/release.json")

    assert response.status_code == 404


def test_preview_exposes_separate_optional_video_guides() -> None:
    client = TestClient(create_preview_app(RELEASE_ROOT))
    case = client.get("/api/tasks/dashboard-member-invitation").json()["cases"][0]
    assert case["before_video_guide"]["chapters"][-1]["t"] == 9.5
    assert case["before_video_guide"] != case["after_video_guide"]
    assert any("yellow warning" in chapter.get("note", "") for chapter in case["after_video_guide"]["chapters"])
    # Guide metadata remains optional for candidates without editorial guides.
    assert _video_guide({}) is None


@pytest.mark.parametrize("guide", [
    None, "bad", {}, {"summary": ""},
    {"summary": "Guide", "cues": [{"time": 1, "text": "Legacy"}]},
    {"summary": "Guide", "chapters": [{"kind": "check", "t": -1, "note": "Wrong time"}]},
    {"summary": "Guide", "chapters": [{"kind": "check", "t": float("inf"), "note": "Wrong time"}]},
    {"summary": "Guide", "chapters": [{"kind": "check", "t": float("nan"), "note": "Wrong time"}]},
    {"summary": "Guide", "chapters": [{"kind": "check", "t": 1, "note": ""}]},
    {"summary": "Guide", "chapters": [{"kind": "step", "t": 1, "note": "Wrong field"}]},
    {"summary": "Guide", "chapters": [{"kind": "check", "t": 1, "label": "Wrong field"}]},
    {"summary": "Guide", "chapters": [{"kind": "unknown", "t": 1, "note": "Wrong kind"}]},
])
def test_invalid_optional_video_guides_do_not_break_preview(guide: object) -> None:
    assert _video_guide({"video_guide": guide}) is None


def test_video_chapters_keep_actions_claims_and_anomalies_on_the_same_frame() -> None:
    guide = {"summary": "Review the form", "chapters": [
        {"kind": "step", "t": 2.5, "label": "Submit"},
        {"kind": "check", "t": 2.5, "note": "The required-field warning is visible."},
        {"kind": "flag", "t": 2.5, "note": "An unrelated toast overlaps the sidebar."},
    ]}
    assert _video_guide({"video_guide": guide}) == guide
