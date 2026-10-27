from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from harbor.agents.installed.acp import AcpAgent, AcpOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext, ModelUsage
from harbor.utils.trajectory_utils import format_trajectory_json

from ibench.utils.dsh import build_trajectory


class DshOptions(AcpOptions):
    version: Literal["0.2.0-rc.2"] = "0.2.0-rc.2"
    reasoning_effort: Literal["off", "low", "high", "max"] = "high"


class Dsh(AcpAgent):
    """Run the official DeepSeek Harness through Harbor's ACP runner."""

    options_model = DshOptions
    options: DshOptions
    _PATCH_PATH = "/installed-agent/dsh.cordis.yml"

    def __init__(
        self,
        logs_dir: Path,
        *,
        model_name: str | None = None,
        version: str | None = None,
        **kwargs,
    ):
        version = version or "0.2.0-rc.2"
        super().__init__(
            logs_dir=logs_dir,
            model_name=model_name or "deepseek/deepseek-flash",
            version=version,
            registry_entry={
                "id": "dsh",
                "name": "DeepSeek Harness",
                "version": version,
                "description": "Official DeepSeek Harness ACP server",
                "repository": "https://github.com/deepseek-ai/deepseek-harness",
                "distribution": {
                    "npx": {
                        "package": f"@deepseek-ai/dsh@{version}",
                        "args": ["--profile", "acp", "--patch", self._PATCH_PATH],
                        "env": {
                            "DSH_HOME": "/tmp/harbor-dsh",
                            "DSH_PERMISSION_MODE": "danger-full-access",
                            "DSH_TELEMETRY_MODE": "DISABLED",
                        },
                    }
                },
            },
            **kwargs,
        )

    @staticmethod
    def name() -> str:
        return "dsh"

    async def install(self, environment: BaseEnvironment) -> None:
        patch = [
            {"id": "acp", "config": {"provider": "deepseek-official", "model": self._parsed_model_name}},
            {"id": "llm-deepseek", "config": {"reasoningEffort": self.options.reasoning_effort}},
            {"id": "tool-web", "config": {"search": False}},
            {"id": "session-log-deepseek", "disabled": True},
            {
                "id": "session-persistence-jsonl",
                "config": {"root": "/logs/agent/dsh-sessions", "compression": "none"},
            },
        ]
        await self._upload_config_text(
            environment,
            content=json.dumps(patch),
            remote_path=self._PATCH_PATH,
            filename="dsh.cordis.yml",
        )
        await super().install(environment)
        # Populate the npm cache and profile before agent network restrictions apply.
        await self.exec_as_agent(environment, command=f"{self._LAUNCHER_REMOTE_PATH} --dump-config >/dev/null")

    def populate_context_post_run(self, context: AgentContext) -> None:
        super().populate_context_post_run(context)
        summary = self._load_summary() or {}
        session_id = (summary.get("session") or {}).get("sessionId")
        trajectory = build_trajectory(self.logs_dir, session_id=session_id, version=self.options.version)
        if trajectory is None:
            return  # Older runs only have ACP logs and no billing usage.
        (self.logs_dir / "trajectory.json").write_text(format_trajectory_json(trajectory.to_json_dict()))
        metrics = trajectory.final_metrics.extra
        context.n_input_tokens = metrics.get("total_prompt_tokens_including_subagents")
        context.n_output_tokens = metrics.get("total_completion_tokens_including_subagents")
        context.n_cache_tokens = metrics.get("total_cached_tokens_including_subagents")
        context.cost_usd = metrics.get("total_cost_usd_including_subagents")
        per_model = {}

        def collect(item):
            for step in item.steps:
                if step.is_copied_context or step.metrics is None:
                    continue
                usage = per_model.setdefault(step.model_name, ModelUsage(cost_usd=0))
                usage.n_input_tokens += step.metrics.prompt_tokens or 0
                usage.n_output_tokens += step.metrics.completion_tokens or 0
                usage.n_cache_tokens += step.metrics.cached_tokens or 0
                usage.cost_usd = usage.cost_usd + step.metrics.cost_usd if usage.cost_usd is not None and step.metrics.cost_usd is not None else None
            for child in item.subagent_trajectories or []:
                collect(child)

        collect(trajectory)
        context.model_usage = per_model or None

    async def exec_as_agent(
        self, environment: BaseEnvironment, command: str, env: dict[str, str] | None = None, **kwargs
    ):
        if env and "HARBOR_ACP_REQUESTED_MODEL" in env:
            # DSH advertises JSON-encoded provider/model pairs as opaque ACP option values.
            env = {
                **env,
                "HARBOR_ACP_REQUESTED_MODEL": json.dumps(
                    ["deepseek-official", self._parsed_model_name], separators=(",", ":")
                ),
            }
        return await super().exec_as_agent(environment, command, env=env, **kwargs)
