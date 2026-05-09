"""Anthropic provider implementation."""

from __future__ import annotations

from typing import Any, AsyncIterator

from app.agentic.providers import BaseProvider, LLMMessage, LLMResponse


class AnthropicProvider(BaseProvider):
    async def _get_client(self):
        from anthropic import AsyncAnthropic

        return AsyncAnthropic(api_key=self.config.api_key)

    async def generate(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
    ) -> LLMResponse:
        client = await self._get_client()
        system = ""
        msgs = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                msgs.append({"role": m.role, "content": m.content})
        resp = await client.messages.create(
            model=self.config.model,
            system=system or None,
            messages=msgs,
            tools=tools,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        return LLMResponse(
            content=text,
            model=resp.model,
            usage=resp.usage.__dict__ if resp.usage else {},
            raw=resp,
        )

    async def stream(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        system = ""
        msgs = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                msgs.append({"role": m.role, "content": m.content})
        async with client.messages.stream(
            model=self.config.model,
            system=system or None,
            messages=msgs,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def generate_with_tools(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        return await self.generate(messages, tools)
