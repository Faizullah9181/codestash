"""Ollama provider implementation — OpenAI-compatible local LLM."""

from __future__ import annotations

from app.agentic.providers.openai import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    async def _get_client(self):
        from openai import AsyncOpenAI

        base_url = self.config.base_url or "http://localhost:11434/v1"
        return AsyncOpenAI(api_key="ollama", base_url=base_url)
