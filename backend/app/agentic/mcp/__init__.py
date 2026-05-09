"""MCP integration — Model Context Protocol server support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPServer:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class MCPTool:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    server: str = ""


MCP_SERVER_TEMPLATES: dict[str, MCPServer] = {
    "filesystem": MCPServer(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"],
    ),
    "github": MCPServer(
        name="github",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
    ),
    "postgres": MCPServer(
        name="postgres",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-postgres"],
        env={"DATABASE_URL": "postgresql://localhost/mydb"},
    ),
    "brave-search": MCPServer(
        name="brave-search",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env={"BRAVE_API_KEY": ""},
    ),
    "memory": MCPServer(
        name="memory",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-memory"],
    ),
    "puppeteer": MCPServer(
        name="puppeteer",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-puppeteer"],
    ),
}
