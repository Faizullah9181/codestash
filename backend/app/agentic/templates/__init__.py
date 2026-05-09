"""Template generator — scaffold complete agentic AI projects."""

from __future__ import annotations

from pathlib import Path

from app.agentic.config import AgentConfig
from app.agentic.patterns import PATTERN_REGISTRY


def generate_project(config: AgentConfig, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    pattern_cls = PATTERN_REGISTRY.get(config.pattern.type)
    if pattern_cls:
        structure = pattern_cls(config).generate_structure()
    else:
        from app.agentic.patterns import PatternStructure

        structure = PatternStructure(
            name=config.pattern.type.value, description="", folders=["agents", "configs"], files={}
        )

    for folder in structure.folders:
        (output_dir / folder).mkdir(parents=True, exist_ok=True)

    for filepath, content in structure.files.items():
        full_path = output_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    _write_config(config, output_dir / "configs" / "agent.yaml")
    _write_env_example(output_dir)
    _write_main(output_dir, config)

    return output_dir


def _write_config(config: AgentConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""agent:
  name: {config.name}
  description: "{config.description}"

provider:
  type: {config.provider.type.value}
  model: {config.provider.model}
  api_key: ${{PROVIDER_API_KEY}}
  base_url: {config.provider.base_url}
  temperature: {config.provider.temperature}

orchestration:
  framework: {config.orchestration.framework.value}

pattern:
  type: {config.pattern.type.value}

memory:
  backend: {config.memory.backend.value}
"""
    path.write_text(content)


def _write_env_example(output_dir: Path) -> None:
    env = """# Provider API keys (uncomment as needed)
PROVIDER_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=

# Memory
DATABASE_URL=

# Telemetry
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
"""
    (output_dir / ".env.example").write_text(env)


def _write_main(output_dir: Path, config: AgentConfig) -> None:
    main_py = f'''"""Main entry point for {config.name} agent."""

import asyncio
from app.agentic.agent import Agent


async def main():
    agent = Agent.from_config("{config.name}")
    task = input("Enter your task: ")
    async for chunk in agent.stream(task):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
'''
    (output_dir / "main.py").write_text(main_py)
