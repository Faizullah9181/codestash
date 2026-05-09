"""Provider abstraction layer — unified interface for all LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from app.agentic.config import ProviderConfig, ProviderType


@dataclass
class LLMResponse:
    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    raw: Any = None


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMessage:
    role: str
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str = ""


class BaseProvider(ABC):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def generate(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
    ) -> LLMResponse: ...

    @abstractmethod
    async def stream(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]: ...

    @abstractmethod
    async def generate_with_tools(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]]
    ) -> LLMResponse: ...


def create_provider(config: ProviderConfig) -> BaseProvider:
    registry: dict[ProviderType, type[BaseProvider]] = {
        ProviderType.OPENAI: _lazy_import("app.agentic.providers.openai", "OpenAIProvider"),
        ProviderType.GEMINI: _lazy_import("app.agentic.providers.gemini", "GeminiProvider"),
        ProviderType.ANTHROPIC: _lazy_import(
            "app.agentic.providers.anthropic", "AnthropicProvider"
        ),
        ProviderType.GROQ: _lazy_import("app.agentic.providers.groq", "GroqProvider"),
        ProviderType.OLLAMA: _lazy_import("app.agentic.providers.ollama", "OllamaProvider"),
        ProviderType.OPENAI_COMPATIBLE: _lazy_import(
            "app.agentic.providers.openai_compatible", "OpenAICompatibleProvider"
        ),
        ProviderType.OPENROUTER: _lazy_import(
            "app.agentic.providers.openai_compatible", "OpenAICompatibleProvider"
        ),
        ProviderType.AZURE_OPENAI: _lazy_import(
            "app.agentic.providers.openai", "AzureOpenAIProvider"
        ),
    }
    provider_cls = registry.get(config.type)
    if provider_cls is None:
        raise ValueError(f"Unsupported provider: {config.type}")
    return provider_cls(config)


def _lazy_import(module_path: str, class_name: str) -> type[BaseProvider]:
    import importlib

    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)
