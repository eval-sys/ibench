"""Price recorded Codex usage at QwenCloud's published USD list rates."""

import json
from collections import Counter, defaultdict
from pathlib import Path

PRICING = {
    "provider": "qwencloud",
    "model": "qwen3.8-max",
    "source": "https://www.qwencloud.com/models/qwen3.8-max",
    "checked_at": "2026-10-26",
    "currency": "USD",
    "scope": "QwenCloud standard list-price estimate, not regional or subscription billing",
    "cache_mode": "implicit",
    "per_million_tokens": {"input": 2.0, "cached_input": 0.25, "output": 6.0},
}
TOKEN_FIELDS = ("prompt_tokens", "completion_tokens", "cached_tokens")
MODELS = {"qwen3.8-max", "qwen3.8-max-0902"}


def qwen_usage(agent: Path) -> dict | None:
    """Read per-response usage, excluding cumulative turn/thread snapshots."""
    responses, invalid = {}, 0
    for path in sorted((agent / "sessions").rglob("*.jsonl")):
        with path.open(encoding="utf-8", errors="replace") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    invalid += 1
                    continue
                if event.get("type") != "token_usage_record":
                    continue
                payload = event["payload"]
                key = payload["session_id"], payload["response_id"]
                usage = payload["usage"]
                if key in responses and responses[key] != usage:
                    raise ValueError(f"Conflicting Qwen usage for response {key}")
                responses[key] = usage
    if not responses:
        return None
    sessions = defaultdict(list)
    for (session, _), usage in responses.items():
        tokens = {
            key: usage[raw]
            for key, raw in zip(TOKEN_FIELDS, ("input_tokens", "output_tokens", "cached_input_tokens"), strict=True)
        }
        if any(type(value) is not int or value < 0 for value in tokens.values()):
            raise ValueError(f"Invalid Qwen response usage: {tokens}")
        sessions[session].append(
            {**tokens, "extra": {"cache_write_input_tokens": usage.get("cache_write_input_tokens", 0)}}
        )
    return {"sessions": dict(sessions), "invalid_jsonl_lines": invalid}


def backfill_qwen(data: dict, native: dict | None = None) -> dict:
    """Preserve steps; use native response totals when journals contain a longer tail."""
    pending, seen = [], set()
    sessions = set()

    def aggregate(records):
        return {
            **{key: sum(record[key] for record in records) for key in (*TOKEN_FIELDS, "cost_usd")},
            "requests": sum(record["requests"] for record in records),
        }

    def visit(document):
        identity = document.get("trajectory_id") or document["session_id"]
        if identity in seen:
            raise ValueError(f"Duplicate Qwen trajectory: {identity}")
        seen.add(identity)
        sessions.add(document["session_id"])
        if document["agent"].get("name") != "codex" or document["agent"].get("model_name") not in MODELS:
            raise ValueError("Expected a Codex trajectory using Qwen3.8-Max")
        records, missing = [], 0
        for step in document["steps"]:
            if step["source"] != "agent" or step.get("is_copied_context"):
                continue
            if step.get("model_name") not in MODELS:
                raise ValueError(f"Unsupported Qwen step model: {step.get('model_name')}")
            metrics = step.get("metrics") or {}
            tokens = {key: metrics.get(key) for key in TOKEN_FIELDS}
            # Harbor's Codex converter serializes a zero cache count as None.
            if tokens["cached_tokens"] is None:
                tokens["cached_tokens"] = 0
            if any(value is not None and (type(value) is not int or value < 0) for value in tokens.values()):
                raise ValueError(f"Invalid Qwen token usage: {tokens}")
            if any(value is None for value in tokens.values()):
                missing += 1
                continue
            prompt, completion, cached = (tokens[key] for key in TOKEN_FIELDS)
            if cached > prompt:
                raise ValueError("Qwen cached tokens exceed input tokens")
            if (metrics.get("extra") or {}).get("cache_write_input_tokens", 0):
                raise ValueError("Explicit cache writes require explicit-cache pricing")
            rates = PRICING["per_million_tokens"]
            cost = (
                (prompt - cached) * rates["input"] + cached * rates["cached_input"] + completion * rates["output"]
            ) / 1_000_000
            records.append({**tokens, "cost_usd": cost, "requests": 1})
            pending.append((metrics, {"cost_usd": cost}))
        atif = aggregate(records)
        billing = records
        if native is not None:
            billing = []
            for metrics in native["sessions"].get(document["session_id"], []):
                prompt, completion, cached = (metrics[key] for key in TOKEN_FIELDS)
                if cached > prompt or metrics["extra"]["cache_write_input_tokens"]:
                    raise ValueError("Invalid or explicit-cache Qwen response usage")
                rates = PRICING["per_million_tokens"]
                cost = (
                    (prompt - cached) * rates["input"] + cached * rates["cached_input"] + completion * rates["output"]
                ) / 1_000_000
                billing.append({**{key: metrics[key] for key in TOKEN_FIELDS}, "cost_usd": cost, "requests": 1})
            recorded = Counter(tuple(record[key] for key in TOKEN_FIELDS) for record in records)
            provider = Counter(tuple(record[key] for key in TOKEN_FIELDS) for record in billing)
            if recorded - provider:
                raise ValueError("Qwen ATIF usage is not covered by native response records")
        main = aggregate(billing)
        if not billing:
            raise ValueError("No recorded Qwen billing usage")
        final = document["final_metrics"]
        for key in TOKEN_FIELDS:
            if final.get(f"total_{key}") is not None and final[f"total_{key}"] not in (atif[key], main[key]):
                raise ValueError(f"Qwen {key} total does not match recorded step usage")
        children = [visit(child) for child in document.get("subagent_trajectories") or []]
        inclusive = aggregate([main, *(child["including_subagents"] for child in children)])
        coverage = {
            "steps_without_usage": missing + sum(child["steps_without_usage"] for child in children),
            "requests_without_step": len(billing)
            - len(records)
            + sum(child["requests_without_step"] for child in children),
        }
        pending.append(
            (
                final,
                {
                    **{f"total_{key}": main[key] for key in TOKEN_FIELDS},
                    "total_cost_usd": main["cost_usd"],
                    "extra": {
                        **(final.get("extra") or {}),
                        "cost_source": "published_price_estimate",
                        "cost_pricing": PRICING,
                        "usage_source": "codex.token_usage_record"
                        if native is not None
                        else "codex.atif_recorded_tokens",
                        "usage_coverage": coverage,
                        **{f"total_{key}_including_subagents": inclusive[key] for key in (*TOKEN_FIELDS, "cost_usd")},
                    },
                },
            )
        )
        return {"status": "recorded_provider_usage", "main": main, "including_subagents": inclusive, **coverage}

    report = visit(data)
    if native is not None and set(native["sessions"]) - sessions:
        raise ValueError("Native Qwen usage contains sessions missing from the trajectory")
    report["invalid_jsonl_lines"] = native["invalid_jsonl_lines"] if native is not None else 0
    for target, fields in pending:
        target.update(fields)
    return report
