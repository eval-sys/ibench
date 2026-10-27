"""Published Fireworks Kimi K3 rates, independent of LiteLLM's model catalog."""

from harbor.models.trajectories import Trajectory

MODEL = "accounts/fireworks/models/kimi-k3"
PRICING = {
    "provider": "fireworks",
    "model": MODEL,
    "source": "https://fireworks.ai/models/fireworks/kimi-k3",
    "checked_at": "2026-10-20",
    "currency": "USD",
    "per_million_tokens": {"input": 3.0, "cached_input": 0.30, "output": 15.0},
}


def price_trajectory(trajectory: Trajectory) -> None:
    """Price this agent's recorded usage after wire model aliases are resolved."""
    steps = [
        step for step in trajectory.steps
        if not step.is_copied_context and step.metrics is not None
    ]
    if not steps or any(step.model_name != MODEL for step in steps):
        return
    rates = PRICING["per_million_tokens"]
    priced = []
    for step in steps:
        metrics = step.metrics
        prompt, completion = metrics.prompt_tokens, metrics.completion_tokens
        cached = (metrics.extra or {}).get("cache_read_input_tokens", metrics.cached_tokens or 0)
        if prompt is None or completion is None or not 0 <= cached <= prompt or completion < 0:
            raise ValueError("Invalid token usage for Fireworks Kimi K3 pricing")
        cost = (
            (prompt - cached) * rates["input"]
            + cached * rates["cached_input"]
            + completion * rates["output"]
        ) / 1_000_000
        priced.append((metrics, cost))
    for metrics, cost in priced:
        metrics.cost_usd = cost
    trajectory.final_metrics.total_cost_usd = sum(cost for _, cost in priced)
    trajectory.final_metrics.extra = {
        **(trajectory.final_metrics.extra or {}),
        "cost_source": "published_price_estimate",
        "cost_pricing": PRICING,
    }


def price_data(data: dict) -> float:
    """Update only cost fields in an existing trajectory, including child agents."""
    trajectory = Trajectory.model_validate(data)
    price_trajectory(trajectory)
    metrics = trajectory.final_metrics
    if (metrics.extra or {}).get("cost_source") != "published_price_estimate":
        raise ValueError("No published Fireworks Kimi K3 pricing for this trajectory")
    for original, step in zip(data["steps"], trajectory.steps, strict=True):
        if not step.is_copied_context and step.metrics is not None:
            original["metrics"]["cost_usd"] = step.metrics.cost_usd
    total = metrics.total_cost_usd + sum(price_data(child) for child in data.get("subagent_trajectories") or [])
    final = data["final_metrics"]
    final["total_cost_usd"] = metrics.total_cost_usd
    final["extra"] = {
        **(final.get("extra") or {}),
        "cost_source": metrics.extra["cost_source"],
        "cost_pricing": metrics.extra["cost_pricing"],
        "total_cost_usd_including_subagents": total,
    }
    return total
