#!/usr/bin/env python3
"""Agentic -- full-stack project generation CLI.

Run without arguments for interactive mode:
    python3 cli.py
"""

from __future__ import annotations

import json
import importlib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_module import (  # noqa: E402
    FRAMEWORK_LABELS,
    PATTERN_SPECS,
    PROVIDER_LABELS,
    render_agent_package,
)

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
    "openai",
    "gemini",
    "anthropic",
    "groq",
    "openrouter",
    "azure-openai",
    "ollama",
    "openai-compatible",
]

PROVIDER_MODELS = {
    "openai": "gpt-4o",
    "gemini": "gemini-2.5-pro",
    "anthropic": "claude-sonnet-4-20250514",
    "groq": "llama-3.3-70b",
    "openrouter": "openai/gpt-4o",
    "azure-openai": "gpt-4o",
    "ollama": "llama3",
    "openai-compatible": "qwen2.5-coder",
}

PROVIDER_ENV_VARS = {
    "openai": {
        "api_key": "OPENAI_API_KEY",
        "base_url": "OPENAI_BASE_URL",
        "base_url_default": "",
    },
    "gemini": {
        "api_key": "GEMINI_API_KEY",
        "base_url": "GEMINI_BASE_URL",
        "base_url_default": "",
    },
    "anthropic": {
        "api_key": "ANTHROPIC_API_KEY",
        "base_url": "ANTHROPIC_BASE_URL",
        "base_url_default": "",
    },
    "groq": {
        "api_key": "GROQ_API_KEY",
        "base_url": "GROQ_BASE_URL",
        "base_url_default": "https://api.groq.com/openai/v1",
    },
    "openrouter": {
        "api_key": "OPENROUTER_API_KEY",
        "base_url": "OPENROUTER_BASE_URL",
        "base_url_default": "https://openrouter.ai/api/v1",
    },
    "azure-openai": {
        "api_key": "AZURE_OPENAI_API_KEY",
        "base_url": "AZURE_OPENAI_ENDPOINT",
        "base_url_default": "",
    },
    "ollama": {
        "api_key": "OLLAMA_API_KEY",
        "base_url": "OLLAMA_BASE_URL",
        "base_url_default": "http://localhost:11434/v1",
    },
    "openai-compatible": {
        "api_key": "OPENAI_COMPATIBLE_API_KEY",
        "base_url": "OPENAI_COMPATIBLE_BASE_URL",
        "base_url_default": "",
    },
}

BASE_URL_PROMPT_PROVIDERS = {
    "azure-openai",
    "ollama",
    "openai-compatible",
    "openrouter",
}

ORCHESTRATION_FRAMEWORKS = [
    "langchain",
    "langgraph",
    "openai-agents",
    "google-adk",
    "crewai",
    "strands",
]

AGENTIC_BASE_DEPENDENCIES = [
    "chromadb>=0.5.0",
    "aiosqlite>=0.20.0",
]

# The LangChain family ships one distribution per provider binding.
LANGCHAIN_PROVIDER_PACKAGES = {
    "gemini": "langchain-google-genai>=2.0.0",
    "anthropic": "langchain-anthropic>=0.3.0",
}
LANGCHAIN_OPENAI_PACKAGE = "langchain-openai>=0.2.0"

# Strands publishes provider bindings as extras of a single distribution.
STRANDS_PROVIDER_EXTRAS = {
    "gemini": "gemini",
    "anthropic": "anthropic",
    "ollama": "ollama",
}

# CrewAI routes a recognised model prefix to a native provider class and raises
# ImportError if that provider's extra is missing. Prefixes it does not recognise
# (only ``groq/`` here) fall through to LiteLLM instead.
CREWAI_PROVIDER_EXTRAS = {
    "anthropic": "[anthropic]",
    "gemini": "[google-genai]",
    "azure-openai": "[azure-ai-inference]",
    "groq": "[litellm]",
}


