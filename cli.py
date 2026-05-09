#!/usr/bin/env python3
"""Agentic -- full-stack project scaffolding CLI.

Run without arguments for interactive mode:
    python3 cli.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_SRC = ROOT / "backend"
FRONTEND_SRC = ROOT / "frontend"
TERRAFORM_SRC = ROOT / "terraform"
DOCKER_COMPOSE_SRC = ROOT / "docker-compose.yml"
GITHUB_SRC = ROOT / ".github"
AGENT_SRC = ROOT / ".agent"
AGENTS_MD_SRC = ROOT / "AGENTS.md"
CONFIG_FILE = Path("agentic.yaml")

PROVIDER_TYPES = [
    "openai", "gemini", "anthropic", "groq",
    "openrouter", "azure-openai", "ollama", "openai-compatible",
]

PROVIDER_MODELS = {
    "openai": "gpt-4o", "gemini": "gemini-2.5-pro",
    "anthropic": "claude-sonnet-4-20250514", "groq": "llama-3.3-70b",
    "openrouter": "openai/gpt-4o", "azure-openai": "gpt-4o",
    "ollama": "llama3", "openai-compatible": "qwen2.5-coder",
}

ORCHESTRATION_FRAMEWORKS = [
    "langchain", "langgraph", "openai-agents",
    "google-adk", "crewai", "strands",
]

PATTERNS = [
    "react", "planner-executor", "reflection", "rag",
    "sequential", "swarm", "reviewer-critic", "hierarchical",
    "autonomous", "tool-use", "planning", "parallel",
    "debate", "coordinator", "blackboard",
]

MCP_SERVERS = ["filesystem", "github", "postgres", "brave-search", "memory", "puppeteer"]

IGNORE_PATTERNS = {
    "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "venv",
    "node_modules", "dist", "build", ".DS_Store", "*.pyc", ".git",
}

REPLACEABLE_SUFFIXES = {
    ".py", ".ts", ".tsx", ".json", ".toml", ".yaml", ".yml",
    ".md", ".tf", ".html", ".css", ".js", ".cfg", ".ini", ".example",
}


def _load_config() -> dict:
    try:
        import yaml
    except ImportError:
        return {}
    if CONFIG_FILE.exists():
        return yaml.safe_load(CONFIG_FILE.read_text()) or {}
    return {}


def _save_config(config: dict) -> None:
    import yaml
    CONFIG_FILE.write_text(yaml.dump(config, default_flow_style=False))


def _prompt(text: str, default: str = "") -> str:
    if default:
        result = input(f"  {text} [{default}]: ").strip()
        return result if result else default
    return input(f"  {text}: ").strip()


def _select(title: str, options: list[str], default: int = 0) -> str | None:
    print(f"\n  {title}")
    for i, opt in enumerate(options):
        marker = "  *" if i == default else "   "
        print(f"    [{i}] {marker} {opt}")
    choice = _prompt("Select", str(default))
    try:
        idx = int(choice)
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    return options[default]


def _multi_select(title: str, options: list[str]) -> list[str]:
    print(f"\n  {title}")
    for i, opt in enumerate(options):
        print(f"    [{i}]    {opt}")
    print("    [a]    Select all")
    print("    [n]    None")
    choice = _prompt("Select (comma-separated, e.g. 0,2,4 or 'a')", "")
    if not choice or choice.lower() == "n":
        return []
    if choice.lower() == "a":
        return list(options)
    selected = []
    for part in choice.split(","):
        try:
            idx = int(part.strip())
            if 0 <= idx < len(options):
                selected.append(options[idx])
        except ValueError:
            pass
    return selected


def _confirm(text: str, default: bool = True) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    result = input(f"  {text}{suffix}: ").strip().lower()
    if not result:
        return default
    return result in ("y", "yes")


def _ignored(path: str, names: list[str]) -> set[str]:
    return IGNORE_PATTERNS


def _copy_dir(src: Path, dst: Path, r: dict[str, str]) -> None:
    if not src.exists():
        return
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=_ignored)
    for root, _dirs, files in os.walk(dst):
        for f in files:
            fp = Path(root) / f
            if fp.suffix in REPLACEABLE_SUFFIXES:
                try:
                    content = fp.read_text()
                except UnicodeDecodeError:
                    continue
                changed = False
                for old, new in r.items():
                    if old in content:
                        content = content.replace(old, new)
                        changed = True
                if changed:
                    fp.write_text(content)


def _copy_file(src: Path, dst: Path, r: dict[str, str]) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if dst.suffix in REPLACEABLE_SUFFIXES:
        try:
            content = dst.read_text()
        except UnicodeDecodeError:
            return
        for old, new in r.items():
            content = content.replace(old, new)
        dst.write_text(content)


def _write_gitignore(dst: Path) -> None:
    (dst / ".gitignore").write_text("""__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.pytest_cache/
