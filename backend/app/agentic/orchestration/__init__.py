"""Orchestration abstraction layer — unified interface for agentic frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from app.agentic.config import AgentConfig, OrchestrationFramework
from app.agentic.providers import BaseProvider


@dataclass
class AgentStep:
    agent_name: str
    action: str
    input: dict[str, Any] = field(default_factory=dict)
    output: Any = None
    error: str | None = None


@dataclass
class OrchestrationResult:
    steps: list[AgentStep] = field(default_factory=list)
    final_output: str = ""
    tokens_used: int = 0
    duration_ms: float = 0


class BaseOrchestrator(ABC):
    def __init__(self, config: AgentConfig, provider: BaseProvider) -> None:
        self.config = config
        self.provider = provider

    @abstractmethod
    async def run(
        self, task: str, context: dict[str, Any] | None = None
    ) -> OrchestrationResult: ...

    @abstractmethod
    async def stream(
        self, task: str, context: dict[str, Any] | None = None
    ) -> AsyncIterator[str]: ...


def create_orchestrator(config: AgentConfig, provider: BaseProvider) -> BaseOrchestrator:
    from app.agentic.orchestration.langchain import LangChainOrchestrator
    from app.agentic.orchestration.openai_agents import OpenAIAgentsOrchestrator
    from app.agentic.orchestration.google_adk import GoogleADKOrchestrator
    from app.agentic.orchestration.crewai import CrewAIOrchestrator

    registry: dict[OrchestrationFramework, type[BaseOrchestrator]] = {
        OrchestrationFramework.LANGCHAIN: LangChainOrchestrator,
        OrchestrationFramework.LANGGRAPH: LangChainOrchestrator,
        OrchestrationFramework.OPENAI_AGENTS: OpenAIAgentsOrchestrator,
        OrchestrationFramework.GOOGLE_ADK: GoogleADKOrchestrator,
        OrchestrationFramework.CREWAI: CrewAIOrchestrator,
        OrchestrationFramework.STRANDS: LangChainOrchestrator,
    }
    cls = registry.get(config.orchestration.framework)
    if cls is None:
        raise ValueError(f"Unsupported orchestration framework: {config.orchestration.framework}")
    return cls(config, provider)
