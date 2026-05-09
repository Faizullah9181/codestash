"""OpenAI-compatible provider — any endpoint matching the OpenAI API spec."""

from __future__ import annotations

from app.agentic.providers.openai import OpenAIProvider


class OpenAICompatibleProvider(OpenAIProvider):
    async def _get_client(self):
        from openai import AsyncOpenAI

        return AsyncOpenAI(api_key=self.config.api_key or "local", base_url=self.config.base_url)
