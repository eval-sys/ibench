from __future__ import annotations

import json
import shlex
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from harbor.agents.capabilities import AgentCapabilities
from harbor.agents.installed.base import BaseInstalledAgent, with_prompt_template
from harbor.agents.installed.node_install import nvm_node_install_snippet
from harbor.agents.options import InstalledAgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trajectories import Agent, FinalMetrics, Observation, ObservationResult, Step, ToolCall, Trajectory
from harbor.utils.trajectory_utils import format_trajectory_json
from pydantic import Field

_RELEASE_SHA256 = "2edc79650fcff72358670af4ffbfbf7d979ba95476611a80ad1151d577e90fe3"
_NODE_PATH_SETUP = '. "$HOME/.nvm/nvm.sh"; export PATH="$HOME/.local/bin:$PATH"; '


class ZCodeOptions(InstalledAgentOptions):
    version: Literal["3.15.3"] = Field(
        default="3.15.3", description="Official desktop release containing the CLI (0.16.9)."
    )
    reasoning_effort: Literal["low", "high", "max"] = "high"


class ZCode(BaseInstalledAgent):
    """Run the unmodified Agent CLI bundled in the official Linux ZCode release."""

    capabilities = AgentCapabilities(atif=True)
    options_model = ZCodeOptions

    def __init__(self, logs_dir: Path, *, version: str | None = None, **kwargs):
        super().__init__(logs_dir, version=version or "3.15.3", **kwargs)

    @staticmethod
    def name() -> str:
        return "zcode"

    def get_version_command(self) -> str:
        return f"{_NODE_PATH_SETUP}zcode --version"

    async def install(self, environment: BaseEnvironment) -> None:
        await self.exec_as_root(
            environment,
            command="""
set -eu
test "$(uname -sm)" = "Linux x86_64" || {
  echo 'The official ZCode package currently requires Linux x86_64.' >&2
  exit 1
}
if ! command -v curl >/dev/null || ! command -v unsquashfs >/dev/null; then
  apt-get update
  apt-get install -y --no-install-recommends ca-certificates curl squashfs-tools
fi
""".strip(),
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )
        await self.exec_as_agent(
            environment,
            command=f"""
set -euo pipefail
{nvm_node_install_snippet(node_major=24)}
runtime="$HOME/.local/share/harbor-zcode/{self._version}"
mkdir -p "$runtime" "$HOME/.local/bin"
if [ ! -f "$runtime/resources/glm/zcode.cjs" ]; then
  archive="$runtime/ZCode.AppImage"
  curl -fL --retry 3 \
    'https://cdn-zcode.z.ai/zcode/electron/releases/{self._version}/linux-x64/ZCode-{self._version}-linux-x64.AppImage' \
    -o "$archive"
  printf '%s  %s\n' '{_RELEASE_SHA256}' "$archive" | sha256sum -c -
  chmod +x "$archive"
  offset=$("$archive" --appimage-offset)
  unsquashfs -no-progress -processors 2 -offset "$offset" -dest "$runtime" \
    "$archive" resources/glm resources/config
  rm "$archive"
fi
printf '#!/bin/sh\nexec node "%s/resources/glm/zcode.cjs" "$@"\n' "$runtime" \
  > "$HOME/.local/bin/zcode"
chmod +x "$HOME/.local/bin/zcode"
{_NODE_PATH_SETUP}zcode --version
""".strip(),
        )

    def _provider_config(self) -> dict:
        api_key = self._get_env("ZCODE_API_KEY")
        if not api_key:
            raise ValueError("ZCODE_API_KEY is required")
        if not self.model_name:
            raise ValueError("ZCode requires model_name")
        return {
            "schemaVersion": 1,
            "config": {
                "providerConfigRules": {
                    "providerRules": [
                        {
                            "providerId": "ibench",
                            "providerName": "iBench API",
                            "config": {
                                "group": "standard-personal",
                                "access": {"type": "api-key", "apiKey": api_key},
                                "api": {
                                    "type": "openai-chat-completions",
                                    "baseUrl": self._get_env("ZCODE_BASE_URL") or "https://api.z.ai/api/paas/v4",
                                },
                                "personalModelIds": [self.model_name],
                            },
                        }
                    ]
                },
                "modelConfigRules": {"providerModelRules": [], "manualProviderModelRules": []},
                "defaultModelSelection": {
                    "providerId": "ibench",
                    "modelId": self.model_name,
                    "options": {"reasoningLevel": self.options.reasoning_effort},
                },
            },
        }

    @with_prompt_template
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        config = self._provider_config()
        private_dir = f"/tmp/harbor-zcode-{uuid.uuid4().hex}"
        output = str(self.environment_logs_dir / "zcode.jsonl")
        await self.exec_as_agent(environment, command=f"mkdir -m 700 {private_dir}")
        await self._upload_config_text(
            environment,
            content=json.dumps(config),
            remote_path=f"{private_dir}/provider.json",
            filename="provider.json",
        )
        run_env = {
            "ZCODE_DATA_BASE_DIR": private_dir,
            "ZCODE_STORAGE_DIR": f"{private_dir}/sessions",
            "ZCODE_PERSONAL_PROVIDER_CONFIG_FILE": f"{private_dir}/provider.json",
            "HARBOR_ZCODE_INSTRUCTION": instruction,
            "NO_COLOR": "1",
        }
        # The private directory is outside downloaded logs; never archive API keys.
        await self.exec_as_agent(
            environment,
            command=(
                f"{_NODE_PATH_SETUP}"
                f'export ZCODE_BUILTIN_PROVIDER_CONFIG_FILE="$HOME/.local/share/harbor-zcode/{self._version}'
                '/resources/config/provider/zcode-builtin.json"; '
                'instruction="$HARBOR_ZCODE_INSTRUCTION"; unset HARBOR_ZCODE_INSTRUCTION; '
                "zcode --mode yolo --output-format stream-json --disallowed-tools WebSearch "
                '--prompt "$instruction" </dev/null 2>&1 | '
                f"tee {shlex.quote(output)}"
            ),
            env=run_env,
        )

    def populate_context_post_run(self, context: AgentContext) -> None:
        trajectory = build_trajectory(self.logs_dir, agent_version=self.version(), model_name=self.model_name)
        if trajectory is None:
            return
        (self.logs_dir / "trajectory.json").write_text(format_trajectory_json(trajectory.to_json_dict()))
        metrics = trajectory.final_metrics
        if metrics is not None:
            context.n_input_tokens = metrics.total_prompt_tokens
            context.n_output_tokens = metrics.total_completion_tokens
            context.n_cache_tokens = metrics.total_cached_tokens


