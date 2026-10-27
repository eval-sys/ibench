from __future__ import annotations

import asyncio
from pathlib import Path

from harbor.agents.capabilities import AgentCapabilities
from harbor.agents.nop import NopAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class SleepAgent(NopAgent):
    """Hold a prepared Harbor trial until its owner releases it."""

    capabilities = AgentCapabilities()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ready = asyncio.Event()
        self.release = asyncio.Event()

    @staticmethod
    def name() -> str:
        return "sleep"

    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        prompt = Path(self.logs_dir) / "instruction.md"
        prompt.write_text(instruction, encoding="utf-8")
        await environment.upload_file(prompt, "/logs/agent/instruction.md")
        self.ready.set()
        await self.release.wait()
