"""Agentic AI Framework — a CLI-first framework for building agentic AI systems.

Usage:
    from app.agentic.agent import Agent
    from app.agentic.config import AgentConfig, ProviderConfig, ProviderType

    config = AgentConfig(
        name="my-agent",
        provider=ProviderConfig(type=ProviderType.OPENAI, model="gpt-4o"),
    )
    agent = Agent.from_config("my-agent", config)
    result = await agent.run("What is the capital of France?")
"""
