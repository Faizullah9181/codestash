"""Memory system — short-term, vector, and persistent memory backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.agentic.config import MemoryBackend, MemoryConfig


@dataclass
class MemoryEntry:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseMemory(ABC):
    def __init__(self, config: MemoryConfig) -> None:
        self.config = config

    @abstractmethod
    async def add(self, entry: MemoryEntry) -> None: ...

    @abstractmethod
    async def get(self, limit: int = 10) -> list[MemoryEntry]: ...

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]: ...

    @abstractmethod
    async def clear(self) -> None: ...


class SimpleMemory(BaseMemory):
    def __init__(self, config: MemoryConfig) -> None:
        super().__init__(config)
        self._entries: list[MemoryEntry] = []

    async def add(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > 1000:
            self._entries = self._entries[-1000:]

    async def get(self, limit: int = 10) -> list[MemoryEntry]:
        return self._entries[-limit:]

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        query_lower = query.lower()
        matches = [e for e in self._entries if query_lower in e.content.lower()]
        return matches[-limit:]

    async def clear(self) -> None:
        self._entries.clear()


class SQLiteMemory(BaseMemory):
    def __init__(self, config: MemoryConfig) -> None:
        super().__init__(config)
        self._db_path = config.connection_string or "agent_memory.db"

    async def _ensure_table(self) -> None:
        import aiosqlite

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, metadata TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
            )
            await db.commit()

    async def add(self, entry: MemoryEntry) -> None:
        import aiosqlite
        import json

        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO memory (role, content, metadata) VALUES (?, ?, ?)",
                (entry.role, entry.content, json.dumps(entry.metadata)),
            )
            await db.commit()

    async def get(self, limit: int = 10) -> list[MemoryEntry]:
        import aiosqlite
        import json

        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT role, content, metadata FROM memory ORDER BY id DESC LIMIT ?", (limit,)
            )
            rows = await cursor.fetchall()
            return [
                MemoryEntry(role=r[0], content=r[1], metadata=json.loads(r[2]) if r[2] else {})
                for r in rows
            ]

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        import aiosqlite
        import json

        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT role, content, metadata FROM memory WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{query}%", limit),
            )
            rows = await cursor.fetchall()
            return [
                MemoryEntry(role=r[0], content=r[1], metadata=json.loads(r[2]) if r[2] else {})
                for r in rows
            ]

    async def clear(self) -> None:
        import aiosqlite

        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM memory")
            await db.commit()


def create_memory(config: MemoryConfig) -> BaseMemory:
    registry: dict[MemoryBackend, type[BaseMemory]] = {
        MemoryBackend.SIMPLE: SimpleMemory,
        MemoryBackend.SQLITE: SQLiteMemory,
    }
    cls = registry.get(config.backend)
    if cls is None:
        raise ValueError(f"Unsupported memory backend: {config.backend}")
    return cls(config)
