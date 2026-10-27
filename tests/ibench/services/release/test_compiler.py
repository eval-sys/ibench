import json
from pathlib import Path

import pytest

from ibench.services.release.compiler import compile_prompt, load_release, prepare_solve


def test_prompt_keeps_manifest_case_order_and_source_action_order(tmp_path: Path) -> None:
    context = tmp_path / "score/steps/score/workdir/case-context"
    cases = []
    for number in (9, 2):
        root = context / "issues" / str(number)
        root.mkdir(parents=True)
        (root / "user-task.json").write_text(
            json.dumps({"intent": f"Goal {number}", "actions": ["Zulu first", "Alpha second"]})
        )
        for fixture in ("before", "reference-after"):
            presentation = root / "fixtures" / fixture / "presentation.json"
            presentation.parent.mkdir(parents=True)
            presentation.write_text(json.dumps({
                "video_guide": {"summary": "PRIVATE_VIDEO_GUIDE", "chapters": [
                    {"kind": "check", "t": 6, "note": "PRIVATE_REFERENCE_OUTCOME"},
                ]},
            }))
        cases.append(
            {
                "case_id": str(number),
                "input": f"/workspace/case-context/issues/{number}",
                "replay_root": f"/logs/{number}",
                "verdict_template": f"/logs/{number}/verdict.json",
                "capture": f"/workspace/case-context/issues/{number}/capture-after.sh",
            }
        )
    (context / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "ibench-score-manifest/v1",
                "task_id": "task",
                "validate": "/workspace/case-context/validate.sh",
                "cases": cases,
            }
        )
    )
    result = compile_prompt(tmp_path, "intent-actions")
    assert result.index("Goal 9") < result.index("Goal 2")
    assert result.count("1. Zulu first\n2. Alpha second") == 2
    intentions = compile_prompt(tmp_path, "intent")
    assert "Goal 9" in intentions and "Goal 2" in intentions and "Zulu" not in intentions
    for prompt in (result, intentions):
        assert "PRIVATE_VIDEO_GUIDE" not in prompt
        assert "PRIVATE_REFERENCE_OUTCOME" not in prompt


@pytest.mark.parametrize("profile", ["intent", "intent-actions"])
def test_compiled_solver_excludes_judge_and_replay_material(tmp_path: Path, profile: str) -> None:
    root = Path(__file__).resolve().parents[4]
    manifest = load_release(root, ("photo-map-panning",))
    task = manifest.tasks[0]
    compiled = prepare_solve(root, task, tmp_path / "solve", profile)
    assert not list(compiled.rglob("rubric.json"))
    assert not list(compiled.rglob("action.mjs"))
