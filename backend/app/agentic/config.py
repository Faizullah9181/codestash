"""Agentic AI Framework — Configuration Models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    AZURE_OPENAI = "azure-openai"
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai-compatible"


class OrchestrationFramework(str, Enum):
    OPENAI_AGENTS = "openai-agents"
    GOOGLE_ADK = "google-adk"
    LANGCHAIN = "langchain"
    LANGGRAPH = "langgraph"
    STRANDS = "strands"
    CREWAI = "crewai"


class PatternType(str, Enum):
    REACT = "react"
    TOOL_USE = "tool-use"
    REFLECTION = "reflection"
    PLANNING = "planning"
    RAG = "rag"
    AUTONOMOUS = "autonomous"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    REVIEWER_CRITIC = "reviewer-critic"
    PLANNER_EXECUTOR = "planner-executor"
    HIERARCHICAL = "hierarchical"
    SWARM = "swarm"
    DEBATE = "debate"
    COORDINATOR = "coordinator"
    BLACKBOARD = "blackboard"


class MemoryBackend(str, Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    REDIS = "redis"
    CHROMA = "chroma"
    WEAVIATE = "weaviate"
    SIMPLE = "simple"


class ProviderConfig(BaseModel):
    type: ProviderType
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    extra: dict[str, Any] = Field(default_factory=dict)


class OrchestrationConfig(BaseModel):
    framework: OrchestrationFramework = OrchestrationFramework.LANGCHAIN
    config: dict[str, Any] = Field(default_factory=dict)


class PatternConfig(BaseModel):
    type: PatternType
    config: dict[str, Any] = Field(default_factory=dict)


class MemoryConfig(BaseModel):
    backend: MemoryBackend = MemoryBackend.SIMPLE
    connection_string: str = ""
    config: dict[str, Any] = Field(default_factory=dict)


class MCPConfig(BaseModel):
    servers: list[dict[str, Any]] = Field(default_factory=list)


class TelemetryConfig(BaseModel):
    enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""


class AgentConfig(BaseModel):
    name: str = "agent"
    description: str = ""
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    orchestration: OrchestrationConfig = Field(default_factory=OrchestrationConfig)
    pattern: PatternConfig = Field(default_factory=PatternConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    tools: list[str] = Field(default_factory=list)
