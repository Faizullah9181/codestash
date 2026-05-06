"""
Item service — business logic for items.

Services:
- Transform schemas → dicts before sending to the repository
- Enforce business rules (status transitions, validation, etc.)
- Orchestrate cross-model operations
- Keep controllers thin
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import PaginatedResponse
from app.repositories.item_repository import item_repository


class ItemService:
    """Business logic for items. Controller calls this; this calls the repository."""

    def __init__(self, repo=item_repository):
        self.repo = repo

    async def list_items(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
    ) -> PaginatedResponse:
        """List items with optional status filter."""
        filters = {"status": status} if status else None
        return await self.repo.list(db, page=page, limit=limit, filters=filters)

    async def get_item(self, db: AsyncSession, item_id: int):
        """Get item by ID."""
        return await self.repo.get(db, item_id)

    async def create_item(self, db: AsyncSession, data: dict):
        """Create a new item. `data` is already validated by the Pydantic schema."""
        # ── Business rules go here ────────────────────────────────
        # Example: enforce default status, compute derived fields, etc.
        if "status" not in data or data["status"] is None:
            data["status"] = "active"
        # ──────────────────────────────────────────────────────────
        return await self.repo.create(db, data)

    async def update_item(self, db: AsyncSession, item_id: int, data: dict):
        """Partial update. Only fields present in `data` are changed."""
        return await self.repo.update(db, item_id, data)

    async def delete_item(self, db: AsyncSession, item_id: int):
        """Delete item by ID."""
        await self.repo.delete(db, item_id)


# Singleton — import this in controllers
item_service = ItemService()
