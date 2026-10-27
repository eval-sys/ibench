"""Summarize archived ZCode/DSH/Qwen usage; optionally backfill recorded costs.

Usage: uv run python -m ibench.utils.usage runs/RUN [--write] [--output report.json]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from harbor.models.trajectories import Trajectory

from ibench.utils.dsh import build_trajectory as build_dsh_trajectory
from ibench.utils.qwen import backfill_qwen, qwen_usage

GLM_PRICING = {
    "provider": "z.ai",
    "model": "GLM-5.3-Flash",
    "source": "https://docs.z.ai/guides/overview/pricing",
    "checked_at": "2026-10-20",
    "currency": "USD",
    "per_million_tokens": {"input": 0.15, "cached_input": 0.03, "output": 0.50},
}
USAGE_SOURCE = "zcode.model_request_completed"
TOKEN_FIELDS = {
    "prompt_tokens": "inputTokens",
    "completion_tokens": "outputTokens",
    "cached_tokens": "cacheReadTokens",
}


def events(path: Path, coverage: dict):
    """Read complete JSONL events and count damaged lines left by interrupted runs."""
    seen = set()
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                coverage["invalid_jsonl_lines"] += 1
                continue
            if not isinstance(event, dict):
                raise ValueError(f"Non-object event in {path}")
            event_id = event.get("eventId")
            if event_id:
                if event_id in seen:
                    continue
                seen.add(event_id)
            yield event


def zcode_usage(path: Path) -> dict:
    """Use provider request records, never turn totals or UI usage snapshots."""
    coverage = {"invalid_jsonl_lines": 0}
    active, requests, completed, messages = {}, {}, {}, {}
    for event in events(path, coverage):
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        kind = payload.get("type") if event.get("type") == "session.updated" else None
        if kind == "model_request_started":
            request_id = payload["requestId"]
            active[payload.get("sessionId"), payload.get("turnId")] = request_id
            requests.setdefault(request_id, set())
        elif event.get("type") == "model.streaming":
            message_id = payload["assistantMessageId"]
            timestamp = event.get("timestamp")
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp / 1000, tz=UTC).isoformat()
            message = messages.setdefault(message_id, {"timestamp": timestamp, "text": ""})
            if payload.get("kind") == "text_delta":
                message["text"] += payload.get("delta", "")
            request_id = active.get((event.get("sessionId"), event.get("turnId")))
            if request_id:
                requests[request_id].add(message_id)
        elif kind == "model_request_completed":
            request_id = payload["requestId"]
            record = {
                "usage": payload.get("usage"),
                "actor": payload.get("modelCall", {}).get("actorKind"),
                "model": payload.get("modelId"),
            }
            if request_id in completed and completed[request_id] != record:
                raise ValueError(f"Conflicting usage for request {request_id}")
            completed[request_id] = record
    records = []
    for request_id, record in completed.items():
        usage = record["usage"]
        if not usage:
            continue
        if record["model"] != GLM_PRICING["model"] or record["actor"] not in {"main", "subagent"}:
            raise ValueError(f"Unsupported ZCode model/actor: {record}")
        tokens = {key: usage.get(raw) for key, raw in TOKEN_FIELDS.items()}
        if any(type(value) is not int or value < 0 for value in tokens.values()):
            raise ValueError(f"Invalid provider token usage: {tokens}")
        if tokens["cached_tokens"] > tokens["prompt_tokens"]:
            raise ValueError(f"Cached tokens exceed input tokens: {tokens}")
        rates = GLM_PRICING["per_million_tokens"]
        cost = (
            (tokens["prompt_tokens"] - tokens["cached_tokens"]) * rates["input"]
            + tokens["cached_tokens"] * rates["cached_input"]
            + tokens["completion_tokens"] * rates["output"]
        ) / 1_000_000
        bound = requests.get(request_id, set())
        records.append({
            "request_id": request_id, "actor": record["actor"],
            "message_id": next(iter(bound)) if len(bound) == 1 else None,
            **tokens, "cost_usd": cost,
        })
    coverage.update({
        "recorded_requests": len(records),
        "requests_without_usage": len(set(requests) | set(completed)) - len(records),
        "requests_without_step": sum(record["message_id"] is None for record in records),
    })
    return {"messages": messages, "records": records, "coverage": coverage}


def totals(records: list[dict]) -> dict:
    return {
        **{key: sum(record[key] for record in records) for key in TOKEN_FIELDS},
        "cost_usd": sum(record["cost_usd"] for record in records),
        "requests": sum(record.get("requests", 1) for record in records),
    }


def backfill_zcode(data: dict, usage: dict) -> dict:
    """Preserve existing trajectory content; add recorded metrics and provenance."""
    if data["agent"].get("model_name") != GLM_PRICING["model"]:
        raise ValueError("Trajectory model does not match GLM pricing")
    steps = [step for step in data["steps"] if step["source"] == "agent"]
    # Timeout logs can have a longer tail than the saved trajectory. Match the
    # original converter's first-event timestamp, never shift steps by position.
    by_timestamp = defaultdict(list)
    for message_id, message in usage["messages"].items():
        by_timestamp[message["timestamp"]].append(message_id)
    step_messages = []
    for step in steps:
        candidates = by_timestamp[step.get("timestamp")]
        if len(candidates) > 1:
            candidates = [mid for mid in candidates if usage["messages"][mid]["text"] == step["message"]]
        step_messages.append(candidates[0] if len(candidates) == 1 else None)
    if len(set(mid for mid in step_messages if mid is not None)) != sum(mid is not None for mid in step_messages):
        raise ValueError("Ambiguous trajectory timestamps: multiple steps match the same provider message")
    main = totals([record for record in usage["records"] if record["actor"] == "main"])
    inclusive = totals(usage["records"])
    if not main["requests"]:
        raise ValueError("No recorded main-agent provider usage")
    by_message = defaultdict(list)
    for record in usage["records"]:
        if record["message_id"] is not None:
            by_message[record["message_id"]].append(record)
    for step, message_id in zip(steps, step_messages, strict=True):
        records = by_message[message_id]
        if not records:
            continue
        metrics = step.get("metrics") or {}
        aggregate = totals(records)
        metrics.update({key: aggregate[key] for key in (*TOKEN_FIELDS, "cost_usd")})
        metrics["extra"] = {
            **(metrics.get("extra") or {}),
            "usage_source": USAGE_SOURCE,
            "provider_request_ids": [record["request_id"] for record in records],
            "actor_kind": records[0]["actor"],
        }
        step["metrics"] = metrics
    matched_messages = {mid for mid in step_messages if mid is not None}
    coverage = {
        **usage["coverage"],
        "requests_without_step": sum(record["message_id"] not in matched_messages for record in usage["records"]),
        "steps_without_usage": sum(not by_message[mid] for mid in step_messages),
    }
    final = data.setdefault("final_metrics", {})
    final.update({f"total_{key}": main[key] for key in (*TOKEN_FIELDS, "cost_usd")})
    final["extra"] = {
        **(final.get("extra") or {}),
        "usage_source": USAGE_SOURCE,
        "usage_coverage": coverage,
        "cost_source": "published_price_estimate",
        "cost_pricing": GLM_PRICING,
        **{f"total_{key}_including_subagents": inclusive[key] for key in (*TOKEN_FIELDS, "cost_usd")},
    }
    # Existing ZCode trajectories flatten child messages into the steps array.
    # The ordinary final metrics retain the main-agent scope, as with Kimi.
    if data.get("notes"):
        data["notes"] = data["notes"].replace(
            "Token totals cover completed turns only.",
            "Token totals use recorded provider requests; final metrics cover the main agent, "
            "with totals including child agents in final_metrics.extra.",
        )
    return {"status": "recorded_provider_usage", "main": main, "including_subagents": inclusive, **coverage}


def dsh_usage(path: Path) -> dict:
    """DSH 0.2.0-rc.2 ACP used/size are context occupancy, not billing usage."""
    coverage = {"invalid_jsonl_lines": 0}
    snapshots = []
    for event in events(path, coverage):
        if event.get("event_type") != "session_update":
            continue
        update = event.get("payload", {}).get("update", {})
        if update.get("sessionUpdate") == "usage_update":
            snapshots.append(update)
    used = [snapshot["used"] for snapshot in snapshots if isinstance(snapshot.get("used"), (int, float))]
    return {
        "status": "billing_usage_unavailable",
        "reason": "Archived DSH ACP events contain context occupancy, without input/output/cache billing tokens.",
        "cost_usd": None,
        "context": {
            "snapshots": len(snapshots),
            "peak_used_tokens": max(used, default=None),
            "last_used_tokens": used[-1] if used else None,
            "capacity_tokens": snapshots[-1].get("size") if snapshots else None,
        },
        **coverage,
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--write", action="store_true", help="Write available provider metrics into trajectories")
    parser.add_argument("--output", type=Path, help="Save the per-task JSON report")
    args = parser.parse_args()
    run = args.run.resolve()
    trials = json.loads((run / "results.json").read_text())["trials"]
    reports, pending = [], []
    for trial in trials:
        agent = run / trial["solver_trial"] / "steps/solve/agent"
        path = agent / "trajectory.json"
        data = json.loads(path.read_text())
        if data["agent"]["name"] == "codex":
            report = backfill_qwen(data, qwen_usage(agent))
            Trajectory.model_validate(data)
            pending.append((path, data))
        elif data["agent"]["name"] == "zcode":
            report = backfill_zcode(data, zcode_usage(agent / "zcode.jsonl"))
            Trajectory.model_validate(data)
            pending.append((path, data))
        elif data["agent"]["name"] == "dsh":
            native = build_dsh_trajectory(agent)
            if native is None:
                report = dsh_usage(agent / "acp-events.jsonl")
            else:
                data = native.to_json_dict()
                pending.append((path, data))
                final = data["final_metrics"]
                report = {"status": "recorded_provider_usage"}
                for label, suffix in [("main", ""), ("including_subagents", "_including_subagents")]:
                    metrics = final["extra"] if suffix else final
                    report[label] = {
                        key: metrics.get(f"total_{key}{suffix}")
                        for key in (*TOKEN_FIELDS, "cost_usd")
                    }
                    report[label]["requests"] = final["extra"][f"requests_with_usage{suffix}"]
        else:
            raise ValueError(f"Unsupported agent: {data['agent']['name']}")
        reports.append({"task_id": trial["task_id"], "solver_trial": trial["solver_trial"], **report})
    measured = [report["including_subagents"] for report in reports if "including_subagents" in report]
    priced = [item for item in measured if all(item[key] is not None for key in (*TOKEN_FIELDS, "cost_usd"))]
    result = {
        "schema_version": "ibench-usage/v1", "run": run.name,
        "cost_scope": "recorded_provider_usage_including_subagents",
        "trials": len(reports), "trials_with_billing_usage": len(measured),
        "totals": totals(priced) if priced else None,
        "pricing": pending[0][1]["final_metrics"]["extra"]["cost_pricing"] if measured else None,
        "tasks": reports,
    }
    if args.write:
        for path, data in pending:
            write_json(path, data)
    if args.output:
        write_json(args.output, result)
    print(json.dumps({key: value for key, value in result.items() if key != "tasks"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
