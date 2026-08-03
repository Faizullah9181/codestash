"""
Reusable Pydantic schemas and response models.

Provides:
- Base schema with id, created_at, updated_at
- Paginated response wrapper
- Common request/response patterns
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, field_serializer

T = TypeVar("T")


class SchemaBase(BaseModel):
    """Base schema — all response schemas should inherit from this."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _as_utc_iso(self, value: datetime) -> str:
        """Timestamps are stored naive-UTC; tag them so clients don't read them as local."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class CreateBase(BaseModel):
    """Base for create-request schemas. Override with your fields."""


class UpdateBase(BaseModel):
    """Base for update-request schemas. Override with your fields."""


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    items: list[T]
    total: int
    page: int
    limit: int
    has_more: bool


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str = "disconnected"


class AgentResponse(BaseModel):
    """Agent runtime and observability summary."""

    name: str
    provider: dict[str, Any]
    orchestration: dict[str, Any]
    pattern: dict[str, Any]
    memory: dict[str, Any]
    telemetry: dict[str, Any]
    agentops: dict[str, Any]
    probe: dict[str, Any] | None = None
