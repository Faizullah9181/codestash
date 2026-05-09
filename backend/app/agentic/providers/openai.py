"""OpenAI provider implementation."""

from __future__ import annotations

from typing import Any, AsyncIterator

from app.agentic.providers import BaseProvider, LLMMessage, LLMResponse


class OpenAIProvider(BaseProvider):
    async def _get_client(self):
        from openai import AsyncOpenAI

        return AsyncOpenAI(
            api_key=self.config.api_key or None, base_url=self.config.base_url or None
        )

    async def generate(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
    ) -> LLMResponse:
        client = await self._get_client()
        resp = await client.chat.completions.create(
            model=self.config.model,
            messages=[m.__dict__ for m in messages],
            tools=tools,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        choice = resp.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            usage={"input": resp.usage.prompt_tokens, "output": resp.usage.completion_tokens}
            if resp.usage
            else {},
            finish_reason=choice.finish_reason or "stop",
            raw=resp,
        )

    async def stream(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        stream = await client.chat.completions.create(
            model=self.config.model,
            messages=[m.__dict__ for m in messages],
            stream=True,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_with_tools(
        self, messages: list[LLMMessage], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        return await self.generate(messages, tools)


class AzureOpenAIProvider(OpenAIProvider):
    async def _get_client(self):
        from openai import AsyncAzureOpenAI

        return AsyncAzureOpenAI(
            api_key=self.config.api_key,
            azure_endpoint=self.config.base_url,
            api_version=self.config.extra.get("api_version", "2024-02-15-preview"),
        )
