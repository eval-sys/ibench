"""Backfill Kimi Code ATIF without rerunning agents or changing scores.

Usage: uv run python -m ibench.utils.kimicode RUN_OR_TRIAL [--dry-run] [--overwrite]
The pinned upstream parser is vendored to work offline with Harbor 0.23.0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from harbor.models.trajectories import SubagentTrajectoryRef, Trajectory
from harbor.utils.trajectory_utils import format_trajectory_json
from harbor.utils.trajectory_validator import TrajectoryValidator

from . import trajectory as upstream
from .pricing import price_data, price_trajectory

CONVERTER_COMMIT = "1b7f64e72cb6c968381953d570681b49db38c922"


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ms(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp() * 1000)


def _write_trajectory(destination: Path, text: str) -> None:
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent, suffix=".tmp", delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(text)
            output.close()
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)


def _read_events(path: Path, warnings: list[str]) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    events = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line, strict=False)
        except json.JSONDecodeError as exc:
            if number == len(lines) and not text.endswith("\n"):
                warnings.append(f"Ignored truncated final JSONL line: {path.name}:{number}")
                continue
            raise ValueError(f"Invalid JSONL: {path}:{number}") from exc
        _check(isinstance(event, dict), f"Non-object JSONL event: {path}:{number}")
        _check(event.get("agentId", path.parent.name) == path.parent.name, f"Agent identity mismatch: {path}")
        events.append(event)
    return events


def _merge_events(body: list[dict], tail: list[dict]) -> tuple[list[dict], int]:
    """Only remove a proven suffix/prefix overlap; reject ambiguous ordering."""
    left = [json.dumps(e, sort_keys=True) for e in body]
    right = [json.dumps(e, sort_keys=True) for e in tail]
    overlap = next((n for n in range(min(len(left), len(right)), 0, -1) if left[-n:] == right[:n]), 0)
    _check(not set(left).intersection(right[overlap:]), "Tail overlaps outside the body suffix")
    remaining = tail[overlap:]
    before = [e["time"] for e in body if isinstance(e.get("time"), int)]
    after = [e["time"] for e in remaining if isinstance(e.get("time"), int)]
    if remaining:
        _check(bool(before and after) and min(after) >= max(before), "Tail event order is not established")
    return body + remaining, overlap


def _annotate(
    trajectory: Trajectory,
    wire: Path,
    events: list[dict],
    model: str | None,
    version: str | None,
    execution: dict,
    cutoff: int | None,
) -> Trajectory:
    prompts = [e for e in events if e.get("type") == "turn.prompt"]
    origins = [p.get("origin", {}).get("kind") for p in prompts]
    copied = sum(bool(s.is_copied_context) for s in trajectory.steps)
    removed = 0
    # A task notification in the current invocation is not resumed-session context.
    if (
        copied
        and origins
        and origins[0] == "user"
        and origins[1:]
        and all(o == "task" for o in origins[1:])
        and execution.get("started_at")
        and prompts[0].get("time", 0) >= _ms(execution["started_at"])
    ):
        parsed = upstream.parse_wire(wire)
        last_turn = max(s.turn for s in parsed.steps)
        for step in parsed.steps:
            step.turn = last_turn
        trajectory = upstream.to_trajectory(parsed, agent_name="kimi-code", agent_version=version, model_name=model)
        trajectory.notes = "Background-task notifications belong to this invocation, not copied resume context."
        removed = copied
    agent_id = wire.parent.name
    trajectory.trajectory_id = f"{trajectory.session_id}/{agent_id}"
    for step in trajectory.steps:
        if model and step.model_name == "__kimi_env_model__":
            step.extra = {**(step.extra or {}), "wire_model_alias": step.model_name}
            step.model_name = model
        if cutoff is not None and step.timestamp and _ms(step.timestamp) > cutoff:
            step.extra = {**(step.extra or {}), "started_after_execution_cutoff": True}
    if trajectory.agent.model_name in (None, "__kimi_env_model__") and model:
        trajectory.agent.model_name = model
    price_trajectory(trajectory)
    trajectory.agent.extra = {
        **(trajectory.agent.extra or {}),
        "wire_agent_id": agent_id,
        "configured_model_name": model,
    }
    user_steps = [s for s in trajectory.steps if s.source == "user"]
    _check(len(user_steps) == len(prompts), "User prompt count mismatch")
    for step, prompt in zip(user_steps, prompts, strict=True):
        step.extra = {**(step.extra or {}), "wire_prompt_origin": prompt.get("origin")}

    loops = [e["event"] for e in events if e.get("type") == "context.append_loop_event"]
    calls = Counter(e["toolCallId"] for e in loops if e.get("type") == "tool.call")
    results = Counter(e["toolCallId"] for e in loops if e.get("type") == "tool.result")
    actual_calls = Counter(c.tool_call_id for s in trajectory.steps for c in s.tool_calls or [])
    actual_results = Counter(r.source_call_id for s in trajectory.steps if s.observation for r in s.observation.results)
    _check(calls == actual_calls and results == actual_results, "Tool calls/results were lost during conversion")
    agents = [s for s in trajectory.steps if s.source == "agent"]
    begins = sum(e.get("type") == "step.begin" for e in loops)
    requests = sum(e.get("type") == "llm.request" for e in events)
    _check(begins == requests == len(agents), "Model-step/request count mismatch")

    # Independently count one usage per raw model step, including an unfinished last step.
    usages, usage, active = [], None, False
    for event in events:
        ev = event.get("event", {})
        if ev.get("type") == "step.begin":
            if active:
                usages.append(usage)
            active, usage = True, None
        if event.get("type") == "usage.record" and active:
            usage = event.get("usage")
        if ev.get("type") == "step.end":
            _check(active, "Model step ended without a matching begin")
            usages.append(ev.get("usage") or usage)
            active, usage = False, None
    if active:
        usages.append(usage)
    _check(len(usages) == len(agents), "Usage/model-step count mismatch")
    totals = Counter()
    for step, usage in zip(agents, usages, strict=True):
        if usage and not step.is_copied_context:
            for key in ("inputOther", "inputCacheRead", "inputCacheCreation", "output"):
                totals[key] += usage.get(key, 0) or 0
    fm = trajectory.final_metrics
    expected = (
        totals["inputOther"] + totals["inputCacheRead"] + totals["inputCacheCreation"],
        totals["output"],
        totals["inputCacheRead"],
    )
    _check(
        expected == (fm.total_prompt_tokens or 0, fm.total_completion_tokens or 0, fm.total_cached_tokens or 0),
        "Final token metrics differ from raw per-step usage",
    )
    times = [e["time"] for e in events if isinstance(e.get("time"), int)]
    late = [e for e in events if cutoff is not None and e.get("time", 0) > cutoff]
    trajectory.extra = {
        "offline_wire_validation": {
            "events": len(events),
            "agent_steps": len(agents),
            "all_steps": len(trajectory.steps),
            "raw_step_begins": begins,
            "completed_model_steps": sum(e.get("type") == "step.end" for e in loops),
            "unfinished_model_steps": begins - sum(e.get("type") == "step.end" for e in loops),
            "tool_calls": calls.total(),
            "tool_results": results.total(),
            "calls_without_results": list((calls - results).elements()),
            "orphan_results": [],
            "usage_records": sum(e.get("type") == "usage.record" for e in events),
            "usage_scopes": dict(
                Counter(e.get("usageScope", "unknown") for e in events if e.get("type") == "usage.record")
            ),
            "prompt_tokens": fm.total_prompt_tokens,
            "completion_tokens": fm.total_completion_tokens,
            "cached_tokens": fm.total_cached_tokens,
            "source": fm.extra.get("source"),
            "first_event_time_ms": min(times) if times else None,
            "last_event_time_ms": max(times) if times else None,
            "events_after_execution_cutoff": len(late),
            "model_requests_after_execution_cutoff": sum(e.get("type") == "llm.request" for e in late),
            "same_invocation_copied_flags_removed": removed,
        }
    }
    return trajectory


def _link_children(main: Trajectory, original: Path, sources: set[Path], warnings: list[str]) -> list[dict]:
    children = {c.agent.extra["wire_agent_id"]: c for c in main.subagent_trajectories or []}
    relations = []
    for parent in [main, *children.values()]:
        for step in parent.steps:
            calls = {c.tool_call_id: c for c in step.tool_calls or []}
            for obs in step.observation.results if step.observation else []:
                call = calls.get(obs.source_call_id)
                if not call or call.function_name not in {"Agent", "AgentSwarm"} or not isinstance(obs.content, str):
                    continue
                text = obs.content
                if call.function_name == "AgentSwarm":
                    match = re.search(r"^output_path: .+?/(\.kimi-code/.+)$", text, re.M)
                    if match:
                        artifact = (original / match[1]).resolve()
                        _check(
                            artifact.is_relative_to(original.resolve()),
                            "Externalized tool result escapes log directory",
                        )
                        _check(
                            artifact.parent.name == "tool-results" and artifact.name.startswith("AgentSwarm-"),
                            "Unexpected externalized AgentSwarm artifact path",
                        )
                        if artifact.is_file():
                            text = artifact.read_text()
                            sources.add(artifact)
                        else:
                            warnings.append(f"Missing externalized AgentSwarm result: {match[1]}")
                    ids = re.findall(r'<subagent agent_id="([^"]+)"', text)
                else:
                    ids = re.findall(r"^agent_id: (\S+)$", text.split("\n\n", 1)[0], re.M)
                refs = []
                for agent_id in dict.fromkeys(ids):
                    if agent_id not in children:
                        warnings.append(f"Missing child wire log for returned agent ID: {agent_id}")
                        continue
                    child = children[agent_id]
                    refs.append(SubagentTrajectoryRef(trajectory_id=child.trajectory_id, session_id=child.session_id))
                    relations.append(
                        {
                            "parent": parent.trajectory_id,
                            "call_id": call.tool_call_id,
                            "child": child.trajectory_id,
                            "evidence": "explicit_agent_id_in_tool_result",
                        }
                    )
                obs.subagent_trajectory_ref = refs or None
    return relations


def convert_trial(trial: Path, *, overwrite: bool = False, dry_run: bool = False) -> dict:
    """Convert one native solve trial; preserve raw logs, patch and historical result files."""
    trial = trial.resolve()
    original = trial / "steps/solve/agent"
    _check(original.is_dir(), f"Missing solve agent logs: {original}")
    destination = original / "trajectory.json"
    if destination.exists() and not overwrite:
        return {"trial": trial.name, "status": "skipped", "reason": "trajectory.json already exists"}
    result_path = trial / "result.json"
    wire_paths = sorted(original.glob(".kimi-code/sessions/*/session_*/agents/*/wire.jsonl"))
    input_paths = {
        result_path,
        *wire_paths,
        *(trial / "agent").rglob("wire.jsonl"),
        *original.rglob("AgentSwarm-*.txt"),
    }
    input_paths.update(
        p for p in (original / "kimi-code.txt", original / ".kimi-code/session_index.jsonl") if p.is_file()
    )
    before = {p: {"sha256": _sha(p), "bytes": p.stat().st_size} for p in input_paths}
    result = json.loads(result_path.read_bytes())
    config = result["config"]["agent"]
    _check(config.get("name") == "kimi-code", f"Not a Kimi Code trial: {trial}")
    model = config.get("model_name")
    version = (result.get("agent_info") or {}).get("version") or (config.get("kwargs") or {}).get("version")
    step = next((s for s in result.get("step_results", []) if s.get("step_name") == "solve"), {})
    execution = step.get("agent_execution") or result.get("agent_execution") or {}
    error = step.get("exception_info") or result.get("exception_info") or {}
    timeout = re.search(r"timed out after ([\d.]+) seconds", error.get("exception_message", ""))
    cutoff = _ms(execution["finished_at"]) if execution.get("finished_at") else None
    cutoff_basis = "recorded_agent_execution_finish" if cutoff is not None else None
    if timeout and execution.get("started_at"):
        cutoff = _ms(execution["started_at"]) + int(float(timeout[1]) * 1000)
        cutoff_basis = "agent_start_plus_recorded_timeout"
    sources, warnings, fragments = {result_path}, [], []
    with TemporaryDirectory(prefix="ibench-kimi-atif-") as temporary:
        work, logs = Path(temporary), {}
        for filename in ("kimi-code.txt", ".kimi-code/session_index.jsonl"):
            source = original / filename
            if source.is_file():
                target = work / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                sources.add(source)
        for source in wire_paths:
            relative = source.relative_to(original)
            events = _read_events(source, warnings)
            sources.add(source)
            tail = trial / "agent" / relative
            if tail.is_file():
                more = _read_events(tail, warnings)
                events, overlap = _merge_events(events, more)
                fragments.append(
                    {
                        "path": str(tail.relative_to(trial)),
                        "agent_id": source.parent.name,
                        "events_appended": len(more) - overlap,
                        "overlapping_events": overlap,
                    }
                )
                sources.add(tail)
            target = work / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events))
            key = (target.parents[2].name, target.parent.name)
            _check(key not in logs, f"Duplicate session/agent identity: {key}")
            logs[key] = (target, events)
        unmatched = set((trial / "agent").rglob("wire.jsonl")) - sources
        _check(not unmatched, f"Tail logs without matching bodies: {sorted(map(str, unmatched))}")
        main = upstream.build_trajectory(work, agent_version=version, model_name=model)
        _check(
            main is not None and main.final_metrics.extra.get("source") == "wire",
            "No matching main wire log; refusing a silent stdout fallback",
        )
        _check((main.session_id, "main") in logs, "Selected session has no main log")
        wire, events = logs[(main.session_id, "main")]
        main = _annotate(main, wire, events, model, version, execution, cutoff)
        children = []
        for (session, agent_id), (wire, events) in logs.items():
            if session != main.session_id or agent_id == "main":
                continue
            child = upstream.to_trajectory(
                upstream.parse_wire(wire), agent_name="kimi-code", agent_version=version, model_name=model
            )
            _check(child is not None, f"No convertible child steps: {agent_id}")
            children.append(_annotate(child, wire, events, model, version, execution, cutoff))
        main.subagent_trajectories = children or None
        costs = [agent.final_metrics.total_cost_usd for agent in [main, *children]]
        if all(cost is not None for cost in costs):
            main.final_metrics.extra["total_cost_usd_including_subagents"] = sum(costs)
        relations = _link_children(main, original, sources, warnings)
        linked = {r["child"] for r in relations}
        inputs = [{"path": str(p.relative_to(trial)), **before[p]} for p in sorted(sources)]
        main.extra["offline_conversion"] = {
            "converter_commit": CONVERTER_COMMIT,
            "converter_sha256": _sha(Path(upstream.__file__)),
            "model_name": model,
            "agent_version": version,
            "raw_inputs": inputs,
            "execution": execution,
            "execution_cutoff_ms": cutoff,
            "execution_cutoff_basis": cutoff_basis,
            "fragments": fragments,
            "child_relations": relations,
            "unlinked_child_agents": [
                c.agent.extra["wire_agent_id"] for c in children if c.trajectory_id not in linked
            ],
            "ignored_sessions": sorted({sid for sid, _ in logs if sid != main.session_id}),
            "warnings": warnings,
            "usage_policy": "Per-agent metrics; never combine parent/child usage or invent missing costs.",
            "limitations": [
                "No multimedia extraction; original payloads remain in wire logs.",
                "Shutdown events are retained; inspect execution-cutoff counters.",
                "Historical result and score files are not updated.",
            ],
        }
        validator = TrajectoryValidator()
        data = main.to_json_dict()
        _check(validator.validate(data, validate_images=False), str(validator.errors))
        text = format_trajectory_json(data)
        _check(validator.validate(json.loads(text), validate_images=False), str(validator.errors))
        _check(all(_sha(trial / i["path"]) == i["sha256"] for i in inputs), "Inputs changed during conversion")
        if not dry_run:
            _write_trajectory(destination, text)
        return {
            "trial": trial.name,
            "status": "validated" if dry_run else "written",
            "trajectory": str(destination),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "main": main.extra["offline_wire_validation"],
            "children": len(children),
            "linked_children": len({r["child"] for r in relations}),
            "fragments": len(fragments),
            "warnings": warnings,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ibench.utils.kimicode", description=__doc__)
    parser.add_argument("path", type=Path, help="iBench run, jobs/solve directory, or single solve trial")
    parser.add_argument("--dry-run", action="store_true", help="Convert and validate without writing trajectories")
    parser.add_argument("--overwrite", action="store_true", help="Reconvert existing trajectory.json files")
    parser.add_argument("--cost-only", action="store_true", help="Update only costs in existing trajectories")
    args = parser.parse_args(argv)
    root = args.path.resolve()
    if (root / "steps/solve/agent").is_dir():
        trials = [root]
    else:
        directory = root / "jobs/solve" if (root / "jobs/solve").is_dir() else root
        trials = sorted(p.parent for p in directory.glob("*/result.json"))
    if not trials:
        parser.error(f"No solve trials found: {root}")
    counts = Counter()
    for trial in trials:
        try:
            if args.cost_only:
                destination = trial / "steps/solve/agent/trajectory.json"
                data = json.loads(destination.read_text())
                total = price_data(data)
                validator = TrajectoryValidator()
                _check(validator.validate(data, validate_images=False), str(validator.errors))
                if not args.dry_run:
                    _write_trajectory(destination, format_trajectory_json(data))
                report = {
                    "trial": trial.name, "status": "validated" if args.dry_run else "written",
                    "total_cost_usd_including_subagents": total,
                }
            else:
                report = convert_trial(trial, overwrite=args.overwrite, dry_run=args.dry_run)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            report = {"trial": trial.name, "status": "failed", "error": str(exc)}
        counts[report["status"]] += 1
        print(json.dumps(report), flush=True)
    print(json.dumps({"summary": dict(counts), "total": len(trials)}))
    return int(bool(counts["failed"]))
