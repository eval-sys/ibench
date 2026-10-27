import asyncio
import json
from datetime import UTC, datetime

import pytest
from harbor.models.agent.context import AgentContext

from ibench.agents.dsh import Dsh
from ibench.utils.dsh import build_trajectory, usage_metrics

SOURCE = {"kind": "model", "provider": "deepseek-official", "model": "deepseek-flash"}
USAGE = {"inputTokens": 100, "cacheReadTokens": 900, "outputTokens": 20, "totalTokens": 1020}
TIME = int(datetime(2026, 10, 19, 2, tzinfo=UTC).timestamp() * 1000)


def assistant(call=False, usage=USAGE):
    return {
        "turn": 0, "step": 0, "message": {
            "id": "msg1", "role": "assistant", "source": SOURCE,
            "content": [{"type": "reasoning", "text": "Inspect the file"}, {"type": "text", "text": "Done"}]
            + ([{"type": "tool-call", "id": "call1", "name": "bash", "arguments": '{"command":"pwd"}'}] if call else []),
        }, "usage": usage, "stream": [],
    }


def journal(tmp_path, session_id="main", events=None, parent=None, seeded=False):
    path = tmp_path / "dsh-sessions" / session_id / "v4.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {"type": "session", "version": 4, "id": session_id, "createdAt": TIME, "isSeeded": seeded}
    if parent:
        header["parentSession"] = parent
    events = events if events is not None else [("step/start", {"turn": 0, "step": 0}), ("assistant/message", assistant())]
    path.write_text("\n".join(json.dumps(row) for row in [header, *[
        {"type": kind, "seq": i, "time": TIME + i, "data": data} for i, (kind, data) in enumerate(events)
    ]]) + "\n")
    return path


def test_disjoint_dsh_usage_normalizes_cache_and_prices_it_once():
    metrics = usage_metrics(USAGE, SOURCE, TIME)
    assert metrics["prompt_tokens"] == 1000
    assert metrics["cached_tokens"] == 900
    assert metrics["completion_tokens"] == 20
    assert metrics["cost_usd"] == pytest.approx(0.0000594)
    assert metrics["extra"]["pricing_tier"] == "peak"


@pytest.mark.parametrize("date,hour,tier", [
    ("2026-10-19", 1, "peak"), ("2026-10-19", 4, "off_peak"),
    ("2026-10-19", 6, "peak"), ("2026-10-19", 10, "off_peak"),
    ("2026-10-18", 2, "off_peak"), ("2026-10-01", 2, "off_peak"),
    ("2026-10-10", 2, "off_peak"),  # Saturday remains off-peak on a make-up workday.
])
def test_pricing_uses_utc_windows_weekends_and_chinese_holidays(date, hour, tier):
    at = datetime.fromisoformat(date).replace(hour=hour, tzinfo=UTC)
    assert usage_metrics(USAGE, SOURCE, int(at.timestamp() * 1000))["extra"]["pricing_tier"] == tier


def test_unknown_provider_preserves_tokens_without_using_official_rates():
    metrics = usage_metrics(USAGE, {**SOURCE, "provider": "other"}, TIME)
    assert metrics["prompt_tokens"] == 1000
    assert "cost_usd" not in metrics


def test_native_tool_call_and_result_form_one_agent_step(tmp_path):
    journal(tmp_path, events=[
        ("assistant/message", assistant(call=True)),
        ("tool/result", {"turn": 0, "step": 0, "message": {
            "role": "tool", "source": {"kind": "tool", "callId": "call1"},
            "content": [{"type": "text", "text": "/workspace/app"}],
        }}),
    ])
    item = build_trajectory(tmp_path)
    assert len(item.steps) == 1
    step = item.steps[0]
    assert step.reasoning_content == "Inspect the file"
    assert step.tool_calls[0].arguments == {"command": "pwd"}
    assert step.observation.results[0].source_call_id == "call1"
    assert step.metrics.prompt_tokens == 1000
    assert item.final_metrics.total_cost_usd == pytest.approx(0.0000594)


def test_children_exclude_inherited_usage_and_include_own_usage_in_rollup(tmp_path):
    journal(tmp_path)
    journal(tmp_path, "child", parent="main", seeded=True, events=[
        ("assistant/message", assistant()),
        ("session/end-seed", {"inherited": True}),
        ("assistant/message", assistant()),
    ])
    item = build_trajectory(tmp_path)
    child = item.subagent_trajectories[0]
    assert child.steps[0].is_copied_context
    assert child.steps[0].metrics is None
    assert child.final_metrics.total_prompt_tokens == 1000
    assert item.final_metrics.total_prompt_tokens == 1000
    assert item.final_metrics.extra["total_prompt_tokens_including_subagents"] == 2000
    assert item.final_metrics.extra["total_cost_usd_including_subagents"] == pytest.approx(0.0001188)