def _agent_dependencies(framework: str, provider: str) -> list[str]:
    """Return the SDK packages the generated agent module imports."""
    if framework == "google-adk":
        if provider == "gemini":
            return ["google-adk>=1.0.0"]
        # ADK reaches every non-Gemini provider through LiteLLM.
        return ["google-adk>=1.0.0", "litellm>=1.55.0"]
    if framework in {"langchain", "langgraph"}:
        core = "langchain>=0.3.0" if framework == "langchain" else "langgraph>=0.2.0"
        return [core, LANGCHAIN_PROVIDER_PACKAGES.get(provider, LANGCHAIN_OPENAI_PACKAGE)]
    if framework == "crewai":
        # openai / openrouter / ollama / openai-compatible all resolve to a native
        # provider backed by the openai SDK, which CrewAI already depends on.
        return [f"crewai{CREWAI_PROVIDER_EXTRAS.get(provider, '')}>=1.0.0"]
    if framework == "openai-agents":
        if provider in {"gemini", "anthropic"}:
            return ["openai-agents[litellm]>=0.1.0"]
        return ["openai-agents>=0.1.0"]
    extra = STRANDS_PROVIDER_EXTRAS.get(provider, "openai")
    return [f"strands-agents[{extra}]>=1.0.0"]


PATTERNS = [
    "react",
    "planner-executor",
    "reflection",
    "rag",
    "sequential",
    "swarm",
    "reviewer-critic",
    "hierarchical",
    "autonomous",
    "tool-use",
    "planning",
    "parallel",
    "debate",
    "coordinator",
    "blackboard",
]

MCP_SERVERS = [
    "filesystem",
    "github",
    "postgres",
    "brave-search",
    "memory",
    "puppeteer",
]

IGNORE_PATTERNS = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".DS_Store",
    "*.pyc",
    ".git",
    # Dependencies are tailored per project, so the template lock file never matches.
    "uv.lock",
}

REPLACEABLE_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".md",
    ".tf",
    ".html",
    ".css",
    ".js",
    ".cfg",
    ".ini",
    ".example",
}


def _load_config() -> dict:
    try:
        yaml = importlib.import_module("yaml")
    except ModuleNotFoundError:
        return {}
    if CONFIG_FILE.exists():
        return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    return {}


def _save_config(config: dict) -> None:
    try:
        yaml = importlib.import_module("yaml")
    except ModuleNotFoundError:
        CONFIG_FILE.write_text(_dump_simple_yaml(config) + "\n", encoding="utf-8")
        return
    CONFIG_FILE.write_text(yaml.dump(config, default_flow_style=False), encoding="utf-8")


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


def _ignored(_path: str, _names: list[str]) -> set[str]:
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
                    content = fp.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                changed = False
                for old, new in r.items():
                    if old in content:
                        content = content.replace(old, new)
                        changed = True
                if changed:
                    fp.write_text(content, encoding="utf-8")


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


def _provider_env(provider: str) -> dict[str, str]:
    return PROVIDER_ENV_VARS.get(provider, PROVIDER_ENV_VARS["openai"])


def _provider_api_key_env(provider: str) -> str:
    return _provider_env(provider)["api_key"]


def _provider_base_url_env(provider: str) -> str:
    return _provider_env(provider)["base_url"]


def _provider_base_url_default(provider: str) -> str:
    return _provider_env(provider).get("base_url_default", "")


def _env_value(value: str) -> str:
    if value == "":
        return ""
    if any(ch.isspace() for ch in value) or any(ch in value for ch in "#'\""):
        return json.dumps(value)
    return value


def _env_line(key: str, value: str) -> str:
    return f"{key}={_env_value(value)}"


