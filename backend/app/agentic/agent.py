"""Agent runtime — the core agent execution engine."""

from __future__ import annotations

from typing import Any, AsyncIterator

from app.agentic.config import AgentConfig, ProviderConfig, ProviderType
from app.agentic.memory import BaseMemory, MemoryEntry, create_memory
from app.agentic.orchestration import BaseOrchestrator, OrchestrationResult, create_orchestrator
from app.agentic.providers import BaseProvider, create_provider
from app.agentic.telemetry import Tracer


class Agent:
    def __init__(
        self,
        name: str,
        provider: BaseProvider,
        orchestrator: BaseOrchestrator,
        memory: BaseMemory | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self.name = name
        self.provider = provider
        self.orchestrator = orchestrator
        self.memory = memory
        self.tracer = tracer

    @classmethod
    def from_config(cls, name: str, config: AgentConfig | None = None) -> Agent:
        if config is None:
            config = AgentConfig(
                name=name, provider=ProviderConfig(type=ProviderType.OPENAI, model="gpt-4o")
            )
        provider = create_provider(config.provider)
        orchestrator = create_orchestrator(config, provider)
        memory = create_memory(config.memory)
        return cls(name=name, provider=provider, orchestrator=orchestrator, memory=memory)

    async def run(self, task: str, context: dict[str, Any] | None = None) -> OrchestrationResult:
        if self.memory:
            await self.memory.add(MemoryEntry(role="user", content=task))
        result = await self.orchestrator.run(task, context)
        if self.memory:
            await self.memory.add(MemoryEntry(role="assistant", content=result.final_output))
        return result

    async def stream(self, task: str, context: dict[str, Any] | None = None) -> AsyncIterator[str]:
        if self.memory:
            await self.memory.add(MemoryEntry(role="user", content=task))
        full_response = ""
        async for chunk in self.orchestrator.stream(task, context):
            full_response += chunk
            yield chunk
        if self.memory:
            await self.memory.add(MemoryEntry(role="assistant", content=full_response))

    async def chat(self, message: str) -> str:
        result = await self.run(message)
        return result.final_output
