"""Agent code templates for each pattern -- F433-style (factory + orchestrator + singleton)."""

_AGENT_TEMPLATES: dict[str, str] = {}

# React -----------------------------------------------------------------------

_AGENT_TEMPLATES[
    "react"
] = '''"""ReAct agent -- {name} ({pattern} / {provider} / {fw})."""

from __future__ import annotations

from typing import AsyncIterator

from app.agentic.config import AgentConfig
from app.agentic.memory import Memory, MemoryEntry
from app.agentic.telemetry import Tracer

{provider_import}
{compat_block}

def build_root_agent(config: AgentConfig | None = None) -> "{class_name}Agent":
    """Factory: construct the root {pattern} agent."""
    return {class_name}Agent(config)


class {class_name}Agent:
    """Root orchestrator for {name} -- {pattern} pattern."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self._config = config or AgentConfig()
{provider_init}
{compat_setup}
        self.memory = Memory()
        self.tracer = Tracer()
        self.max_iterations = 10

    async def run(self, task: str) -> str:
        await self.memory.add(MemoryEntry(role="user", content=task))
        messages = [
            {{"role": "system", "content": "You are a ReAct agent. Think step by step, act, observe, repeat."}},
            {{"role": "user", "content": task}},
        ]
        for _ in range(self.max_iterations):
            resp = await self._call(messages)
            if "FINAL ANSWER" in resp:
                result = resp.split("FINAL ANSWER:")[-1].strip()
                await self.memory.add(MemoryEntry(role="assistant", content=result))
                return result
            messages.append({{"role": "assistant", "content": resp}})
            messages.append({{"role": "user", "content": "Continue. Use FINAL ANSWER when done."}})
        await self.memory.add(MemoryEntry(role="assistant", content=resp))
        return resp

    async def stream(self, task: str) -> AsyncIterator[str]:
        messages = [{{"role": "user", "content": task}}]
        stream = await self._client.chat.completions.create(
            model=self._config.model, messages=messages, stream=True,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _call(self, messages: list[dict]) -> str:
        resp = await self._client.chat.completions.create(
            model=self._config.model, messages=messages,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        return resp.choices[0].message.content or ""


root_agent = build_root_agent()
"""Module-level singleton for {name}."""
'''

# Swarm -----------------------------------------------------------------------

_AGENT_TEMPLATES[
    "swarm"
] = '''"""Swarm agent -- {name} ({pattern} / {provider} / {fw})."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from app.agentic.config import AgentConfig
from app.agentic.memory import Memory, MemoryEntry
from app.agentic.telemetry import Tracer

{provider_import}
{compat_block}

class SwarmCoordinator:
    """Routes tasks to worker agents and aggregates results."""

    def __init__(self, agents: list) -> None:
        self.agents = agents

    async def dispatch(self, task: str) -> dict:
        tasks = [agent.run(task) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {{agent.name: str(r) for agent, r in zip(self.agents, results)}}


def build_root_agent(config: AgentConfig | None = None) -> "{class_name}Agent":
    """Factory: construct the root swarm agent."""
    return {class_name}Agent(config)


class {class_name}Agent:
    """Root orchestrator for {name} -- swarm of workers."""

    def __init__(self, config: AgentConfig | None = None, num_workers: int = 3) -> None:
        self._config = config or AgentConfig()
        self.name = self._config.name
{provider_init}
{compat_setup}
        self.memory = Memory()
        self.tracer = Tracer()
        self.num_workers = num_workers
        self.coordinator = SwarmCoordinator([self] * num_workers)

    async def run(self, task: str) -> str:
        await self.memory.add(MemoryEntry(role="user", content=task))
        messages = [
            {{"role": "system", "content": "You are part of an agent swarm. Coordinate with peers, execute your sub-task, share results."}},
            {{"role": "user", "content": task}},
        ]
        resp = await self._call(messages)
        await self.memory.add(MemoryEntry(role="assistant", content=resp))
        return resp

    async def stream(self, task: str) -> AsyncIterator[str]:
        messages = [{{"role": "user", "content": task}}]
        stream = await self._client.chat.completions.create(
            model=self._config.model, messages=messages, stream=True,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _call(self, messages: list[dict]) -> str:
        resp = await self._client.chat.completions.create(
            model=self._config.model, messages=messages,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        return resp.choices[0].message.content or ""


root_agent = build_root_agent()
"""Module-level singleton for {name}."""
'''