def test_missing_usage_is_unavailable_not_free(tmp_path):
    journal(tmp_path, events=[("assistant/message", assistant(usage=None))])
    item = build_trajectory(tmp_path)
    assert item.final_metrics.total_prompt_tokens is None
    assert item.final_metrics.total_cost_usd is None
    assert item.final_metrics.extra["requests_without_usage"] == 1


def test_timeout_truncated_final_line_keeps_completed_usage(tmp_path):
    path = journal(tmp_path)
    with path.open("a") as stream:
        stream.write('{"type":"assistant/message"')
    item = build_trajectory(tmp_path)
    assert item.extra["truncated_final_line"]
    assert item.final_metrics.total_prompt_tokens == 1000


def test_agent_context_and_atif_both_receive_inclusive_usage(tmp_path):
    journal(tmp_path)
    journal(tmp_path, "child", parent="main")
    (tmp_path / "acp-summary.json").write_text(json.dumps({"session": {"sessionId": "main"}}))
    context = AgentContext()
    Dsh(logs_dir=tmp_path).populate_context_post_run(context)
    assert context.n_input_tokens == 2000
    assert context.n_cache_tokens == 1800
    assert context.n_output_tokens == 40
    assert context.cost_usd == pytest.approx(0.0001188)
    assert context.model_usage["deepseek-official/deepseek-flash"].n_input_tokens == 2000
    saved = json.loads((tmp_path / "trajectory.json").read_text())
    assert saved["final_metrics"]["total_prompt_tokens"] == 1000


def test_attempt_usage_is_counted_once_from_final_stream_usage(tmp_path):
    journal(tmp_path, events=[
        ("request/context", SOURCE),
        ("assistant/attempt", {"turn": 0, "step": 0, "stream": [
            {"type": "chunk", "time": TIME, "chunk": {"type": "usage", "usage": USAGE}},
        ]}),
    ])
    item = build_trajectory(tmp_path)
    assert item.steps[0].extra["native_attempt"]
    assert item.final_metrics.total_prompt_tokens == 1000
    assert item.final_metrics.total_cost_usd == pytest.approx(0.0000594)


def test_compaction_model_usage_is_included(tmp_path):
    journal(tmp_path, events=[
        ("assistant/message", assistant()),
        ("compaction/summary", {
            "summary": "A shorter conversation", "provider": "deepseek-official", "model": "deepseek-flash",
            "llmStreamCall": True, "usage": USAGE,
        }),
    ])
    item = build_trajectory(tmp_path)
    assert item.steps[1].extra["native_event_type"] == "compaction/summary"
    assert item.final_metrics.total_prompt_tokens == 2000
    assert item.final_metrics.total_cost_usd == pytest.approx(0.0001188)


def test_usage_cli_reads_native_journals_and_keeps_results_unchanged(tmp_path, monkeypatch):
    from ibench.utils.usage import main

    trial = "jobs/solve/trial"
    agent = tmp_path / trial / "steps/solve/agent"
    journal(agent)
    journal(agent, "child", parent="main")
    (agent / "trajectory.json").write_text(json.dumps({"agent": {"name": "dsh"}}))
    results = json.dumps({"trials": [{"task_id": "task", "solver_trial": trial, "rewards": {"reward": 1}}]})
    (tmp_path / "results.json").write_text(results)
    output = tmp_path / "usage-summary.json"
    monkeypatch.setattr("sys.argv", ["usage", str(tmp_path), "--write", "--output", str(output)])
    main()
    report = json.loads(output.read_text())
    assert report["totals"]["requests"] == 2
    assert report["totals"]["prompt_tokens"] == 2000
    assert report["pricing"]["provider"] == "deepseek-official"
    assert (tmp_path / "results.json").read_text() == results


def test_install_configures_real_native_persistence_in_archived_agent_directory(tmp_path, monkeypatch):
    from harbor.agents.installed.acp import AcpAgent

    captured = {}

    async def upload(self, environment, **kwargs):
        captured["patch"] = json.loads(kwargs["content"])

    async def noop(*args, **kwargs):
        pass

    monkeypatch.setattr(Dsh, "_upload_config_text", upload)
    monkeypatch.setattr(Dsh, "exec_as_agent", noop)
    monkeypatch.setattr(AcpAgent, "install", noop)
    asyncio.run(Dsh(logs_dir=tmp_path).install(None))
    entries = {entry["id"]: entry for entry in captured["patch"]}
    assert entries["session-persistence-jsonl"]["config"] == {"root": "/logs/agent/dsh-sessions", "compression": "none"}
    assert entries["session-log-deepseek"]["disabled"] is True
