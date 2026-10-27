import copy
import json

import pytest

from ibench.utils.usage import backfill_zcode, dsh_usage, totals, zcode_usage


def log(tmp_path, events):
    path = tmp_path / "events.jsonl"
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    return path


def request(kind, request_id="r1", session="main", actor="main", usage=None):
    payload = {
        "type": f"model_request_{kind}", "requestId": request_id, "sessionId": session,
        "turnId": "turn", "modelId": "GLM-5.3-Flash", "modelCall": {"actorKind": actor},
    }
    if usage is not None:
        payload["usage"] = usage
    return {"type": "session.updated", "payload": payload}


def message(message_id="m1", session="main"):
    return {
        "type": "model.streaming", "sessionId": session, "turnId": "turn",
        "timestamp": 1_000 * int(message_id[1:]),
        "payload": {"kind": "start", "assistantMessageId": message_id},
    }


def tokens(prompt=1_000_000, cached=800_000, output=100_000):
    return {"inputTokens": prompt, "cacheReadTokens": cached, "outputTokens": output, "reasoningTokens": output}


def trajectory(count=1):
    return {
        "agent": {"name": "zcode", "model_name": "GLM-5.3-Flash"},
        "steps": [
            {"source": "agent", "message": "preserve this", "extra": {"original": True},
             "timestamp": f"1970-01-01T00:00:{i:02d}+00:00"}
            for i in range(1, count + 1)
        ],
        "final_metrics": {"total_steps": count, "extra": {"original": True}},
    }


def test_provider_records_deduplicated_without_turn_or_snapshot_double_counting(tmp_path):
    completed = request("completed", usage=tokens())
    completed["eventId"] = "completed"
    path = log(tmp_path, [
        request("started"), message(), completed, completed,
        {**completed, "eventId": "different-event-same-request"},
        {"type": "turn.completed", "payload": {"usage": tokens()}},
        {"type": "session.updated", "payload": {"usage": tokens()}},
    ])
    usage = zcode_usage(path)
    data = trajectory()
    report = backfill_zcode(data, usage)
    assert report["main"]["requests"] == 1
    assert data["final_metrics"]["total_prompt_tokens"] == 1_000_000
    # Reasoning is already part of output; cached tokens are part of input.
    assert data["final_metrics"]["total_cost_usd"] == pytest.approx(0.104)
    assert data["steps"][0]["metrics"]["cost_usd"] == pytest.approx(0.104)
    before = copy.deepcopy(data)
    backfill_zcode(data, usage)
    assert data == before
    assert data["steps"][0]["message"] == "preserve this"
    assert data["steps"][0]["extra"] == {"original": True}


def test_concurrent_child_sessions_keep_step_ownership_and_own_totals(tmp_path):
    usage = zcode_usage(log(tmp_path, [
        request("started"), message(),
        request("started", "r2", "child", "subagent"), message("m2", "child"),
        request("completed", "r2", "child", "subagent", tokens()),
        request("completed", usage=tokens()),
    ]))
    data = trajectory(2)
    backfill_zcode(data, usage)
    assert data["steps"][0]["metrics"]["extra"]["actor_kind"] == "main"
    assert data["steps"][1]["metrics"]["extra"]["actor_kind"] == "subagent"
    assert data["final_metrics"]["total_prompt_tokens"] == 1_000_000
    assert data["final_metrics"]["extra"]["total_prompt_tokens_including_subagents"] == 2_000_000
    assert data["final_metrics"]["extra"]["total_cost_usd_including_subagents"] == pytest.approx(0.208)


def test_timeout_keeps_recorded_usage_and_marks_missing_request(tmp_path):
    path = log(tmp_path, [
        request("started"), message(), request("completed", usage=tokens()),
        request("started", "r2"), message("m2"),
    ])
    with path.open("a") as stream:
        stream.write('{"interrupted":')
    usage = zcode_usage(path)
    data = trajectory(2)
    report = backfill_zcode(data, usage)
    assert report["requests_without_usage"] == 1
    assert report["invalid_jsonl_lines"] == 1
    assert "metrics" not in data["steps"][1]
    assert report["main"]["cost_usd"] == pytest.approx(0.104)


def test_retries_are_separate_billable_requests(tmp_path):
    usage = zcode_usage(log(tmp_path, [
        request("started"), message(), request("completed", usage=tokens()),
        request("started", "r2"), message(), request("completed", "r2", usage=tokens()),
    ]))
    data = trajectory()
    backfill_zcode(data, usage)
    assert data["steps"][0]["metrics"]["prompt_tokens"] == 2_000_000
    assert data["final_metrics"]["total_prompt_tokens"] == 2_000_000


def test_longer_timeout_log_tail_is_in_total_without_shifting_existing_steps(tmp_path):
    usage = zcode_usage(log(tmp_path, [
        request("started"), message(), request("completed", usage=tokens()),
        request("started", "r2"), message("m2"), request("completed", "r2", usage=tokens(output=0)),
    ]))
    data = trajectory(2)
    data["steps"] = data["steps"][1:]
    report = backfill_zcode(data, usage)
    assert report["requests_without_step"] == 1
    assert data["steps"][0]["metrics"]["completion_tokens"] == 0
    assert data["final_metrics"]["total_completion_tokens"] == 100_000


def test_ambiguous_step_binding_retains_total_without_inventing_step_usage(tmp_path):
    usage = zcode_usage(log(tmp_path, [
        request("started"), message(), message("m2"), request("completed", usage=tokens()),
    ]))
    data = trajectory(2)
    report = backfill_zcode(data, usage)
    assert report["requests_without_step"] == 1
    assert all("metrics" not in step for step in data["steps"])
    assert report["main"]["prompt_tokens"] == 1_000_000


@pytest.mark.parametrize("usage", [tokens(cached=1_000_001), tokens(prompt=-1), tokens(output=None)])
def test_invalid_provider_usage_is_rejected(tmp_path, usage):
    with pytest.raises(ValueError):
        zcode_usage(log(tmp_path, [request("completed", usage=usage)]))


def test_conflicting_duplicate_request_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Conflicting"):
        zcode_usage(log(tmp_path, [request("completed", usage=tokens()), request("completed", usage=tokens(output=0))]))


def test_dsh_context_snapshots_are_not_summed_or_priced(tmp_path):
    report = dsh_usage(log(tmp_path, [
        {"event_type": "session_update", "payload": {"update": {
            "sessionUpdate": "usage_update", "used": used, "size": 1_000_000,
        }}}
        for used in [10_000, 30_000, 20_000]
    ]))
    assert report["status"] == "billing_usage_unavailable"
    assert report["cost_usd"] is None
    assert report["context"]["peak_used_tokens"] == 30_000
    assert report["context"]["last_used_tokens"] == 20_000
    assert "prompt_tokens" not in report


def test_run_totals_sum_request_counts_instead_of_counting_tasks():
    assert totals([{"prompt_tokens": 10, "cached_tokens": 0, "completion_tokens": 2, "cost_usd": 1, "requests": 8}] * 2) == {
        "prompt_tokens": 20, "cached_tokens": 0, "completion_tokens": 4, "cost_usd": 2, "requests": 16,
    }
