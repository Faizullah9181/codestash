"""Groq provider implementation — OpenAI-compatible."""

from __future__ import annotations

from app.agentic.providers.openai import OpenAIProvider


class GroqProvider(OpenAIProvider):
    async def _get_client(self):
        from openai import AsyncOpenAI

        return AsyncOpenAI(api_key=self.config.api_key, base_url="https://api.groq.com/openai/v1")
