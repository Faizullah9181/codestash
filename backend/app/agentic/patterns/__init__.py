"""Agentic design patterns — architecture generators for multi-agent systems."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.agentic.config import AgentConfig, PatternType


@dataclass
class PatternStructure:
    name: str
    description: str
    folders: list[str]
    files: dict[str, str]
    config: dict[str, Any] = field(default_factory=dict)


class BasePattern(ABC):
    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    @abstractmethod
    def generate_structure(self) -> PatternStructure: ...

    @abstractmethod
    def system_prompt(self) -> str: ...


class ReActPattern(BasePattern):
    def generate_structure(self) -> PatternStructure:
        return PatternStructure(
            name="react",
            description="Reasoning + Acting loop agent",
            folders=["agents", "tools", "memory", "configs"],
            files={
                "agents/react_agent.py": _REACT_AGENT_TEMPLATE,
                "configs/agent.yaml": _REACT_CONFIG,
            },
        )

    def system_prompt(self) -> str:
        return (
            "You are a ReAct agent. Follow this cycle:\n"
            "1. Thought: analyze the situation\n"
            "2. Action: execute a tool\n"
            "3. Observation: process the result\n"
            "4. Repeat until the task is complete"
        )


class ReflectionPattern(BasePattern):
    def generate_structure(self) -> PatternStructure:
        return PatternStructure(
            name="reflection",
            description="Agent with self-reflection and improvement loop",
            folders=["agents", "tools", "memory", "configs"],
            files={
                "agents/executor.py": _EXECUTOR_TEMPLATE,
                "agents/critic.py": _CRITIC_TEMPLATE,
                "configs/agent.yaml": _REFLECTION_CONFIG,
            },
        )

    def system_prompt(self) -> str:
        return (
            "You are a self-reflective agent. After each action:\n"
            "1. Execute the requested task\n"
            "2. Critically evaluate your own output\n"
            "3. Identify improvements\n"
            "4. Refine and re-execute if needed"
        )


class PlannerExecutorPattern(BasePattern):
    def generate_structure(self) -> PatternStructure:
        return PatternStructure(
            name="planner-executor",
            description="Planner + Executor hierarchical pattern",
            folders=["agents", "tools", "memory", "configs", "workflows"],
            files={
                "agents/planner.py": _PLANNER_TEMPLATE,
                "agents/executor.py": _EXECUTOR_TEMPLATE,
                "workflows/main.py": _WORKFLOW_TEMPLATE,
                "configs/agent.yaml": _PLANNER_EXECUTOR_CONFIG,
            },
        )

    def system_prompt(self) -> str:
        return (
            "You are a planning agent. Break complex tasks into steps:\n"
            "1. Decompose the goal into sub-tasks\n"
            "2. Assign each sub-task to an executor\n"
            "3. Aggregate results\n"
            "4. Validate the final output"
        )


class RAGPattern(BasePattern):
    def generate_structure(self) -> PatternStructure:
        return PatternStructure(
            name="rag",
            description="Retrieval-Augmented Generation agent",
            folders=["agents", "tools", "memory", "configs", "data"],
            files={
                "agents/rag_agent.py": _RAG_AGENT_TEMPLATE,
                "tools/retriever.py": _RETRIEVER_TEMPLATE,
                "configs/agent.yaml": _RAG_CONFIG,
            },
        )

    def system_prompt(self) -> str:
        return (
            "You are a RAG agent. For every query:\n"
            "1. Retrieve relevant documents\n"
            "2. Evaluate relevance\n"
            "3. Generate a response grounded in retrieved context\n"
            "4. Cite sources"
        )


class SwarmPattern(BasePattern):
    def generate_structure(self) -> PatternStructure:
        return PatternStructure(
            name="swarm",
            description="Multi-agent swarm coordination pattern",
            folders=["agents", "tools", "memory", "configs", "workflows"],
            files={
                "agents/swarm_agent.py": _SWARM_AGENT_TEMPLATE,
                "workflows/coordinator.py": _COORDINATOR_TEMPLATE,
                "configs/agent.yaml": _SWARM_CONFIG,
            },
        )

    def system_prompt(self) -> str:
        return (
            "You are part of an agent swarm. Coordinate with peers:\n"
            "1. Evaluate which sub-task you can handle best\n"
            "2. Execute your specialized sub-task\n"
            "3. Share results with the swarm\n"
            "4. Accept feedback from coordinator"
        )


class SequentialPattern(BasePattern):
    def generate_structure(self) -> PatternStructure:
        return PatternStructure(
            name="sequential",
            description="Sequential pipeline of specialized agents",
            folders=["agents", "tools", "memory", "configs", "workflows"],
            files={
                "agents/stage1.py": _STAGE_TEMPLATE,
                "agents/stage2.py": _STAGE_TEMPLATE,
                "agents/stage3.py": _STAGE_TEMPLATE,
                "workflows/pipeline.py": _PIPELINE_TEMPLATE,
                "configs/agent.yaml": _SEQUENTIAL_CONFIG,
            },
        )

    def system_prompt(self) -> str:
        return "You are a stage in a sequential pipeline. Process your input and pass the output to the next stage."


PATTERN_REGISTRY: dict[PatternType, type[BasePattern]] = {
    PatternType.REACT: ReActPattern,
    PatternType.TOOL_USE: ReActPattern,
    PatternType.REFLECTION: ReflectionPattern,
    PatternType.PLANNING: PlannerExecutorPattern,
    PatternType.RAG: RAGPattern,
    PatternType.AUTONOMOUS: ReActPattern,
    PatternType.SEQUENTIAL: SequentialPattern,
    PatternType.PARALLEL: SwarmPattern,
    PatternType.REVIEWER_CRITIC: ReflectionPattern,
    PatternType.PLANNER_EXECUTOR: PlannerExecutorPattern,
    PatternType.HIERARCHICAL: PlannerExecutorPattern,
    PatternType.SWARM: SwarmPattern,
    PatternType.DEBATE: ReflectionPattern,
    PatternType.COORDINATOR: SwarmPattern,
    PatternType.BLACKBOARD: SwarmPattern,
}


def create_pattern(config: AgentConfig) -> BasePattern:
    cls = PATTERN_REGISTRY.get(config.pattern.type)
    if cls is None:
        raise ValueError(f"Unsupported pattern: {config.pattern.type}")
    return cls(config)


# ── Templates ─────────────────────────────────────────────────────────────────

_REACT_AGENT_TEMPLATE = '''"""ReAct agent — Reasoning + Acting loop."""

from app.agentic.agent import Agent


class ReActAgent(Agent):
    async def run(self, task: str) -> str:
        messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": task}]
        for _ in range(self.max_iterations):
            resp = await self.provider.generate(messages)
            if "FINAL ANSWER" in resp.content:
                return resp.content.split("FINAL ANSWER:")[-1].strip()
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": "Continue. Use FINAL ANSWER when done."})
        return resp.content
'''

_REACT_CONFIG = """agent:
  name: react-agent
  pattern: react
  max_iterations: 10
