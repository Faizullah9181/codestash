"""Agentic AI Framework — CLI entry point.

Usage:
    agentic init
    agentic providers add <type> [--model] [--api-key] [--base-url]
    agentic providers list
    agentic orchestration use <framework>
    agentic pattern use <pattern>
    agentic run <task>
    agentic dev
    agentic inspect
    agentic mcp add <server>
    agentic create <project-name>
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer
import yaml

from app.agentic.config import (
    AgentConfig,
    OrchestrationConfig,
    OrchestrationFramework,
    PatternConfig,
    PatternType,
    ProviderConfig,
    ProviderType,
)
from app.agentic.templates import generate_project

app = typer.Typer(help="Agentic AI Framework — build, orchestrate, and run agentic AI systems.")
providers_app = typer.Typer(help="Manage LLM providers.")
orchestration_app = typer.Typer(help="Manage orchestration frameworks.")
pattern_app = typer.Typer(help="Manage agentic design patterns.")
mcp_app = typer.Typer(help="Manage MCP servers.")

app.add_typer(providers_app, name="providers")
app.add_typer(orchestration_app, name="orchestration")
app.add_typer(pattern_app, name="pattern")
app.add_typer(mcp_app, name="mcp")

CONFIG_FILE = Path("agentic.yaml")
STATE_FILE = Path(".agentic_state.json")


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _load_config() -> AgentConfig:
    if CONFIG_FILE.exists():
        data = yaml.safe_load(CONFIG_FILE.read_text()) or {}
        return AgentConfig(**data)
    return AgentConfig()


def _save_config(config: AgentConfig) -> None:
    CONFIG_FILE.write_text(yaml.dump(json.loads(config.model_dump_json()), default_flow_style=False))


# ── Init ──────────────────────────────────────────────────────────────────────

@app.command()
def init(force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config")):
    """Initialize an agentic AI project in the current directory."""
    if CONFIG_FILE.exists() and not force:
        typer.echo("agentic.yaml already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    config = AgentConfig(
        name=typer.prompt("Project name", default="my-agent"),
        description=typer.prompt("Description", default="An agentic AI project"),
        provider=ProviderConfig(
            type=ProviderType(typer.prompt("Provider type", default="openai")),
            model=typer.prompt("Model", default="gpt-4o"),
        ),
        orchestration=OrchestrationConfig(
            framework=OrchestrationFramework(typer.prompt("Orchestration framework", default="langchain")),
        ),
        pattern=PatternConfig(
            type=PatternType(typer.prompt("Pattern type", default="react")),
        ),
    )
    _save_config(config)
    typer.echo(f"✓ Initialized {config.name} in {CONFIG_FILE}")


# ── Providers ─────────────────────────────────────────────────────────────────

@providers_app.command(name="add")
def providers_add(
    provider_type: str = typer.Argument(..., help="Provider type: openai, gemini, anthropic, groq, ollama, openai-compatible"),
    model: str = typer.Option("", "--model", "-m", help="Model name"),
    api_key: str = typer.Option("", "--api-key", "-k", help="API key"),
    base_url: str = typer.Option("", "--base-url", "-u", help="Base URL for OpenAI-compatible endpoints"),
):
    """Add or configure an LLM provider."""
    config = _load_config()
    try:
        ptype = ProviderType(provider_type)
    except ValueError:
        typer.echo(f"Unknown provider type: {provider_type}")
        typer.echo(f"Available: {', '.join(t.value for t in ProviderType)}")
        raise typer.Exit(1)

    config.provider = ProviderConfig(
        type=ptype,
        model=model or typer.prompt("Model", default="gpt-4o"),
        api_key=api_key or typer.prompt("API key", default=""),
        base_url=base_url or (typer.prompt("Base URL", default="") if ptype == ProviderType.OPENAI_COMPATIBLE else ""),
    )
    _save_config(config)
    typer.echo(f"✓ Provider set to {ptype.value} ({config.provider.model})")


@providers_app.command(name="list")
def providers_list():
    """List configured providers."""
    config = _load_config()
    typer.echo(f"Current provider: {config.provider.type.value}")
    typer.echo(f"  Model:      {config.provider.model}")
    typer.echo(f"  Base URL:   {config.provider.base_url or '(default)'}")
    typer.echo(f"  Temperature: {config.provider.temperature}")


# ── Orchestration ─────────────────────────────────────────────────────────────

@orchestration_app.command(name="use")
def orchestration_use(
    framework: str = typer.Argument(..., help="Framework: langchain, langgraph, openai-agents, google-adk, crewai, strands"),
):
    """Select the orchestration framework."""
    try:
        fw = OrchestrationFramework(framework)
    except ValueError:
        typer.echo(f"Unknown framework: {framework}")
        typer.echo(f"Available: {', '.join(f.value for f in OrchestrationFramework)}")
        raise typer.Exit(1)

    config = _load_config()
    config.orchestration = OrchestrationConfig(framework=fw)
    _save_config(config)
    typer.echo(f"✓ Orchestration set to {fw.value}")


# ── Pattern ───────────────────────────────────────────────────────────────────

@pattern_app.command(name="use")
def pattern_use(
    pattern: str = typer.Argument(..., help="Pattern: react, reflection, planner-executor, rag, swarm, sequential, ..."),
):
    """Select the agentic design pattern."""
    try:
        pt = PatternType(pattern)
    except ValueError:
        typer.echo(f"Unknown pattern: {pattern}")
        typer.echo(f"Available: {', '.join(p.value for p in PatternType)}")
        raise typer.Exit(1)

    config = _load_config()
    config.pattern = PatternConfig(type=pt)
    _save_config(config)
    typer.echo(f"✓ Pattern set to {pt.value}")


# ── Run ───────────────────────────────────────────────────────────────────────

@app.command()
def run(
    task: str = typer.Argument(..., help="The task or prompt to run"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream the output"),
):
    """Run the agent with a task."""
    config = _load_config()
    asyncio.run(_run_agent(config, task, stream))


async def _run_agent(config: AgentConfig, task: str, stream: bool) -> None:
    from app.agentic.agent import Agent
    agent = Agent.from_config(config.name, config)
    if stream:
        async for chunk in agent.stream(task):
            typer.echo(chunk, nl=False)
        typer.echo()
    else:
        result = await agent.run(task)
        typer.echo(result.final_output)


# ── Dev ───────────────────────────────────────────────────────────────────────

@app.command()
def dev():
    """Start interactive development mode."""
    config = _load_config()
    typer.echo(f"Agentic Dev Mode — {config.name}")
    typer.echo(f"  Provider: {config.provider.type.value} ({config.provider.model})")
    typer.echo(f"  Orchestration: {config.orchestration.framework.value}")
    typer.echo(f"  Pattern: {config.pattern.type.value}")
    typer.echo("Type 'exit' to quit, 'help' for commands.\n")
    asyncio.run(_dev_loop(config))


async def _dev_loop(config: AgentConfig) -> None:
    from app.agentic.agent import Agent
    agent = Agent.from_config(config.name, config)
    while True:
        try:
            task = typer.prompt(">", prompt_suffix=" ")
        except (KeyboardInterrupt, EOFError):
            typer.echo("\nGoodbye!")
            break
        if task.lower() in ("exit", "quit", "q"):
            typer.echo("Goodbye!")
            break
        if task.lower() == "help":
            typer.echo("Commands: exit/quit, help, clear, inspect")
            continue
        if task.lower() == "clear":
            if agent.memory:
                await agent.memory.clear()
            typer.echo("Memory cleared.")
            continue
        if task.lower() == "inspect":
            typer.echo(f"Name: {agent.name}")
            typer.echo(f"Provider: {agent.provider.config.type.value}")
            continue
        async for chunk in agent.stream(task):
            typer.echo(chunk, nl=False)
        typer.echo()


# ── Inspect ───────────────────────────────────────────────────────────────────

@app.command()
def inspect():
    """Inspect current project configuration."""
    config = _load_config()
    typer.echo(yaml.dump(json.loads(config.model_dump_json()), default_flow_style=False))


# ── Create ────────────────────────────────────────────────────────────────────

@app.command()
def create(
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    output: str = typer.Option(".", "--output", "-o", help="Output directory"),
    pattern: str = typer.Option("react", "--pattern", "-p", help="Agentic design pattern"),
):
    """Generate a complete agentic AI project."""
    config = _load_config()
    config.name = project_name
    try:
        config.pattern = PatternConfig(type=PatternType(pattern))
    except ValueError:
        typer.echo(f"Unknown pattern: {pattern}, using 'react'")
        config.pattern = PatternConfig(type=PatternType.REACT)

    output_dir = Path(output) / project_name
    generate_project(config, output_dir)
    typer.echo(f"✓ Created project '{project_name}' at {output_dir}")
    _list_tree(output_dir)


def _list_tree(path: Path, prefix: str = "") -> None:
    items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        typer.echo(f"{prefix}{connector}{item.name}")
        if item.is_dir():
            _list_tree(item, prefix + ("    " if is_last else "│   "))


# ── MCP ───────────────────────────────────────────────────────────────────────

@mcp_app.command(name="add")
def mcp_add(
    server: str = typer.Argument(..., help="MCP server: filesystem, github, postgres, brave-search, memory, puppeteer"),
):
    """Add an MCP server to the project."""
    from app.agentic.mcp import MCP_SERVER_TEMPLATES

    if server not in MCP_SERVER_TEMPLATES:
        typer.echo(f"Unknown MCP server: {server}")
        typer.echo(f"Available: {', '.join(MCP_SERVER_TEMPLATES.keys())}")
        raise typer.Exit(1)

    config = _load_config()
    template = MCP_SERVER_TEMPLATES[server]
    config.mcp.servers.append({
        "name": template.name,
        "command": template.command,
        "args": template.args,
        "env": template.env,
    })
    _save_config(config)
    typer.echo(f"✓ MCP server '{server}' added")


@mcp_app.command(name="list")
def mcp_list():
    """List configured MCP servers."""
    config = _load_config()
    if not config.mcp.servers:
        typer.echo("No MCP servers configured.")
        typer.echo(f"Available templates: {', '.join(_get_mcp_templates())}")
        return
    for s in config.mcp.servers:
        typer.echo(f"  {s['name']}: {s['command']} {' '.join(s.get('args', []))}")


def _get_mcp_templates() -> list[str]:
    from app.agentic.mcp import MCP_SERVER_TEMPLATES
    return list(MCP_SERVER_TEMPLATES.keys())


# ── Graph ─────────────────────────────────────────────────────────────────────

@app.command()
def graph():
    """Show the dependency graph of the current configuration."""
    config = _load_config()
    typer.echo(f"""
┌─────────────────────────────────────────┐
│  Agent: {config.name:<30} │
├─────────────────────────────────────────┤
│  Provider:      {config.provider.type.value:<23} │
│  Model:         {config.provider.model:<23} │
│  Orchestration: {config.orchestration.framework.value:<23} │
│  Pattern:       {config.pattern.type.value:<23} │
│  Memory:        {config.memory.backend.value:<23} │
│  MCP Servers:   {len(config.mcp.servers):<23} │
│  Telemetry:     {'enabled' if config.telemetry.enabled else 'disabled':<23} │
└─────────────────────────────────────────┘
""")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    app()


if __name__ == "__main__":
    main()
