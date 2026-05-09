"""OpenAI Agents SDK orchestrator."""

from __future__ import annotations

import time
from typing import Any, AsyncIterator

from app.agentic.config import AgentConfig
from app.agentic.orchestration import AgentStep, BaseOrchestrator, OrchestrationResult
from app.agentic.providers import BaseProvider, LLMMessage


class OpenAIAgentsOrchestrator(BaseOrchestrator):
    def __init__(self, config: AgentConfig, provider: BaseProvider) -> None:
        super().__init__(config, provider)

    async def run(self, task: str, context: dict[str, Any] | None = None) -> OrchestrationResult:
        start = time.monotonic()
        steps: list[AgentStep] = []

        system_prompt = (
            context.get("system_prompt", "You are a helpful AI assistant.")
            if context
            else "You are a helpful AI assistant."
        )
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=task),
        ]

        agent_tools = context.get("tools") if context else None
        step = AgentStep(agent_name=self.config.name, action="run", input={"task": task})
        resp = await self.provider.generate(messages, agent_tools)
        step.output = resp.content
        steps.append(step)

        return OrchestrationResult(
            steps=steps,
            final_output=resp.content,
            tokens_used=resp.usage.get("input", 0) + resp.usage.get("output", 0),
            duration_ms=(time.monotonic() - start) * 1000,
        )

    async def stream(self, task: str, context: dict[str, Any] | None = None) -> AsyncIterator[str]:
        system_prompt = (
            context.get("system_prompt", "You are a helpful AI assistant.")
            if context
            else "You are a helpful AI assistant."
        )
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=task),
        ]
        async for chunk in self.provider.stream(messages):
            yield chunk