def _backend_env_content(
    name: str,
    provider: str,
    model: str,
    fw: str,
    pattern: str,
    mcp_servers: list[str],
    api_key: str,
    base_url: str,
    *,
    example: bool,
) -> str:
    db_name = name
    app_name = f"{name.replace('-', ' ').replace('_', ' ').title()} API"
    api_key_env = _provider_api_key_env(provider)
    base_url_env = _provider_base_url_env(provider)
    effective_base_url = base_url or _provider_base_url_default(provider)

    lines = [
        "# Application",
        _env_line("APP_NAME", app_name),
        _env_line("ENV", "development"),
        _env_line(
            "DATABASE_URL",
            f"postgresql+asyncpg://{db_name}:{db_name}@db:5432/{db_name}",
        ),
        _env_line("CORS_ORIGINS", "http://localhost:5173"),
        "",
        "# Agent",
        _env_line("AGENT_PROVIDER_TYPE", provider),
        _env_line("AGENT_MODEL", model),
        _env_line("AGENT_TEMPERATURE", "0.7"),
        _env_line("AGENT_MAX_TOKENS", "4096"),
        _env_line("AGENT_ORCHESTRATION_FRAMEWORK", fw),
        _env_line("AGENT_PATTERN", pattern),
        _env_line("AGENT_MCP_SERVERS", ",".join(mcp_servers)),
        _env_line("AGENTOPS_ENABLED", "false"),
        _env_line("AGENTOPS_API_KEY", ""),
        _env_line("AGENTOPS_CAPTURE_CONTENT", "false"),
        _env_line("AGENTOPS_TAGS", "codestash,fastapi"),
        _env_line("AGENTOPS_ENVIRONMENT", "development"),
        _env_line("AGENTOPS_EXPORT_FLUSH_INTERVAL", "1000"),
        _env_line("AGENTOPS_MAX_WAIT_TIME", "5000"),
        _env_line("AGENTOPS_MAX_QUEUE_SIZE", "512"),
        "",
        f"# Provider: {provider}",
        _env_line(api_key_env, "" if example else api_key),
    ]

    if effective_base_url:
        lines.append(_env_line(base_url_env, effective_base_url))

    if provider == "azure-openai":
        lines.append(_env_line("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"))

    return "\n".join(lines).rstrip() + "\n"


def _write_backend_env_files(
    backend_dir: Path,
    name: str,
    provider: str,
    model: str,
    fw: str,
    pattern: str,
    mcp_servers: list[str],
    api_key: str,
    base_url: str,
) -> None:
    backend_dir.mkdir(parents=True, exist_ok=True)
    (backend_dir / ".env.example").write_text(
        _backend_env_content(
            name,
            provider,
            model,
            fw,
            pattern,
            mcp_servers,
            api_key="",
            base_url=base_url,
            example=True,
        )
    )
    (backend_dir / ".env").write_text(
        _backend_env_content(
            name,
            provider,
            model,
            fw,
            pattern,
            mcp_servers,
            api_key=api_key,
            base_url=base_url,
            example=False,
        )
    )


def _write_frontend_env(output_dir: Path) -> None:
    env_example = output_dir / "frontend" / ".env.example"
    if env_example.exists():
        (output_dir / "frontend" / ".env").write_text(env_example.read_text())


def _yaml_scalar(value: object) -> str:
    if value is None:
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "":
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_./:@+-]+", text):
        return text
    return json.dumps(text)