# Planner-Executor ------------------------------------------------------------

_AGENT_TEMPLATES[
    "planner-executor"
] = '''"""Planner-Executor agent -- {name} ({pattern} / {provider} / {fw})."""

from __future__ import annotations

from typing import AsyncIterator

from app.agentic.config import AgentConfig
from app.agentic.memory import Memory, MemoryEntry
from app.agentic.telemetry import Tracer

{provider_import}
{compat_block}

def build_root_agent(config: AgentConfig | None = None) -> "{class_name}Agent":
    """Factory: construct the root planner-executor agent."""
    return {class_name}Agent(config)


class {class_name}Agent:
    """Root orchestrator for {name} -- plans then executes."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self._config = config or AgentConfig()
{provider_init}
{compat_setup}
        self.memory = Memory()
        self.tracer = Tracer()

    async def plan(self, goal: str) -> list[str]:
        prompt = f"Break this goal into sequential sub-tasks. Return a numbered list.\\n\\nGoal: {{goal}}"
        resp = await self._call([{{"role": "user", "content": prompt}}])
        return [line.strip("- 0123456789. ") for line in resp.split("\\n") if line.strip()]

    async def run(self, task: str) -> str:
        await self.memory.add(MemoryEntry(role="user", content=task))
        steps = await self.plan(task)
        results = []
        for step in steps:
            resp = await self._call([{{"role": "user", "content": step}}])
            results.append(resp)
        final = "\\n".join(results)
        await self.memory.add(MemoryEntry(role="assistant", content=final))
        return final

    async def stream(self, task: str) -> AsyncIterator[str]:
        messages = [{{"role": "user", "content": task}}]
        stream = await self._client.chat.completions.create(
            model=self._config.model, messages=messages, stream=True,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _call(self, messages: list[dict]) -> str:
        resp = await self._client.chat.completions.create(
            model=self._config.model, messages=messages,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        return resp.choices[0].message.content or ""


root_agent = build_root_agent()
"""Module-level singleton for {name}."""
'''

# Reflection ------------------------------------------------------------------

_AGENT_TEMPLATES[
    "reflection"
] = '''"""Reflection agent -- {name} ({pattern} / {provider} / {fw})."""

from __future__ import annotations

from typing import AsyncIterator

from app.agentic.config import AgentConfig
from app.agentic.memory import Memory, MemoryEntry
from app.agentic.telemetry import Tracer

{provider_import}
{compat_block}

def build_root_agent(config: AgentConfig | None = None) -> "{class_name}Agent":
    """Factory: construct the root reflection agent."""
    return {class_name}Agent(config)


class {class_name}Agent:
    """Root orchestrator for {name} -- self-critique loop."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self._config = config or AgentConfig()
{provider_init}
{compat_setup}
        self.memory = Memory()
        self.tracer = Tracer()
        self.max_refinements = 3

    async def run(self, task: str) -> str:
        await self.memory.add(MemoryEntry(role="user", content=task))
        resp = await self._call([{{"role": "user", "content": task}}])
        for _ in range(self.max_refinements):
            critique = f"Critically review and improve this output:\\n\\n{{resp}}"
            refined = await self._call([{{"role": "user", "content": critique}}])
            if refined == resp:
                break
            resp = refined
        await self.memory.add(MemoryEntry(role="assistant", content=resp))
        return resp

    async def stream(self, task: str) -> AsyncIterator[str]:
        messages = [{{"role": "user", "content": task}}]
        stream = await self._client.chat.completions.create(
            model=self._config.model, messages=messages, stream=True,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _call(self, messages: list[dict]) -> str:
        resp = await self._client.chat.completions.create(
            model=self._config.model, messages=messages,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        return resp.choices[0].message.content or ""


root_agent = build_root_agent()
"""Module-level singleton for {name}."""
'''

# RAG -------------------------------------------------------------------------

