"""Root agent for agentic.

Provider:      OpenAI (openai)
Orchestration: LangChain (langchain)
Pattern:       react (single topology)

Generated module. It uses the LangChain SDK directly:

* ``build_model``   binds OpenAI to LangChain.
* ``build_runtime`` assembles the react topology from LangChain primitives.
* ``Agent``         adapts that runtime to the application-facing interface.

Edit the instructions, tools and topology here — this is the one file that owns
the agent's behaviour.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

from app.agentic.config import AgentConfig
from app.agentic.memory import MemoryEntry, create_memory
from app.agentic.telemetry import Tracer

PROVIDER = "openai"
FRAMEWORK = "langchain"
PATTERN = "react"
APP_NAME = "agentic"

INSTRUCTIONS = (
    "You are a ReAct agent. Reason step by step about the request, call a tool when it "
    "would give you information you do not already have, then answer.\n"
    "State your reasoning briefly before the final answer."
)


@tool
def recall(query: str) -> str:
    """Look up previously stored context for the current task."""
    return f"no stored context for {query!r} yet"


TOOLS = [recall]


def build_model(config: AgentConfig) -> Any:
    """OpenAI is reached through the OpenAI-compatible chat completions API."""
    return ChatOpenAI(
        model=config.provider.model,
        api_key=config.provider.api_key or "not-needed",
        base_url=config.provider.base_url or None,
        temperature=config.provider.temperature,
        max_tokens=config.provider.max_tokens,
    )


def build_runtime(config: AgentConfig) -> Any:
    """LangChain's create_agent builds the model + tool-calling loop."""
    return create_agent(
        build_model(config),
        tools=TOOLS,
        system_prompt=INSTRUCTIONS,
        name=APP_NAME,
    )


@dataclass(slots=True)
class AgentResult:
    """Outcome of a single agent run."""

    final_output: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


class Agent:
    """LangChain agent exposed through a framework-agnostic interface."""

    def __init__(self, config: AgentConfig, runtime: Any) -> None:
        self.config = config
        self.runtime = runtime
        self.memory = create_memory(config.memory)
        self.tracer = Tracer(config.telemetry)
        self._steps: list[dict[str, Any]] = []

    @classmethod
    def from_config(cls, name: str | None = None, config: AgentConfig | None = None) -> "Agent":
        """Build the agent from environment-backed configuration."""
        config = config or AgentConfig.from_env(name=name or APP_NAME)
        return cls(config, build_runtime(config))

    async def run(self, task: str, user_id: str = "system") -> AgentResult:
        """Run the react topology once and return the structured result."""
        started = time.perf_counter()
        self._steps = []
        async with self.tracer.span(
            "agent.run", {"framework": FRAMEWORK, "pattern": PATTERN, "provider": PROVIDER}
        ):
            output = await self._invoke(task, user_id)
        await self._remember(task, output)
        return AgentResult(
            final_output=output,
            steps=list(self._steps),
            duration_ms=(time.perf_counter() - started) * 1000,
        )

    async def stream(self, task: str, user_id: str = "system") -> AsyncIterator[str]:
        """Yield output chunks as the topology produces them."""
        async for chunk in self._stream(task, user_id):
            yield chunk

    async def chat(self, message: str) -> str:
        """Convenience wrapper that returns only the final text."""
        return (await self.run(message)).final_output

    async def _invoke(self, task: str, user_id: str) -> str:
        del user_id
        state = await self.runtime.ainvoke({"messages": [("user", task)]})
        return str(getattr(state["messages"][-1], "content", "")).strip()

    async def _stream(self, task: str, user_id: str) -> AsyncIterator[str]:
        del user_id
        async for chunk, _meta in self.runtime.astream(
            {"messages": [("user", task)]}, stream_mode="messages"
        ):
            text = getattr(chunk, "content", "")
            if text:
                yield str(text)

    async def _remember(self, task: str, output: str) -> None:
        await self.memory.add(MemoryEntry(role="user", content=task))
        await self.memory.add(MemoryEntry(role="assistant", content=output))


root_agent = Agent.from_config(APP_NAME)
