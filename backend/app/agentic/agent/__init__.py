"""Agent package for agentic.

Re-exports the generated agent so ``from app.agentic.agent import Agent`` keeps
working regardless of how ``agent.py`` is structured internally.
"""

from app.agentic.agent.agent import (
    FRAMEWORK,
    PATTERN,
    PROVIDER,
    Agent,
    AgentResult,
    build_model,
    build_runtime,
    root_agent,
)

__all__ = [
    "FRAMEWORK",
    "PATTERN",
    "PROVIDER",
    "Agent",
    "AgentResult",
    "build_model",
    "build_runtime",
    "root_agent",
]