.ruff_cache/
node_modules/
dist/
build/
.env
.env.local
.idea/
.vscode/
*.swp
*.swo
.DS_Store
terraform/.terraform/
terraform/*.tfstate
terraform/*.tfstate.*
terraform/.terraform.lock.hcl
*.log
""")


def _print_tree(path: Path, prefix: str = "", depth: int = 0) -> None:
    if depth >= 2:
        return
    items = sorted(
        [p for p in path.iterdir() if p.name not in IGNORE_PATTERNS and p.name != ".gitignore"],
        key=lambda p: (not p.is_dir(), p.name),
    )
    for i, item in enumerate(items[:12]):
        last = i == len(items) - 1
        print(f"  {prefix}{'`-- ' if last else '|-- '}{item.name}")
        if item.is_dir() and depth < 1:
            _print_tree(item, prefix + ("    " if last else "|   "), depth + 1)
    if len(items) > 12:
        print(f"  {prefix}{'    ' if items else ''}(... {len(items) - 12} more)")


# -- Backend generation -------------------------------------------------------

PROVIDER_NAMES = {
    "openai": "OPENAI", "gemini": "GEMINI", "anthropic": "ANTHROPIC",
    "groq": "GROQ", "ollama": "OLLAMA", "openai-compatible": "OPENAI_COMPATIBLE",
    "openrouter": "OPENROUTER", "azure-openai": "AZURE_OPENAI",
}

PATTERN_NAMES = {
    "react": "REACT", "planner-executor": "PLANNER_EXECUTOR",
    "reflection": "REFLECTION", "rag": "RAG", "swarm": "SWARM",
    "sequential": "SEQUENTIAL", "reviewer-critic": "REVIEWER_CRITIC",
    "hierarchical": "HIERARCHICAL", "autonomous": "AUTONOMOUS",
    "tool-use": "TOOL_USE", "planning": "PLANNING", "parallel": "PARALLEL",
    "debate": "DEBATE", "coordinator": "COORDINATOR", "blackboard": "BLACKBOARD",
}


def _generate_config_py(provider: str, pattern: str) -> str:
    prov_name = PROVIDER_NAMES.get(provider, "OPENAI")
    pat_name = PATTERN_NAMES.get(pattern, "REACT")
    mdl = PROVIDER_MODELS.get(provider, "gpt-4o")
    return f'''"""Agent configuration for {pattern} pattern with {provider} provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderType(str, Enum):
    {prov_name} = "{provider}"


class PatternType(str, Enum):
    {pat_name} = "{pattern}"


@dataclass
class AgentConfig:
    name: str = "agent"
    provider_type: ProviderType = ProviderType.{prov_name}
    model: str = "{mdl}"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    extra: dict[str, Any] = field(default_factory=dict)
'''





def _memory_module_py() -> str:
    return '''"""Memory system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class Memory:
    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    async def add(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > 1000:
            self._entries = self._entries[-1000:]

    async def get(self, limit: int = 10) -> list[MemoryEntry]:
        return self._entries[-limit:]

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        q = query.lower()
        return [e for e in self._entries if q in e.content.lower()][-limit:]

    async def clear(self) -> None:
        self._entries.clear()
'''


def _mcp_module_py(mcp_servers: list[str]) -> str:
    servers_repr = repr(mcp_servers)
    return f'''"""MCP integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ENABLED_SERVERS: list[str] = {servers_repr}


@dataclass
class MCPServer:
    name: str
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
'''


def _telemetry_module_py() -> str:
    return '''"""Telemetry and tracing."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class TraceSpan:
    name: str
    start_time: float
    end_time: float = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Tracer:
    def __init__(self) -> None:
        self._traces: list[TraceSpan] = []

    @asynccontextmanager
    async def span(self, name: str, metadata: dict[str, Any] | None = None) -> AsyncIterator[TraceSpan]:
        span = TraceSpan(name=name, start_time=time.monotonic(), metadata=metadata or {})
        try:
            yield span
        except Exception as e:
            span.error = str(e)
            raise
        finally:
            span.end_time = time.monotonic()

    def get_traces(self) -> list[TraceSpan]:
        return self._traces

    def clear(self) -> None:
        self._traces.clear()
'''


def _write_backend(output_dir: Path, name: str, provider: str, fw: str, pattern: str, mcp_servers: list[str], r: dict[str, str]) -> None:
    be = output_dir / "backend"
    app_dir = be / "app"
    agentic_dir = app_dir / "agentic"

    for d in [be, app_dir, agentic_dir]:
        d.mkdir(parents=True, exist_ok=True)

    _copy_file(BACKEND_SRC / "pyproject.toml", be / "pyproject.toml", r)
    _copy_file(BACKEND_SRC / "Dockerfile", be / "Dockerfile", r)
    _copy_file(BACKEND_SRC / "Makefile", be / "Makefile", r)
    (be / ".env.example").write_text(
        "DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname\n"
        "PROVIDER_API_KEY=\nOPENAI_API_KEY=\nGEMINI_API_KEY=\nANTHROPIC_API_KEY=\n"
    )

    (app_dir / "__init__.py").write_text("")
    _copy_file(BACKEND_SRC / "app" / "config.py", app_dir / "config.py", r)
    _copy_file(BACKEND_SRC / "app" / "main.py", app_dir / "main.py", r)

    api_dir = app_dir / "api"
    api_dir.mkdir(exist_ok=True)
    for fname in ("__init__.py", "schemas.py", "health.py", "items.py"):
        src = BACKEND_SRC / "app" / "api" / fname
        if src.exists():
            _copy_file(src, api_dir / fname, r)

    db_dir = app_dir / "db"
    db_dir.mkdir(exist_ok=True)
    for fname in ("__init__.py", "connection.py", "models.py"):
        src = BACKEND_SRC / "app" / "db" / fname
        if src.exists():
            _copy_file(src, db_dir / fname, r)

    repo_dir = app_dir / "repositories"
    repo_dir.mkdir(exist_ok=True)
    for fname in ("__init__.py", "base.py", "item_repository.py"):
        src = BACKEND_SRC / "app" / "repositories" / fname
        if src.exists():
            _copy_file(src, repo_dir / fname, r)
    repo_db_dir = repo_dir / "db"
    repo_db_dir.mkdir(exist_ok=True)
    src_db = BACKEND_SRC / "app" / "repositories" / "db"
    if src_db.exists():
        for f in src_db.iterdir():
            if f.is_file():
                _copy_file(f, repo_db_dir / f.name, r)

    svc_dir = app_dir / "services"
    svc_dir.mkdir(exist_ok=True)
    for fname in ("__init__.py", "item_service.py"):
        src = BACKEND_SRC / "app" / "services" / fname
        if src.exists():
            _copy_file(src, svc_dir / fname, r)

    tests_dir = be / "tests"
    tests_dir.mkdir(exist_ok=True)
    src_test = BACKEND_SRC / "tests" / "test_health.py"
    if src_test.exists():
        _copy_file(src_test, tests_dir / "test_health.py", r)

    (agentic_dir / "__init__.py").write_text(f'"""Agentic AI agent for {name}."""\n')
    (agentic_dir / "config.py").write_text(_generate_config_py(provider, pattern))
    (agentic_dir / "agent.py").write_text(_generate_agent_py(name, pattern, provider, fw))

    memory_dir = agentic_dir / "memory"
    memory_dir.mkdir(exist_ok=True)
    (memory_dir / "__init__.py").write_text(_memory_module_py())

    mcp_dir = agentic_dir / "mcp"
    mcp_dir.mkdir(exist_ok=True)
    (mcp_dir / "__init__.py").write_text(_mcp_module_py(mcp_servers))

    tele_dir = agentic_dir / "telemetry"
    tele_dir.mkdir(exist_ok=True)
    (tele_dir / "__init__.py").write_text(_telemetry_module_py())


# -- Agent templates per pattern (self-contained, no external provider/orch imports) --

def _setup_agent_dir(output_dir: Path, name: str, provider: str, fw: str, pattern: str, mcp_servers: list[str]) -> None:
    agent_dir = output_dir / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "skill.update.py").write_text((AGENT_SRC / "skill.update.py").read_text())
    _write_filtered_skills_json(agent_dir, provider, fw)

    core_skills = {"agent-setup", "arch-review", "git-safety", "test-cycle", "skill-forge"}
    skills_dir = agent_dir / "skills"
    skills_dir.mkdir(exist_ok=True)
    for skill_name in sorted(core_skills):
        src = AGENT_SRC / "skills" / skill_name
        if src.exists():
            _copy_dir(src, skills_dir / skill_name, {})

    (agent_dir / "CLAUDE.md").write_text(_generate_claude_md(name, provider, fw, pattern, mcp_servers))
    (agent_dir / "settings.json").write_text("{}")
    (agent_dir / "settings.local.json").write_text("{}")

    if mcp_servers:
        mcp_dir = agent_dir / "mcp"
        mcp_dir.mkdir(exist_ok=True)
        for s in mcp_servers:
            (mcp_dir / f"{s}.json").write_text("{}")

    agents_dir = agent_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    (agents_dir / f"{name}-agent.md").write_text(_generate_agent_md(name, pattern))

    commands_dir = agent_dir / "commands"
    commands_dir.mkdir(exist_ok=True)


def _write_filtered_skills_json(agent_dir: Path, provider: str, fw: str) -> None:
    try:
        all_skills = json.loads((AGENT_SRC / "skills.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        all_skills = []

    relevance = {
        "fastapi/fastapi": True,
        "agentscope-ai/agentscope": fw in ("agentscope",),
        "nextlevelbuilder/ui-ux-pro-max": False,
        "sickn33/antigravity-awesome-skills": True,
    }

    filtered = [s for s in all_skills if relevance.get(s.get("slug", ""), False)]
    (agent_dir / "skills.json").write_text(json.dumps(filtered, indent=2))


def _generate_claude_md(name: str, provider: str, fw: str, pattern: str, mcp_servers: list[str]) -> str:
    mcp_list = ", ".join(mcp_servers) if mcp_servers else "none"
    return f"""# {name} -- Agent Instructions

## Project Overview
This is a full-stack project scaffolded by the Agentic CLI.
- Backend: FastAPI + SQLAlchemy (async) + PostgreSQL
- Frontend: React + TypeScript + Vite
- Infra: Terraform (DigitalOcean)
- AI: {fw} orchestration, {pattern} pattern, {provider} provider

## Key Rules
1. Keep code generic and reusable
2. Do not hardcode domain-specific terms
3. Do not commit secrets or .env values
4. Prefer small, testable units
5. Preserve API compatibility when refactoring

## AI Stack
- Provider: {provider}
- Orchestration: {fw}
- Pattern: {pattern}
- MCP Servers: {mcp_list}

## Build & Test
- Backend: cd backend && make dev
- Backend tests: cd backend && make test
- Frontend: cd frontend && npm run dev
- Full stack: docker compose up

## Skills
Skills are managed via .agent/skill.update.py
- List: python .agent/skill.update.py list
- Sync: python .agent/skill.update.py sync
"""


def _generate_agent_md(name: str, pattern: str) -> str:
    strategies = {
        "react": "Reason step by step, execute tools, observe results, repeat until done.",
        "planner-executor": "First plan the task into sub-steps, then execute each step sequentially.",
        "reflection": "Execute the task, then critically evaluate your output and refine.",
        "rag": "Retrieve relevant context first, then generate a grounded response with citations.",
        "swarm": "Coordinate with peer agents, each handling a specialized sub-task.",
        "sequential": "Process the input through stages: analyze, process, output.",
        "reviewer-critic": "Generate a draft, then review and improve it.",
        "hierarchical": "Delegate sub-tasks to specialized agents and aggregate results.",
        "autonomous": "Drive toward the goal independently, using tools as needed.",
        "tool-use": "Select and use the right tool for each step of the task.",
    }
    strategy = strategies.get(pattern, "Execute the task efficiently using available tools and context.")
    return f"""# {name} Agent

## Role
You are a {pattern} agent for the {name} project.

## Strategy
{strategy}

## Context
- This project uses FastAPI (backend) and React (frontend)
- Follow the project rules in AGENTS.md
- Use available skills and MCP tools when relevant
"""


# -- Create Project (full interactive flow) ------------------------------------

def _interactive_create_project() -> None:
    print("\n  [ Create New Project ]\n")
    name = _prompt("Project name", "my-project")
    output = _prompt("Output directory", ".")

    output_dir = Path(output).resolve() / name
    if output_dir.exists() and any(output_dir.iterdir()):
        if not _confirm(f"Directory '{output_dir}' already exists. Overwrite?", default=False):
            print("  Aborted.\n")
            return

    print("\n  -- LLM Provider --")
    provider = _select("Provider type:", PROVIDER_TYPES, default=0)
    model = _prompt("Model name", PROVIDER_MODELS.get(provider, "gpt-4o"))
    api_key = _prompt("API key (leave blank to use env var)", "")
    base_url = ""
    if provider in ("ollama", "openai-compatible", "openrouter"):
        default_url = "http://localhost:11434/v1" if provider == "ollama" else ""
        base_url = _prompt("Base URL", default_url)

    print("\n  -- Orchestration --")
    fw = _select("Framework:", ORCHESTRATION_FRAMEWORKS, default=0)

    print("\n  -- Agentic Pattern --")
    pattern = _select("Pattern:", PATTERNS, default=0)

    print("\n  -- MCP Servers --")
    mcp_servers = _multi_select("Select MCP servers to include:", MCP_SERVERS)

    print(f"\n  Scaffolding '{name}'...")

    r = {
        "codestash-starterpack": name,
        "codestash-backend": name,
        "codestash_backend": name.replace("-", "_"),
        "CodeStash Starterpack": name.title(),
        "codestash-db": f"{name}-db",
        "codestash-frontend": f"{name}-frontend",
        "codestash-node": f"{name}-node",
        "codestash": name,
    }

    _write_backend(output_dir, name, provider, fw, pattern, mcp_servers, r)
    _copy_dir(FRONTEND_SRC, output_dir / "frontend", r)
    _copy_dir(TERRAFORM_SRC, output_dir / "terraform", r)
    _copy_dir(GITHUB_SRC, output_dir / ".github", r)
    _setup_agent_dir(output_dir, name, provider, fw, pattern, mcp_servers)
    _copy_file(DOCKER_COMPOSE_SRC, output_dir / "docker-compose.yml", r)
    _copy_file(AGENTS_MD_SRC, output_dir / "AGENTS.md", r)
    _copy_file(Path(__file__), output_dir / "cli.py", {})
    _write_gitignore(output_dir)

    _write_agentic_yaml(output_dir, name, {
        "provider": {"type": provider, "model": model, "api_key": api_key, "base_url": base_url, "temperature": 0.7},
        "orchestration": {"framework": fw},
        "pattern": {"type": pattern},
        "mcp": {"servers": [{"name": s, "enabled": True} for s in mcp_servers]},
        "memory": {"backend": "simple"},
    })

    print("\n  Syncing AI skills...")
    skill_py = output_dir / ".agent" / "skill.update.py"
    if skill_py.exists():
        subprocess.run([sys.executable, str(skill_py), "sync"], cwd=str(output_dir))

    print(f"\n  Project created: {output_dir}")
    _print_tree(output_dir)
    print("\n  Configuration summary:")
    print(f"    Provider:      {provider} ({model})")
    print(f"    Orchestration: {fw}")
    print(f"    Pattern:       {pattern}")
    print(f"    MCP Servers:   {', '.join(mcp_servers) if mcp_servers else 'none'}")
    print("\n  Next steps:")
    print(f"    cd {output_dir}")
    print("    cp backend/.env.example backend/.env")
    print("    docker compose up --build\n")


def _write_agentic_yaml(output_dir: Path, project_name: str, config: dict) -> None:
    import yaml
    config["name"] = project_name
    (output_dir / "agentic.yaml").write_text(yaml.dump(config, default_flow_style=False))


# -- View Configuration --------------------------------------------------------

def _interactive_view_config() -> None:
    c = _load_config()
    if not c:
        print("\n  No agentic.yaml found. Create a project first.\n")
        return
    print("\n  [ Project Configuration ]\n")
    p = c.get("provider", {})
    o = c.get("orchestration", {})
    pt = c.get("pattern", {})
    m = c.get("memory", {})
    srv = c.get("mcp", {}).get("servers", [])
    print(f"  Project:       {c.get('name', '(not set)')}")
    print(f"  Provider:      {p.get('type', '(not set)')} / {p.get('model', '')}")
    print(f"  Orchestration: {o.get('framework', '(not set)')}")
    print(f"  Pattern:       {pt.get('type', '(not set)')}")
    print(f"  Memory:        {m.get('backend', 'simple')}")
    print(f"  MCP Servers:   {len(srv)} configured")
    if srv:
        for s in srv:
            print(f"    - {s['name']}")
    print(f"  Config file:   {CONFIG_FILE.resolve()}\n")


# -- Main Menu -----------------------------------------------------------------

MENU_ITEMS = [
    ("Create New Project", _interactive_create_project),
    ("View Configuration", _interactive_view_config),
]

HEADER = """
  -------------------------------------------------
         AGENTIC -- Full-Stack Scaffolding
            & AI Agent CLI
  -------------------------------------------------
"""


def _menu() -> None:
    while True:
        print(HEADER)
        for i, (label, _) in enumerate(MENU_ITEMS):
            print(f"    [{i + 1}] {label}")
        print("\n    [0] Exit\n")

        try:
            choice = input("  Select > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Goodbye.\n")
            break

        if choice in ("0", "q", "quit", "exit"):
            print("\n  Goodbye.\n")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(MENU_ITEMS):
                MENU_ITEMS[idx][1]()
            else:
                print("\n  Invalid selection.\n")
        except ValueError:
            print("\n  Invalid selection.\n")


def main() -> None:
    _menu()

# -- New agent templates (F433 pattern: factory + orchestrator class + singleton) --

PROVIDER_IMPORTS = {
    "openai": "from openai import AsyncOpenAI",
    "gemini": "from google import genai",
    "anthropic": "from anthropic import AsyncAnthropic",
    "groq": "from openai import AsyncOpenAI",
    "ollama": "from openai import AsyncOpenAI",
    "openai-compatible": "from openai import AsyncOpenAI",
    "openrouter": "from openai import AsyncOpenAI",
    "azure-openai": "from openai import AsyncOpenAI",
}

PROVIDER_INIT = {
    "openai": '        self._client = AsyncOpenAI(api_key=self._config.api_key or None)',
    "gemini": '        self._client = genai.Client(api_key=self._config.api_key)',
    "anthropic": '        self._client = AsyncAnthropic(api_key=self._config.api_key)',
    "groq": '        self._client = AsyncOpenAI(api_key=self._config.api_key, base_url="https://api.groq.com/openai/v1")',
    "ollama": '        self._client = AsyncOpenAI(api_key="ollama", base_url=self._config.base_url or "http://localhost:11434/v1")',
    "openai-compatible": '        self._client = AsyncOpenAI(api_key=self._config.api_key or "local", base_url=self._config.base_url or None)',
    "openrouter": '        self._client = AsyncOpenAI(api_key=self._config.api_key, base_url="https://openrouter.ai/api/v1")',
    "azure-openai": '        self._client = AsyncOpenAI(api_key=self._config.api_key, base_url=self._config.base_url)',
}

COMPAT_NEEDS_LITELLM = {
    ("google-adk", "openai"): True,
    ("google-adk", "anthropic"): True,
    ("google-adk", "groq"): True,
    ("google-adk", "ollama"): True,
    ("openai-agents", "gemini"): True,
    ("openai-agents", "anthropic"): True,
}


def _needs_litellm(fw: str, provider: str) -> bool:
    return COMPAT_NEEDS_LITELLM.get((fw, provider), False)


def _compat_block(fw: str, provider: str) -> str:
    return f"""

# Compatibility: {fw} does not natively support {provider}.
# Using LiteLLM as a bridge. Install: pip install litellm
import litellm
litellm.set_verbose = False
"""


def _compat_setup() -> str:
    return """
        self._litellm_model = f"openai/{{self._config.model}}\""""


def _generate_agent_py(name: str, pattern: str, provider: str, fw: str) -> str:
    import sys
    sys.path.insert(0, str(ROOT))
    from agent_templates import _AGENT_TEMPLATES
    template = _AGENT_TEMPLATES.get(pattern, _AGENT_TEMPLATES["react"])
    import_line = PROVIDER_IMPORTS.get(provider, PROVIDER_IMPORTS["openai"])
    init_line = PROVIDER_INIT.get(provider, PROVIDER_INIT["openai"])
    needs_compat = _needs_litellm(fw, provider)
    compat_block = _compat_block(fw, provider) if needs_compat else ""
    compat_setup = _compat_setup() if needs_compat else ""
    return template.format(
        name=name, pattern=pattern, provider=provider, fw=fw,
        provider_import=import_line, provider_init=init_line,
        compat_block=compat_block, compat_setup=compat_setup,
        class_name=name.replace("-", " ").title().replace(" ", ""),
    )

if __name__ == "__main__":
    main()
