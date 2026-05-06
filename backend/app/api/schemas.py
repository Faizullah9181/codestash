"""
Reusable Pydantic schemas and response models.

Provides:
- Base schema with id, created_at, updated_at
- Paginated response wrapper
- Common request/response patterns
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class SchemaBase(BaseModel):
    """Base schema — all response schemas should inherit from this."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


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