def build_trajectory(logs_dir: Path, *, agent_version: str | None, model_name: str | None) -> Trajectory | None:
    path = logs_dir / "zcode.jsonl"
    if not path.exists():
        return None
    steps: list[Step] = []
    messages: dict[str, Step] = {}
    calls: dict[str, tuple[Step, ToolCall]] = {}
    seen: set[str] = set()
    totals: dict[str, int] = {}
    session_id = "unknown"
    completed = False
    for line in path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue  # A timeout can leave the final JSON line incomplete.
        if not isinstance(event, dict):
            continue
        event_id = event.get("eventId")
        if event_id:
            if event_id in seen:
                continue
            seen.add(event_id)
        session_id = event.get("sessionId") or session_id
        payload = event.get("payload", event)
        if not isinstance(payload, dict):
            continue
        event_type = event.get("type")
        kind = payload.get("kind")
        timestamp = event.get("timestamp")
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp / 1000, tz=UTC).isoformat()
        if event_type == "turn.started":
            steps.append(Step(step_id=len(steps) + 1, source="user", message=payload["input"], timestamp=timestamp))
            completed = False
        elif event_type == "model.streaming":
            message_id = payload["assistantMessageId"]
            if message_id not in messages:
                step = Step(
                    step_id=len(steps) + 1,
                    source="agent",
                    message="",
                    timestamp=timestamp,
                    model_name=model_name,
                    llm_call_count=1,
                    extra={"stream_complete": False},
                )
                messages[message_id] = step
                steps.append(step)
            step = messages[message_id]
            if kind == "text_delta":
                step.message += payload.get("delta", "")
            elif kind == "reasoning_delta":
                step.reasoning_content = (step.reasoning_content or "") + payload.get("delta", "")
            elif kind == "finish":
                step.extra = {"stream_complete": True}
        if (event_type == "model.streaming" and kind == "tool_call") or (
            event_type == "tool.updated" and kind in {"scheduled", "started"}
        ):
            call_id = payload["toolCallId"]
            if call_id not in calls:
                owner = messages.get(payload.get("assistantMessageId"))
                if owner is None:
                    continue
                call = ToolCall(
                    tool_call_id=call_id, function_name=payload["toolName"], arguments=payload.get("input", {})
                )
                owner.tool_calls = [*(owner.tool_calls or []), call]
                calls[call_id] = owner, call
            elif "input" in payload:
                calls[call_id][1].arguments = payload["input"]
        elif event_type == "tool.updated" and kind in {"result", "error"}:
            call_id = payload["toolCallId"]
            if call_id not in calls:
                continue
            owner, _ = calls[call_id]
            result = payload.get("result", payload.get("error"))
            content = result.get("content", result) if isinstance(result, dict) else result
            observation = ObservationResult(
                source_call_id=call_id,
                content=content if isinstance(content, str) else json.dumps(content, ensure_ascii=False),
                extra={"kind": kind, "success": result.get("success")} if isinstance(result, dict) else {"kind": kind},
            )
            if owner.observation is None:
                owner.observation = Observation(results=[])
            owner.observation.results = [r for r in owner.observation.results if r.source_call_id != call_id] + [
                observation
            ]
        elif event_type == "turn.completed":
            completed = True
            for key in ("inputTokens", "outputTokens", "cacheReadTokens"):
                value = payload.get("usage", {}).get(key)
                if value is not None:
                    totals[key] = totals.get(key, 0) + value
    if not messages:
        return None
    return Trajectory(
        schema_version="ATIF-v1.7",
        session_id=session_id,
        agent=Agent(name="zcode", version=agent_version or "unknown", model_name=model_name),
        steps=steps,
        notes="One agent step per model.streaming assistantMessageId. Token totals cover completed turns only.",
        extra={"turn_completed": completed},
        final_metrics=FinalMetrics(
            total_prompt_tokens=totals.get("inputTokens"),
            total_completion_tokens=totals.get("outputTokens"),
            total_cached_tokens=totals.get("cacheReadTokens"),
            total_steps=len(steps),
        ),
    )
