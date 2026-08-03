"""Agentic AI Framework — Configuration Models."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BACKEND_ROOT / ".env")
_load_dotenv(PROJECT_ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _first_env(names: tuple[str, ...], default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _csv_env(name: str, default: list[str]) -> list[str]:
    value = os.environ.get(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


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


PROVIDER_ENV_VARS = {
    ProviderType.OPENAI.value: ("OPENAI_API_KEY", "OPENAI_BASE_URL"),
    ProviderType.GEMINI.value: ("GEMINI_API_KEY", "GEMINI_BASE_URL"),
    ProviderType.ANTHROPIC.value: ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"),
    ProviderType.GROQ.value: ("GROQ_API_KEY", "GROQ_BASE_URL"),
    ProviderType.OPENROUTER.value: ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL"),
    ProviderType.AZURE_OPENAI.value: ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"),
    ProviderType.OLLAMA.value: ("OLLAMA_API_KEY", "OLLAMA_BASE_URL"),
    ProviderType.OPENAI_COMPATIBLE.value: (
        "OPENAI_COMPATIBLE_API_KEY",
        "OPENAI_COMPATIBLE_BASE_URL",
    ),
}


class ProviderConfig(BaseModel):
    type: ProviderType
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    extra: dict[str, Any] = Field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "model": self.model,
            "base_url": self.base_url or "(default)",
            "api_key_configured": bool(self.api_key.strip()),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "extra": self.extra,
        }


class OrchestrationConfig(BaseModel):
    framework: OrchestrationFramework = OrchestrationFramework.LANGCHAIN
    config: dict[str, Any] = Field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        return {"framework": self.framework.value, "config": self.config}


class PatternConfig(BaseModel):
    type: PatternType
    config: dict[str, Any] = Field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        return {"type": self.type.value, "config": self.config}


class MemoryConfig(BaseModel):
    backend: MemoryBackend = MemoryBackend.SIMPLE
    connection_string: str = ""
    config: dict[str, Any] = Field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        return {
            "backend": self.backend.value,
            "configured": bool(self.connection_string.strip()),
            "config": self.config,
        }


class MCPConfig(BaseModel):
    servers: list[dict[str, Any]] = Field(default_factory=list)


class TelemetryConfig(BaseModel):
    enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""

    def describe(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "langfuse_public_key": bool(self.langfuse_public_key.strip()),
            "langfuse_secret_key": bool(self.langfuse_secret_key.strip()),
            "langfuse_host": self.langfuse_host,
        }


class AgentOpsConfig(BaseModel):
    enabled: bool = False
    api_key: str = ""
    capture_content: bool = False
    default_tags: str = "codestash,fastapi"
    environment: str = "development"
    export_flush_interval: int = 1000
    max_wait_time: int = 5000
    max_queue_size: int = 512

    @property
    def is_configured(self) -> bool:
        return self.enabled and bool(self.api_key.strip())

    @property
    def tags(self) -> list[str]:
        configured = [tag.strip() for tag in self.default_tags.split(",") if tag.strip()]
        environment_tag = f"environment:{self.environment.strip() or 'development'}"
        return list(dict.fromkeys([*configured, environment_tag]))

    def describe(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "configured": self.is_configured,
            "api_key": bool(self.api_key.strip()),
            "capture_content": self.capture_content,
            "default_tags": self.tags,
            "environment": self.environment,
            "export_flush_interval": self.export_flush_interval,
            "max_wait_time": self.max_wait_time,
            "max_queue_size": self.max_queue_size,
        }


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
    agentops: AgentOpsConfig = Field(default_factory=AgentOpsConfig)

    @classmethod
    def from_env(cls, name: str | None = None) -> AgentConfig:
        provider_type = ProviderType(_env("AGENT_PROVIDER_TYPE", ProviderType.OPENAI.value))
        api_key_env, base_url_env = PROVIDER_ENV_VARS[provider_type.value]
        config = cls(
            name=name or _env("AGENT_NAME", "agent"),
            description=_env("AGENT_DESCRIPTION", ""),
            provider=ProviderConfig(
                type=provider_type,
                api_key=_first_env((api_key_env, "PROVIDER_API_KEY"), ""),
                base_url=_first_env((base_url_env, "AGENT_BASE_URL"), ""),
                model=_env("AGENT_MODEL", "gpt-4o"),
                temperature=_float_env("AGENT_TEMPERATURE", 0.7),
                max_tokens=_int_env("AGENT_MAX_TOKENS", 4096),
                extra={
                    "orchestration_framework": _env("AGENT_ORCHESTRATION_FRAMEWORK", "langchain"),
                    "pattern": _env("AGENT_PATTERN", PatternType.REACT.value),
                    "mcp_servers": _csv_env("AGENT_MCP_SERVERS", []),
                },
            ),
            orchestration=OrchestrationConfig(
                framework=OrchestrationFramework(
                    _env("AGENT_ORCHESTRATION_FRAMEWORK", OrchestrationFramework.LANGCHAIN.value)
                )
            ),
            pattern=PatternConfig(type=PatternType(_env("AGENT_PATTERN", PatternType.REACT.value))),
            memory=MemoryConfig(
                backend=MemoryBackend(_env("AGENT_MEMORY_BACKEND", MemoryBackend.SIMPLE.value)),
                connection_string=_env("AGENT_MEMORY_CONNECTION_STRING", ""),
            ),
            telemetry=TelemetryConfig(
                enabled=_env("AGENT_TELEMETRY_ENABLED", "false").lower() in {"1", "true", "yes"},
                langfuse_public_key=_env("LANGFUSE_PUBLIC_KEY", ""),
                langfuse_secret_key=_env("LANGFUSE_SECRET_KEY", ""),
                langfuse_host=_env("LANGFUSE_HOST", ""),
            ),
            tools=_csv_env("AGENT_TOOLS", []),
            agentops=AgentOpsConfig(
                enabled=_env("AGENTOPS_ENABLED", "false").lower() in {"1", "true", "yes"},
                api_key=_env("AGENTOPS_API_KEY", ""),
                capture_content=_env("AGENTOPS_CAPTURE_CONTENT", "false").lower()
                in {"1", "true", "yes"},
                default_tags=_env("AGENTOPS_TAGS", "codestash,fastapi"),
                environment=_env("AGENTOPS_ENVIRONMENT", _env("ENV", "development")),
                export_flush_interval=_int_env("AGENTOPS_EXPORT_FLUSH_INTERVAL", 1000),
                max_wait_time=_int_env("AGENTOPS_MAX_WAIT_TIME", 5000),
                max_queue_size=_int_env("AGENTOPS_MAX_QUEUE_SIZE", 512),
            ),
        )
        return config

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "provider": self.provider.describe(),
            "orchestration": self.orchestration.describe(),
            "pattern": self.pattern.describe(),
            "memory": self.memory.describe(),
            "telemetry": self.telemetry.describe(),
            "agentops": self.agentops.describe(),
            "tools": self.tools,
            "mcp": self.mcp.model_dump(),
        }


__all__ = ["AgentConfig", "AgentOpsConfig", "PatternType", "ProviderType"]
