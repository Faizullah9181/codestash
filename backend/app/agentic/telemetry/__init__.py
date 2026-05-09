"""Telemetry — OpenTelemetry-based tracing, logging, and observability."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from app.agentic.config import TelemetryConfig


@dataclass
class TraceSpan:
    name: str
    start_time: float
    end_time: float = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class Trace:
    id: str
    spans: list[TraceSpan] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Tracer:
    def __init__(self, config: TelemetryConfig) -> None:
        self.config = config
        self._traces: list[Trace] = []

    @asynccontextmanager
    async def span(
        self, name: str, metadata: dict[str, Any] | None = None
    ) -> AsyncIterator[TraceSpan]:
        span = TraceSpan(name=name, start_time=time.monotonic(), metadata=metadata or {})
        try:
            yield span
        except Exception as e:
            span.error = str(e)
            raise
        finally:
            span.end_time = time.monotonic()

    def trace(self, trace_id: str | None = None) -> Trace:
        import uuid

        t = Trace(id=trace_id or str(uuid.uuid4()))
        self._traces.append(t)
        return t

    def get_traces(self) -> list[Trace]:
        return self._traces

    def clear(self) -> None:
        self._traces.clear()