_AGENT_TEMPLATES["rag"] = '''"""RAG agent -- {name} ({pattern} / {provider} / {fw})."""

from __future__ import annotations

from typing import AsyncIterator

from app.agentic.config import AgentConfig
from app.agentic.memory import Memory, MemoryEntry
from app.agentic.telemetry import Tracer

{provider_import}
{compat_block}

def build_root_agent(config: AgentConfig | None = None) -> "{class_name}Agent":
    """Factory: construct the root RAG agent."""
    return {class_name}Agent(config)


class {class_name}Agent:
    """Root orchestrator for {name} -- retrieval-augmented generation."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self._config = config or AgentConfig()
{provider_init}
{compat_setup}
        self.memory = Memory()
        self.tracer = Tracer()

    async def retrieve(self, query: str, k: int = 5) -> list[str]:
        entries = await self.memory.search(query, limit=k)
        return [e.content for e in entries]

    async def run(self, task: str) -> str:
        await self.memory.add(MemoryEntry(role="user", content=task))
        docs = await self.retrieve(task)
        context = "\\n".join(docs) if docs else "No relevant context found."
        prompt = f"Context:\\n{{context}}\\n\\nQuestion: {{task}}\\n\\nAnswer grounded in context:"
        resp = await self._call([{{"role": "user", "content": prompt}}])
        await self.memory.add(MemoryEntry(role="assistant", content=resp))
        return resp

    async def stream(self, task: str) -> AsyncIterator[str]:
        messages = [{{"role": "user", "content": task}}]
        stream = await self._client.chat.completions.create(
            model=self._config.model, messages=messages, stream=True,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _call(self, messages: list[dict]) -> str:
        resp = await self._client.chat.completions.create(
            model=self._config.model, messages=messages,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        return resp.choices[0].message.content or ""


root_agent = build_root_agent()
"""Module-level singleton for {name}."""
'''

# Sequential ------------------------------------------------------------------

_AGENT_TEMPLATES[
    "sequential"
] = '''"""Sequential agent -- {name} ({pattern} / {provider} / {fw})."""

from __future__ import annotations

from typing import AsyncIterator

from app.agentic.config import AgentConfig
from app.agentic.memory import Memory, MemoryEntry
from app.agentic.telemetry import Tracer

{provider_import}
{compat_block}

def build_root_agent(config: AgentConfig | None = None) -> "{class_name}Agent":
    """Factory: construct the root sequential pipeline agent."""
    return {class_name}Agent(config)


class {class_name}Agent:
    """Root orchestrator for {name} -- sequential processing pipeline."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self._config = config or AgentConfig()
{provider_init}
{compat_setup}
        self.memory = Memory()
        self.tracer = Tracer()

    async def run(self, task: str) -> str:
        await self.memory.add(MemoryEntry(role="user", content=task))
        messages = [
            {{"role": "system", "content": "You are a sequential pipeline stage. Process your input and pass the output forward."}},
            {{"role": "user", "content": task}},
        ]
        resp = await self._call(messages)
        await self.memory.add(MemoryEntry(role="assistant", content=resp))
        return resp

    async def stream(self, task: str) -> AsyncIterator[str]:
        messages = [{{"role": "user", "content": task}}]
        stream = await self._client.chat.completions.create(
            model=self._config.model, messages=messages, stream=True,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _call(self, messages: list[dict]) -> str:
        resp = await self._client.chat.completions.create(
            model=self._config.model, messages=messages,
            temperature=self._config.temperature, max_tokens=self._config.max_tokens,
        )
        return resp.choices[0].message.content or ""


root_agent = build_root_agent()
"""Module-level singleton for {name}."""
'''

# Alias all other patterns to existing templates -------------------------------
for _k in ("hierarchical", "planning", "tool-use", "autonomous"):
    _AGENT_TEMPLATES.setdefault(_k, _AGENT_TEMPLATES["react"])
_AGENT_TEMPLATES.setdefault("reviewer-critic", _AGENT_TEMPLATES["reflection"])
_AGENT_TEMPLATES.setdefault("debate", _AGENT_TEMPLATES["reflection"])
_AGENT_TEMPLATES.setdefault("parallel", _AGENT_TEMPLATES["swarm"])
_AGENT_TEMPLATES.setdefault("coordinator", _AGENT_TEMPLATES["swarm"])
_AGENT_TEMPLATES.setdefault("blackboard", _AGENT_TEMPLATES["swarm"])
