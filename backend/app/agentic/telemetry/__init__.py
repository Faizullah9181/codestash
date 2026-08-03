"""Telemetry — tracing and AgentOps observability helpers."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from importlib import import_module
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
        except Exception as exc:
            span.error = str(exc)
            raise
        finally:
            span.end_time = time.monotonic()

    def trace(self, trace_id: str | None = None) -> Trace:
        import uuid

        trace = Trace(id=trace_id or str(uuid.uuid4()))
        self._traces.append(trace)
        return trace

    def get_traces(self) -> list[Trace]:
        return self._traces

    def clear(self) -> None:
        self._traces.clear()


@dataclass(slots=True)
class AgentOpsTelemetryState:
    enabled: bool = False
    configured: bool = False
    capture_content: bool = False
    default_tags: list[str] = field(default_factory=list)
    environment: str = "development"
    error: str | None = None


class AgentOpsTelemetry:
    """Fail-safe AgentOps bootstrapper for generated projects."""

    def __init__(self) -> None:
        self._state = AgentOpsTelemetryState()
        self._sdk: Any | None = None

    def initialize(
        self,
        *,
        enabled: bool,
        api_key: str,
        capture_content: bool,
        default_tags: list[str],
        environment: str,
        export_flush_interval: int,
        max_wait_time: int,
        max_queue_size: int,
    ) -> dict[str, Any]:
        self._state = AgentOpsTelemetryState(
            enabled=enabled,
            configured=enabled and bool(api_key.strip()),
            capture_content=capture_content,
            default_tags=list(dict.fromkeys(default_tags)),
            environment=environment,
            error=None,
        )
        if not enabled:
            return self.describe()
        if not api_key.strip():
            self._state.error = "AGENTOPS_API_KEY is not configured"
            return self.describe()
        try:
            if self._sdk is None:
                self._sdk = import_module("agentops")
            self._sdk.init(
                api_key=api_key,
                auto_start_session=False,
                instrument_llm_calls=False,
                default_tags=self._state.default_tags,
                env_data_opt_out=True,
                fail_safe=True,
                log_session_replay_url=False,
                log_level="WARNING",
                export_flush_interval=export_flush_interval,
                max_wait_time=max_wait_time,
                max_queue_size=max_queue_size,
            )
        except (ModuleNotFoundError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
            self._state.error = self._safe_error(exc, api_key)
        return self.describe()

    def shutdown(self) -> None:
        self._state = AgentOpsTelemetryState()

    def describe(self) -> dict[str, Any]:
        return {
            "enabled": self._state.enabled,
            "configured": self._state.configured,
            "capture_content": self._state.capture_content,
            "default_tags": self._state.default_tags,
            "environment": self._state.environment,
            "error": self._state.error,
        }

    @staticmethod
    def _safe_error(exc: Exception, api_key: str) -> str:
        message = str(exc)
        if api_key and api_key in message:
            message = message.replace(api_key, "[redacted]")
        return message[:240]


agentops_telemetry = AgentOpsTelemetry()