def _dump_simple_yaml(value: object, indent: int = 0) -> str:
    spaces = " " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, dict):
                lines.append(f"{spaces}{key}:")
                lines.append(_dump_simple_yaml(item, indent + 2))
            elif isinstance(item, list):
                if not item:
                    lines.append(f"{spaces}{key}: []")
                    continue
                lines.append(f"{spaces}{key}:")
                lines.append(_dump_simple_yaml(item, indent + 2))
            else:
                lines.append(f"{spaces}{key}: {_yaml_scalar(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                item_lines = _dump_simple_yaml(item, indent + 2).splitlines()
                if item_lines:
                    first = item_lines[0].lstrip()
                    lines.append(f"{spaces}- {first}")
                    lines.extend(item_lines[1:])
                else:
                    lines.append(f"{spaces}- {{}}")
            else:
                lines.append(f"{spaces}- {_yaml_scalar(item)}")
    else:
        lines.append(f"{spaces}{_yaml_scalar(value)}")
    return "\n".join(lines)


MIT_LICENSE_TEMPLATE = """MIT License

Copyright (c) {year} {holder}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _write_license(dst: Path, name: str) -> None:
    holder = os.environ.get("COPYRIGHT_HOLDER") or name.replace("-", " ").title()
    text = MIT_LICENSE_TEMPLATE.format(year=datetime.now().year, holder=holder)
    (dst / "LICENSE").write_text(text, encoding="utf-8")


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


def _write_backend(
    output_dir: Path,
    name: str,
    provider: str,
    model: str,
    fw: str,
    pattern: str,
    mcp_servers: list[str],
    api_key: str,
    base_url: str,
    r: dict[str, str],
) -> None:
    be = output_dir / "backend"
    app_dir = be / "app"
    agentic_dir = app_dir / "agentic"

    for d in [be, app_dir, agentic_dir]:
        d.mkdir(parents=True, exist_ok=True)

    _copy_file(BACKEND_SRC / "pyproject.toml", be / "pyproject.toml", r)
    _copy_file(BACKEND_SRC / "Dockerfile", be / "Dockerfile", r)
    _copy_file(BACKEND_SRC / "Makefile", be / "Makefile", r)
    _write_backend_env_files(
        be,
        name,
        provider,
        model,
        fw,
        pattern,
        mcp_servers,
        api_key,
        base_url,
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

    # Reuse the shared agentic runtime, then fuse the selection into one agent package.
    _copy_dir(BACKEND_SRC / "app" / "agentic", agentic_dir, r)
    _write_agent_package(agentic_dir, name, provider, fw, pattern)

    tests_dir = be / "tests"
    tests_dir.mkdir(exist_ok=True)
    src_test = BACKEND_SRC / "tests" / "test_health.py"
    if src_test.exists():
        _copy_file(src_test, tests_dir / "test_health.py", r)

    _write_agent_dependencies(be / "pyproject.toml", fw, provider)


# -- Agent templates per pattern (self-contained, no external provider/orch imports) --


def _setup_agent_dir(
    output_dir: Path,
    name: str,
    provider: str,
    fw: str,
    pattern: str,
    mcp_servers: list[str],
) -> None:
    agent_dir = output_dir / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "skill.update.py").write_text((AGENT_SRC / "skill.update.py").read_text())
    _write_filtered_skills_json(agent_dir, provider, fw)

    core_skills = {
        "agent-setup",
        "arch-review",
        "git-safety",
        "test-cycle",
        "skill-forge",
    }
    skills_dir = agent_dir / "skills"
    skills_dir.mkdir(exist_ok=True)
    for skill_name in sorted(core_skills):
        src = AGENT_SRC / "skills" / skill_name
        if src.exists():
            _copy_dir(src, skills_dir / skill_name, {})

    (agent_dir / "CLAUDE.md").write_text(
        _generate_claude_md(name, provider, fw, pattern, mcp_servers)
    )
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


def _write_filtered_skills_json(agent_dir: Path, _provider: str, fw: str) -> None:
    try:
        all_skills = json.loads((AGENT_SRC / "skills.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        all_skills = []

    relevance = {
        "fastapi/fastapi": True,
        "agentscope-ai/agentscope": fw in ("agentscope",),
        "nextlevelbuilder/ui-ux-pro-max": False,
        "sickn33/antigravity-awesome-skills": False,
    }

    filtered = [s for s in all_skills if relevance.get(s.get("slug", ""), False)]
    (agent_dir / "skills.json").write_text(json.dumps(filtered, indent=2))


def _generate_claude_md(
    name: str, provider: str, fw: str, pattern: str, mcp_servers: list[str]
) -> str:
    mcp_list = ", ".join(mcp_servers) if mcp_servers else "none"
    return f"""# {name} -- Agent Instructions

## Project Overview
This is a full-stack project generated by the Agentic CLI.
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
    strategy = strategies.get(
        pattern, "Execute the task efficiently using available tools and context."
    )
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
    api_key_env = _provider_api_key_env(provider)
    api_key = _prompt(f"API key (leave blank to use {api_key_env})", "")
    base_url = ""
    if provider in BASE_URL_PROMPT_PROVIDERS:
        default_url = _provider_base_url_default(provider)
        base_url = _prompt("Base URL", default_url)

    print("\n  -- Orchestration --")
    fw = _select("Framework:", ORCHESTRATION_FRAMEWORKS, default=0)

    print("\n  -- Agentic Pattern --")
    pattern = _select("Pattern:", PATTERNS, default=0)

    print("\n  -- MCP Servers --")
    mcp_servers = _multi_select("Select MCP servers to include:", MCP_SERVERS)

    print(f"\n  Generating '{name}'...")

    r = {
        "codestash-starterpack": name,
        "codestash-backend": name,
        "codestash_backend": name.replace("-", "_"),
        "CodeStash Starterpack": name.title(),
        "CodeStash": name.title(),
        "codestash-db": f"{name}-db",
        "codestash-frontend": f"{name}-frontend",
        "codestash-node": f"{name}-node",
        "codestash": name,
    }

    _write_backend(
        output_dir,
        name,
        provider,
        model,
        fw,
        pattern,
        mcp_servers,
        api_key,
        base_url,
        r,
    )
    _copy_dir(FRONTEND_SRC, output_dir / "frontend", r)
    _write_frontend_env(output_dir)
    _copy_dir(TERRAFORM_SRC, output_dir / "terraform", r)
    _copy_dir(GITHUB_SRC, output_dir / ".github", r)
    _setup_agent_dir(output_dir, name, provider, fw, pattern, mcp_servers)
    _copy_file(DOCKER_COMPOSE_SRC, output_dir / "docker-compose.yml", r)
    _copy_file(AGENTS_MD_SRC, output_dir / "AGENTS.md", r)
    _write_gitignore(output_dir)
    _write_license(output_dir, name)
    _write_readme(output_dir, name, provider, model, fw, pattern, mcp_servers)

    _write_agentic_yaml(
        output_dir,
        name,
        {
            "provider": {
                "type": provider,
                "model": model,
                "api_key_env": _provider_api_key_env(provider),
                "base_url": base_url or _provider_base_url_default(provider),
                "base_url_env": _provider_base_url_env(provider),
                "temperature": 0.7,
            },
            "orchestration": {"framework": fw},
            "pattern": {"type": pattern},
            "mcp": {"servers": [{"name": s, "enabled": True} for s in mcp_servers]},
            "memory": {"backend": "simple"},
        },
    )

    print("\n  Syncing AI skills...")
    skill_py = output_dir / ".agent" / "skill.update.py"
    if skill_py.exists():
        subprocess.run([sys.executable, str(skill_py), "sync"], cwd=str(output_dir), check=False)

    print(f"\n  Project created: {output_dir}")
    _print_tree(output_dir)
    print("\n  Configuration summary:")
    print(f"    Provider:      {provider} ({model})")
    print(f"    Orchestration: {fw}")
    print(f"    Pattern:       {pattern}")
    print(f"    MCP Servers:   {', '.join(mcp_servers) if mcp_servers else 'none'}")
    print("\n  Next steps:")
    print(f"    cd {output_dir}")
    print("    docker compose up --build\n")


TOPOLOGY_SUMMARIES = {
    "single": "a single tool-using agent",
    "pipeline": "a pipeline where each role hands its output to the next",
    "loop": "a draft/critique loop that runs for a fixed number of rounds",
    "fanout": "parallel branches whose results are merged by a final agent",
    "supervisor": "a supervisor that briefs and delegates to specialist agents",
}


def _write_readme(
    output_dir: Path,
    name: str,
    provider: str,
    model: str,
    framework: str,
    pattern: str,
    mcp_servers: list[str],
) -> None:
    """Write a README describing the stack this project was actually generated with."""
    spec = PATTERN_SPECS[pattern]
    roles = spec["roles"]
    title = name.replace("-", " ").replace("_", " ").title()
    key_env = _provider_api_key_env(provider)
    roles_line = " → ".join(role for role, _ in roles) if roles else "single agent"
    mcp_line = ", ".join(f"`{s}`" for s in mcp_servers) if mcp_servers else "none configured"

    content = f"""# {title}

FastAPI + React + PostgreSQL application with a built-in agent runtime.

## Stack

| Piece | Choice |
| --- | --- |
| Backend | FastAPI, SQLAlchemy asyncio, asyncpg |
| Frontend | React 19, TypeScript, Vite |
| Database | PostgreSQL 16 |
| LLM provider | {PROVIDER_LABELS[provider]} (`{model}`) |
| Orchestration | {FRAMEWORK_LABELS[framework]} |
| Agentic pattern | `{pattern}` — {TOPOLOGY_SUMMARIES[spec["topology"]]} |
| Agent roles | {roles_line} |
| MCP servers | {mcp_line} |

## Quick Start

```bash
cp backend/.env.example backend/.env   # set {key_env}
cp frontend/.env.example frontend/.env
docker compose up --build
```

| Service | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

`VITE_API_URL` is resolved by the browser. `DEV_PROXY_TARGET` is resolved by the Vite dev server
and is overridden to `http://backend:8000` by docker compose.

## Agent

The agent lives in `backend/app/agentic/agent/agent.py` and is written directly against the
{FRAMEWORK_LABELS[framework]} SDK — there is no wrapper layer or provider switch to unpick.

```python
from app.agentic.agent import root_agent

result = await root_agent.run("Summarise the latest release notes")
print(result.final_output, result.steps, result.duration_ms)

async for chunk in root_agent.stream("Draft a changelog"):
    print(chunk, end="")
```

Three seams to edit:

| Function / class | Responsibility |
| --- | --- |
| `build_model(config)` | Binds {PROVIDER_LABELS[provider]} to {FRAMEWORK_LABELS[framework]} |
| `build_runtime(config)` | Assembles the `{pattern}` topology |
| `Agent` | Adapts the runtime to `run()` / `stream()` / `chat()` |

Check it over HTTP:

```bash
curl localhost:8000/api/agent              # provider, framework, pattern, telemetry
curl "localhost:8000/api/agent?probe=true" # also round-trips one call to the model
```

## Layout

```text
backend/app/
|-- agentic/        # agent runtime, config, mcp, memory, telemetry
|-- api/            # HTTP layer
|-- services/       # business logic
|-- repositories/   # data access + models
`-- main.py
```

The backend follows a Controller → Service → Repository → Model flow. `app/api/items.py` is the
reference resource: copy it, its service and its repository when adding a new entity.

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/status` | Version plus database connectivity |
| `GET` | `/api/agent` | Agent runtime configuration |
| `GET` | `/api/items` | Paginated list — `page`, `limit`, optional `status` |
| `POST` | `/api/items` | Create an item |
| `GET` | `/api/items/{{id}}` | Fetch one item |
| `PATCH` | `/api/items/{{id}}` | Partial update |
| `DELETE` | `/api/items/{{id}}` | Delete an item |

Timestamps are serialised as UTC ISO-8601 with a trailing `Z`.

## Development

```bash
cd backend && make install && make dev    # API on :8000
cd frontend && npm install && npm run dev # UI on :5173
```

```bash
make test    # pytest
make lint    # ruff check
make format  # ruff format
```

## Deployment

`terraform/` holds DigitalOcean modules. Before going to production: restrict `CORS_ORIGINS`,
set `ENV=production` to disable the docs endpoint, move secrets into a managed store, and point
`VITE_API_URL` at the public API origin.

## License

Released under the [MIT License](LICENSE).
"""
    (output_dir / "README.md").write_text(content, encoding="utf-8")


def _write_agentic_yaml(output_dir: Path, project_name: str, config: dict) -> None:
    config = {"name": project_name, **config}
    try:
        yaml = importlib.import_module("yaml")
    except ModuleNotFoundError:
        content = _dump_simple_yaml(config) + "\n"
    else:
        content = yaml.dump(config, default_flow_style=False, sort_keys=False)
    (output_dir / "agentic.yaml").write_text(content, encoding="utf-8")


def _write_agent_dependencies(pyproject_path: Path, framework: str, provider: str) -> None:
    """Rewrite the ``agentic`` extra with the SDKs this selection actually imports."""
    content = pyproject_path.read_text(encoding="utf-8")
    marker = "agentic = [\n"
    start = content.find(marker)
    if start == -1:
        return
    end = content.find("]\n", start)
    if end == -1:
        return
    dependencies = AGENTIC_BASE_DEPENDENCIES + _agent_dependencies(framework, provider)
    block = marker + "".join(f'  "{dependency}",\n' for dependency in dependencies)
    pyproject_path.write_text(content[:start] + block + content[end:], encoding="utf-8")


def _write_agent_package(
    agentic_dir: Path, name: str, provider: str, framework: str, pattern: str
) -> None:
    """Fuse the selected provider, framework and pattern into ``agentic/agent/``."""
    agent_dir = agentic_dir / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in render_agent_package(name, provider, framework, pattern).items():
        (agent_dir / filename).write_text(content, encoding="utf-8")


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
         AGENTIC -- Full-Stack Generator
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


if __name__ == "__main__":
    main()
