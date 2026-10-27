import copy
import json
import sys

import pytest
from harbor.models.trajectories import Trajectory

from ibench.utils.qwen import backfill_qwen, qwen_usage
from ibench.utils.usage import main


def trajectory(identity="main", *, prompt=1_000_000, cached=800_000, completion=100_000):
    return {
        "schema_version": "ATIF-v1.7",
        "session_id": identity,
        "agent": {"name": "codex", "version": "test", "model_name": "qwen3.8-max"},
        "steps": [
            {
                "step_id": 1,
                "source": "agent",
                "message": "Original reasoning",
                "model_name": "qwen3.8-max",
                "llm_call_count": 1,
                "metrics": {
                    "prompt_tokens": prompt,
                    "completion_tokens": completion,
                    "cached_tokens": cached,
                    "extra": {"reasoning_output_tokens": 50_000, "cache_write_input_tokens": 0},
                },
            }
        ],
        "final_metrics": {
            "total_prompt_tokens": prompt,
            "total_completion_tokens": completion,
            "total_cached_tokens": cached,
            "extra": {"original": True},
        },
        "extra": {"original": True},
    }


def test_official_prices_charge_cached_input_once_and_reasoning_with_output():
    data = trajectory()
    report = backfill_qwen(data)
    # 200K uncached * $2 + 800K cached * $0.25 + 100K output * $6.
    assert report["including_subagents"]["cost_usd"] == pytest.approx(1.2)
    assert data["steps"][0]["metrics"]["cost_usd"] == pytest.approx(1.2)
    assert data["final_metrics"]["total_cost_usd"] == pytest.approx(1.2)
    assert data["final_metrics"]["extra"]["cost_pricing"]["provider"] == "qwencloud"
    assert data["final_metrics"]["extra"]["original"] is True
    assert data["steps"][0]["message"] == "Original reasoning"
    assert data["extra"] == {"original": True}
    Trajectory.model_validate(data)
    before = copy.deepcopy(data)
    backfill_qwen(data)
    assert data == before


def test_children_are_included_without_recharging_copied_context():
    data = trajectory()
    child = trajectory("child", prompt=2_000_000)
    copied = copy.deepcopy(child["steps"][0])
    copied.update(step_id=2, is_copied_context=True)
    child["steps"].append(copied)
    data["subagent_trajectories"] = [child]
    report = backfill_qwen(data)
    assert report["main"]["cost_usd"] == pytest.approx(1.2)
    assert report["including_subagents"]["cost_usd"] == pytest.approx(4.4)
    assert report["including_subagents"]["requests"] == 2
    assert child["final_metrics"]["total_cost_usd"] == pytest.approx(3.2)
    assert "cost_usd" not in copied["metrics"]


def test_interrupted_request_is_unknown_instead_of_free():
    data = trajectory()
    data["steps"].append({"step_id": 2, "source": "agent", "model_name": "qwen3.8-max", "message": "Incomplete"})
    report = backfill_qwen(data)
    assert report["steps_without_usage"] == 1
    assert report["including_subagents"]["requests"] == 1
    assert "metrics" not in data["steps"][1]


def test_codex_zero_cache_serialized_as_none_is_priced_as_uncached():
    data = trajectory(cached=0)
    data["steps"][0]["metrics"].pop("cached_tokens")
    report = backfill_qwen(data)
    assert report["main"]["cost_usd"] == pytest.approx(2.6)
    assert report["steps_without_usage"] == 0
    assert "cached_tokens" not in data["steps"][0]["metrics"]


def test_native_response_tail_is_billed_once_without_inventing_a_step(tmp_path):
    directory = tmp_path / "sessions"
    directory.mkdir()
    path = directory / "rollout.jsonl"
    events = [
        {
            "type": "token_usage_record",
            "payload": {
                "session_id": "main",
                "response_id": response,
                "usage": {"input_tokens": 1_000_000, "cached_input_tokens": 800_000, "output_tokens": 100_000},
                "thread_token_usage": {"input_tokens": 999_000_000},
            },
        }
        for response in ["response-1", "response-1", "response-2"]
    ]
    path.write_text("\n".join(json.dumps(e) for e in events) + '\n{"unfinished":')
    native = qwen_usage(tmp_path)
    data = trajectory()
    steps = copy.deepcopy(data["steps"])
    report = backfill_qwen(data, native)
    assert report["main"]["requests"] == 2
    assert report["main"]["cost_usd"] == pytest.approx(2.4)
    assert report["requests_without_step"] == 1
    assert report["invalid_jsonl_lines"] == 1
    assert data["final_metrics"]["total_prompt_tokens"] == 2_000_000
    steps[0]["metrics"]["cost_usd"] = pytest.approx(1.2)
    assert data["steps"] == steps
    before = copy.deepcopy(data)
    backfill_qwen(data, native)
    assert data == before


def test_conflicting_provider_response_usage_is_rejected(tmp_path):
    directory = tmp_path / "sessions"
    directory.mkdir()
    events = [
        {
            "type": "token_usage_record",
            "payload": {
                "session_id": "main",
                "response_id": "same",
                "usage": {"input_tokens": tokens},
            },
        }
        for tokens in [100, 200]
    ]
    (directory / "rollout.jsonl").write_text("\n".join(json.dumps(e) for e in events))
    with pytest.raises(ValueError, match="Conflicting"):
        qwen_usage(tmp_path)


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d["agent"].update(model_name="gpt-6-astra"),
        lambda d: d["steps"][0].update(model_name="other-model"),
        lambda d: d["steps"][0]["metrics"].update(cached_tokens=1_000_001),
        lambda d: d["steps"][0]["metrics"].update(prompt_tokens=-1),
        lambda d: d["steps"][0]["metrics"]["extra"].update(cache_write_input_tokens=100),
        lambda d: d["final_metrics"].update(total_prompt_tokens=2_000_000),
        lambda d: d.update(subagent_trajectories=[trajectory()]),
    ],
)
def test_invalid_or_unpriced_usage_leaves_the_trajectory_unchanged(change):
    data = trajectory()
    change(data)
    before = copy.deepcopy(data)
    with pytest.raises(ValueError):
        backfill_qwen(data)
    assert data == before


def test_run_cli_is_read_only_by_default_and_writes_costs_only_when_requested(tmp_path, monkeypatch, capsys):
    path = tmp_path / "jobs/solve/trial/steps/solve/agent/trajectory.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(trajectory()))
    (tmp_path / "results.json").write_text(
        json.dumps({"trials": [{"task_id": "task", "solver_trial": "jobs/solve/trial"}]})
    )
    original = path.read_bytes()
    output = tmp_path / "usage-summary.json"
    monkeypatch.setattr(sys, "argv", ["usage", str(tmp_path), "--output", str(output)])
    main()
    assert path.read_bytes() == original
    assert json.loads(output.read_text())["totals"]["cost_usd"] == pytest.approx(1.2)
    monkeypatch.setattr(sys, "argv", ["usage", str(tmp_path), "--write"])
    main()
    assert json.loads(path.read_text())["final_metrics"]["total_cost_usd"] == pytest.approx(1.2)
    capsys.readouterr()
