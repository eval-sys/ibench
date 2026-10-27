"""Convert DSH 0.2.0-rc.2's native v4 journals to ATIF and price recorded usage."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from chinese_calendar import is_holiday
from harbor.models.trajectories import Trajectory

PRICING = {
    "provider": "deepseek-official", "model": "deepseek-flash", "currency": "USD",
    "source": "https://api-docs.deepseek.com/quick_start/pricing/", "checked_at": "2026-10-20",
    "per_million_tokens": {
        "peak": {"input": 0.30, "cached_input": 0.006, "output": 1.20},
        "off_peak": {"input": 0.15, "cached_input": 0.003, "output": 0.60},
    },
    "peak_hours_utc": [[1, 4], [6, 10]],
    "peak_days": "Monday-Friday, excluding Chinese public holidays",
    "time_source": "step/start, or assistant event time when absent",
}


def usage_metrics(usage: dict, source: dict, time: int) -> dict:
    # DSH's input is UNCACHED input. Its cache counters are disjoint; ATIF's
    # prompt count includes them. This differs from ZCode's inputTokens.
    uncached, output = usage.get("inputTokens"), usage.get("outputTokens")
    cached, written = usage.get("cacheReadTokens", 0), usage.get("cacheWriteTokens", 0)
    if any(type(value) is not int or value < 0 for value in (uncached, output, cached, written)):
        raise ValueError(f"Invalid DSH token usage: {usage}")
    result = {
        "prompt_tokens": uncached + cached + written, "completion_tokens": output, "cached_tokens": cached,
        "extra": {"usage_source": "dsh.native_session", "native_usage": usage},
    }
    if source.get("provider") != PRICING["provider"] or source.get("model") != PRICING["model"]:
        return result
    at = datetime.fromtimestamp(time / 1_000, tz=UTC)
    try:
        # Calendar dates within peak windows fall on the same UTC/China date.
        peak = at.weekday() < 5 and any(a <= at.hour < b for a, b in PRICING["peak_hours_utc"]) and not is_holiday(at.date())
    except NotImplementedError:
        result["extra"]["cost_unavailable"] = "Holiday calendar does not cover this year"
        return result
    tier = "peak" if peak else "off_peak"
    rates = PRICING["per_million_tokens"][tier]
    result["cost_usd"] = ((uncached + written) * rates["input"] + cached * rates["cached_input"] + output * rates["output"]) / 1_000_000
    result["extra"]["pricing_tier"] = tier
    return result


def _text(blocks: list[dict]) -> str:
    return "\n".join(block.get("text", json.dumps(block, ensure_ascii=False)) for block in blocks)


def _read(path: Path) -> tuple[dict, list[dict], bool]:
    lines = path.read_text().splitlines()
    header = json.loads(lines[0])
    if header.get("type") != "session" or header.get("version") != 4:
        raise ValueError(f"Unsupported DSH native session header: {path}")
    events, truncated = [], False
    for index, line in enumerate(lines[1:], 1):
        try:
            event = json.loads(line)
        except ValueError:
            if index != len(lines) - 1:
                raise
            truncated = True
            break
        if event.get("seq") != len(events):
            raise ValueError(f"Non-contiguous DSH journal: {path}:{index + 1}")
        events.append(event)
    return header, events, truncated


def _convert(path: Path, header: dict, events: list[dict], truncated: bool, version: str) -> dict:
    inherited = [event["seq"] for event in events if event["type"] == "session/end-seed" and event["data"].get("inherited")]
    if header.get("isSeeded") and not inherited:
        raise ValueError(f"Seeded DSH session lacks its inheritance boundary: {path}")
    cut = max(inherited, default=-1)
    steps, calls, starts, route = [], {}, {}, {}
    for event in events:
        kind, payload = event["type"], event["data"]
        if kind == "compaction/summary":
            if not payload.get("llmStreamCall") and payload.get("usage") is None:
                continue
            payload = {
                **payload, "turn": -1, "step": event["seq"],
                "message": {
                    "content": [{"type": "text", "text": payload["summary"]}],
                    "source": {"provider": payload["provider"], "model": payload["model"]},
                },
            }
            kind = "assistant/message"
        if kind == "request/header":
            route = payload["header"]["config"]
        elif kind == "request/context":
            route = payload
        elif kind == "step/start":
            starts[payload["turn"], payload["step"]] = event["time"]
        elif kind in {"user/message", "system/message", "developer/message", "assistant/message", "assistant/attempt"}:
            attempt = kind == "assistant/attempt"
            message = {"content": [], "source": route} if attempt else payload if kind == "user/message" else payload["message"]
            blocks = message.get("content", [])
            source = "agent" if kind.startswith("assistant/") else "user" if kind == "user/message" else "system"
            step = {
                "step_id": len(steps) + 1, "source": source,
                "timestamp": datetime.fromtimestamp(event["time"] / 1_000, tz=UTC).isoformat(),
                "message": _text([b for b in blocks if b["type"] not in {"tool-call", "reasoning"}]),
                "extra": {"native_seq": event["seq"], "native_event_type": event["type"], "message_id": message.get("id"), "native_source": message.get("source")},
            }
            if event["seq"] < cut:
                step["is_copied_context"] = True
            if source == "agent":
                model_source = message.get("source", {})
                step["model_name"] = f"{model_source.get('provider', 'unknown')}/{model_source.get('model', 'unknown')}"
                step["llm_call_count"] = 1
                reasoning = "\n".join(b["text"] for b in blocks if b["type"] == "reasoning")
                if reasoning:
                    step["reasoning_content"] = reasoning
                tool_calls = [
                    {"tool_call_id": block["id"], "function_name": block["name"], "arguments": json.loads(block["arguments"]), "extra": {"raw_arguments": block["arguments"]}}
                    for block in blocks if block["type"] == "tool-call"
                ]
                if tool_calls:
                    step["tool_calls"] = tool_calls
                for call in tool_calls:
                    calls[call["tool_call_id"]] = step
                usage = payload.get("usage")
                if attempt:
                    step["extra"]["native_attempt"] = True
                    usage_chunks = [entry["chunk"]["usage"] for entry in payload.get("stream", []) if entry.get("type") == "chunk" and entry.get("chunk", {}).get("type") == "usage"]
                    usage = usage_chunks[-1] if usage_chunks else None
                if usage is not None and not step.get("is_copied_context"):
                    time = starts.get((payload["turn"], payload["step"]), event["time"])
                    step["metrics"] = usage_metrics(usage, model_source, time)
            steps.append(step)
        elif kind == "tool/result":
            message = payload["message"]
            call_id = message["source"]["callId"]
            if call_id not in calls:
                raise ValueError(f"DSH result has no recorded tool call: {call_id}")
            calls[call_id].setdefault("observation", {"results": []})["results"].append({
                "source_call_id": call_id, "content": _text(message.get("content", [])),
                "extra": {"is_error": message.get("isError", False)},
            })
    agent_steps = [step for step in steps if step["source"] == "agent" and not step.get("is_copied_context")]
    measured = [step["metrics"] for step in agent_steps if "metrics" in step]
    final = {"total_steps": len(steps)}
    if measured or not agent_steps:
        final.update({f"total_{key}": sum(metrics[key] for metrics in measured) for key in ("prompt_tokens", "completion_tokens", "cached_tokens")})
        if all("cost_usd" in metrics for metrics in measured):
            final["total_cost_usd"] = sum(metrics["cost_usd"] for metrics in measured)
    final["extra"] = {
        "usage_source": "dsh.native_session", "requests_with_usage": len(measured),
        "requests_without_usage": len(agent_steps) - len(measured),
        "cost_source": "published_price_estimate" if "total_cost_usd" in final else "unavailable",
        "cost_pricing": PRICING,
    }
    return {
        "schema_version": "ATIF-v1.7", "session_id": header["id"], "trajectory_id": header["id"],
        "agent": {"name": "dsh", "version": version, "model_name": agent_steps[-1]["model_name"] if agent_steps else None},
        "steps": steps, "final_metrics": final,
        "extra": {"native_log": str(path), "native_log_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "truncated_final_line": truncated},
    }


def build_trajectory(logs_dir: Path, *, session_id: str | None = None, version: str = "0.2.0-rc.2") -> Trajectory | None:
    sessions = {}
    for path in sorted((logs_dir / "dsh-sessions").rglob("*.jsonl")):
        header, events, truncated = _read(path)
        if header["id"] in sessions:
            raise ValueError(f"Duplicate DSH session: {header['id']}")
        sessions[header["id"]] = (path, header, events, truncated)
    if not sessions:
        return None
    roots = [sid for sid, (_, header, _, _) in sessions.items() if not header.get("parentSession")]
    if session_id is None:
        if len(roots) != 1:
            raise ValueError(f"Cannot identify main DSH session: {roots}")
        session_id = roots[0]
    if session_id not in sessions:
        raise ValueError(f"Missing main DSH session journal: {session_id}")

    def embed(sid: str, ancestors: set[str]) -> dict:
        if sid in ancestors:
            raise ValueError("Cycle in DSH parent sessions")
        path, header, events, truncated = sessions[sid]
        data = _convert(path, header, events, truncated, version)
        data["extra"]["native_log"] = str(path.relative_to(logs_dir))
        children = [embed(child, ancestors | {sid}) for child, (_, h, _, _) in sessions.items() if h.get("parentSession") == sid]
        if children:
            data["subagent_trajectories"] = children
        final = data["final_metrics"]
        final["extra"]["requests_with_usage_including_subagents"] = final["extra"]["requests_with_usage"] + sum(child["final_metrics"]["extra"]["requests_with_usage_including_subagents"] for child in children)
        for key in ("prompt_tokens", "completion_tokens", "cached_tokens", "cost_usd"):
            values = [final.get(f"total_{key}"), *(child["final_metrics"]["extra"].get(f"total_{key}_including_subagents") for child in children)]
            final["extra"][f"total_{key}_including_subagents"] = sum(values) if all(value is not None for value in values) else None
        return data

    return Trajectory.model_validate(embed(session_id, set()))
