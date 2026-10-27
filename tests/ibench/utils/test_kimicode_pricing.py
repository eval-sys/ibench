import pytest
from harbor.models.trajectories import Trajectory

from ibench.utils.kimicode.pricing import MODEL, price_data, price_trajectory


def trajectory(*steps: dict) -> Trajectory:
    return Trajectory.model_validate({
        "schema_version": "ATIF-v1.7", "session_id": "pricing-test",
        "agent": {"name": "kimi-code", "version": "test", "model_name": MODEL},
        "steps": [
            {"step_id": i, "source": "agent", "message": "", "model_name": MODEL, **step}
            for i, step in enumerate(steps, 1)
        ],
        "final_metrics": {},
    })


def test_cached_input_is_not_charged_again_as_uncached_input():
    item = trajectory({"metrics": {
        "prompt_tokens": 1_000_000, "completion_tokens": 100_000, "cached_tokens": 800_000,
        "extra": {"cache_read_input_tokens": 800_000},
    }})
    price_trajectory(item)
    assert item.final_metrics.total_cost_usd == pytest.approx(2.34)
    assert item.steps[0].metrics.cost_usd == pytest.approx(2.34)
    assert item.final_metrics.extra["cost_pricing"]["provider"] == "fireworks"


def test_copied_context_is_excluded_and_repricing_is_idempotent():
    item = trajectory(
        {"metrics": {"prompt_tokens": 1_000_000, "completion_tokens": 0}},
        {"metrics": {"prompt_tokens": 100_000_000, "completion_tokens": 0}, "is_copied_context": True},
    )
    price_trajectory(item)
    price_trajectory(item)
    assert item.final_metrics.total_cost_usd == 3
    assert item.steps[1].metrics.cost_usd is None


def test_other_provider_or_model_prevents_partial_pricing():
    item = trajectory(
        {"metrics": {"prompt_tokens": 1_000_000, "completion_tokens": 0}},
        {"model_name": "moonshot/kimi-k3", "metrics": {"prompt_tokens": 100, "completion_tokens": 20}},
    )
    price_trajectory(item)
    assert item.final_metrics.total_cost_usd is None
    assert all(s.metrics.cost_usd is None for s in item.steps)


def test_invalid_cache_counts_do_not_write_partial_costs():
    item = trajectory(
        {"metrics": {"prompt_tokens": 100, "completion_tokens": 10}},
        {"metrics": {"prompt_tokens": 100, "completion_tokens": 10, "cached_tokens": 101}},
    )
    with pytest.raises(ValueError, match="Invalid token usage"):
        price_trajectory(item)
    assert item.final_metrics.total_cost_usd is None
    assert all(s.metrics.cost_usd is None for s in item.steps)


def test_cost_only_preserves_original_data_and_includes_child_usage():
    parent = trajectory({"metrics": {"prompt_tokens": 1_000_000, "completion_tokens": 0}}).to_json_dict()
    child = trajectory({"metrics": {"prompt_tokens": 1_000_000, "completion_tokens": 100_000}}).to_json_dict()
    child["trajectory_id"] = "pricing-test/child"
    parent["subagent_trajectories"] = [child]
    parent["extra"] = {"offline_conversion": {"historical_provenance": "retain verbatim"}}
    parent["steps"][0]["extra"] = {"original_payload": [1, 2, 3]}
    assert price_data(parent) == 7.5
    assert parent["final_metrics"]["total_cost_usd"] == 3
    assert child["final_metrics"]["total_cost_usd"] == 4.5
    assert parent["extra"] == {"offline_conversion": {"historical_provenance": "retain verbatim"}}
    assert parent["steps"][0]["extra"] == {"original_payload": [1, 2, 3]}
    assert price_data(parent) == 7.5
