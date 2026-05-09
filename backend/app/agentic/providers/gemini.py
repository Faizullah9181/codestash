"""Gemini provider implementation."""

from __future__ import annotations

from typing import Any, AsyncIterator

from app.agentic.providers import BaseProvider, LLMMessage, LLMResponse


class GeminiProvider(BaseProvider):
    async def _get_client(self):
        from google import genai

        return genai.Client(api_key=self.config.api_key)

    async def generate(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
    ) -> LLMResponse:
        client = await self._get_client()
        contents = [{"role": _map_role(m.role), "parts": [{"text": m.content}]} for m in messages]
        resp = client.models.generate_content(
            model=self.config.model,
            contents=contents,
            config={
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
            },
        )
        return LLMResponse(content=resp.text or "", model=self.config.model, raw=resp)

    async def stream(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        contents = [{"role": _map_role(m.role), "parts": [{"text": m.content}]} for m in messages]
        for chunk in client.models.generate_content_stream(
            model=self.config.model,
            contents=contents,
            config={
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
            },
        ):
            if chunk.text:
                yield chunk.text

    async def generate_with_tools(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        return await self.generate(messages, tools)


def _map_role(role: str) -> str:
    mapping = {"assistant": "model", "user": "user", "system": "user"}
    return mapping.get(role, "user")