"""

_REFLECTION_CONFIG = """agent:
  name: reflection-agent
  pattern: reflection
  roles:
    - executor
    - critic
"""

_PLANNER_EXECUTOR_CONFIG = """agent:
  name: planner-executor
  pattern: planner-executor
  roles:
    - planner
    - executor
"""

_RAG_CONFIG = """agent:
  name: rag-agent
  pattern: rag
  vector_store: chroma
  embedding_model: text-embedding-3-small
"""

_SWARM_CONFIG = """agent:
  name: swarm-agent
  pattern: swarm
  num_agents: 5
  coordination: round-robin
"""

_SEQUENTIAL_CONFIG = """agent:
  name: sequential-pipeline
  pattern: sequential
  stages:
    - input-processor
    - analyzer
    - output-formatter
"""

_EXECUTOR_TEMPLATE = '''"""Executor agent."""

from app.agentic.agent import Agent


class ExecutorAgent(Agent):
    async def run(self, task: str) -> str:
        resp = await self.provider.generate([{"role": "user", "content": task}])
        return resp.content
'''

_CRITIC_TEMPLATE = '''"""Critic agent — reviews and suggests improvements."""

from app.agentic.agent import Agent


class CriticAgent(Agent):
    async def review(self, content: str) -> str:
        prompt = f"Critically review the following output and suggest improvements:\\n\\n{content}"
        resp = await self.provider.generate([{"role": "user", "content": prompt}])
        return resp.content
'''

_PLANNER_TEMPLATE = '''"""Planner agent — decomposes tasks into steps."""

from app.agentic.agent import Agent


class PlannerAgent(Agent):
    async def plan(self, goal: str) -> list[str]:
        prompt = f"Break this goal into sequential sub-tasks. Return a numbered list.\\n\\nGoal: {goal}"
        resp = await self.provider.generate([{"role": "user", "content": prompt}])
        return [line.strip("- 0123456789. ") for line in resp.content.split("\\n") if line.strip()]
'''

_WORKFLOW_TEMPLATE = '''"""Main workflow — orchestrates planner + executor."""

import asyncio
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent


async def run_workflow(goal: str) -> str:
    planner = PlannerAgent()
    executor = ExecutorAgent()
    steps = await planner.plan(goal)
    results = []
    for step in steps:
        result = await executor.run(step)
        results.append(result)
    return "\\n".join(results)
'''

_PIPELINE_TEMPLATE = '''"""Sequential pipeline workflow."""

import asyncio


async def run_pipeline(task: str, stages: list) -> str:
    result = task
    for stage in stages:
        result = await stage.run(result)
    return result
'''

_RAG_AGENT_TEMPLATE = '''"""RAG agent — retrieval-augmented generation."""

from app.agentic.agent import Agent


class RAGAgent(Agent):
    async def run(self, query: str) -> str:
        docs = await self.retrieve(query)
        context = "\\n".join(docs)
        prompt = f"Context:\\n{context}\\n\\nQuestion: {query}\\n\\nAnswer grounded in context:"
        resp = await self.provider.generate([{"role": "user", "content": prompt}])
        return resp.content
'''

_RETRIEVER_TEMPLATE = '''"""Document retriever tool."""

import chromadb


class Retriever:
    def __init__(self, collection_name: str = "documents"):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)

    def search(self, query: str, k: int = 5) -> list[str]:
        results = self.collection.query(query_texts=[query], n_results=k)
        return results["documents"][0] if results["documents"] else []
'''

_SWARM_AGENT_TEMPLATE = '''"""Swarm agent — coordinates with peer agents."""

from app.agentic.agent import Agent


class SwarmAgent(Agent):
    async def run(self, task: str) -> str:
        resp = await self.provider.generate([{"role": "user", "content": task}])
        return resp.content

    async def coordinate(self, peers: list, task: str) -> dict:
        results = {}
        for peer in peers:
            results[peer.name] = await peer.run(task)
        return results
'''

_COORDINATOR_TEMPLATE = '''"""Swarm coordinator — routes tasks to agents."""

import asyncio


class SwarmCoordinator:
    def __init__(self, agents: list):
        self.agents = agents

    async def dispatch(self, task: str) -> dict:
        tasks = [agent.run(task) for agent in self.agents]
        results = await asyncio.gather(*tasks)
        return {agent.name: result for agent, result in zip(self.agents, results)}
'''

_STAGE_TEMPLATE = '''"""Pipeline stage agent."""

from app.agentic.agent import Agent


class StageAgent(Agent):
    async def run(self, task: str) -> str:
        resp = await self.provider.generate([{"role": "user", "content": task}])
        return resp.content
'''
