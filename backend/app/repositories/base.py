"""
Base repository — generic data-access operations.

Provides list (paginated + filtered), get, create, update, delete.
Subclass per model and override `model` to add custom queries.
"""

from typing import Any, Generic, Type, TypeVar

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import PaginatedResponse

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Data-access layer. Talks directly to SQLAlchemy.

    Subclass and set `model` to add model-specific queries.
    Example:
        class ItemRepository(BaseRepository[Item]):
            model = Item

            async def find_by_status(self, db, status, ...):
                ...
    """

    model: Type[ModelType]

    async def list(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        limit: int = 20,
        order_by: str = "created_at",
        descending: bool = True,
        filters: dict[str, Any] | None = None,
    ) -> PaginatedResponse:
        """Paginated list with optional equality filters."""
        query = select(self.model)

        if filters:
            for col, val in filters.items():
                if hasattr(self.model, col):
                    query = query.where(getattr(self.model, col) == val)

        total = await db.scalar(
            select(func.count()).select_from(query.subquery())
        ) or 0

        col = getattr(self.model, order_by, self.model.created_at)
        query = query.order_by(col.desc() if descending else col.asc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await db.execute(query)
        items = list(result.scalars().all())

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_more=((page - 1) * limit + len(items)) < total,
        )

    async def get(self, db: AsyncSession, item_id: int) -> ModelType:
        """Get by ID. Raises 404 if missing."""
        result = await db.execute(
            select(self.model).where(self.model.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found")
        return item

    async def create(self, db: AsyncSession, data: dict) -> ModelType:
        """Insert a new row."""
        item = self.model(**data)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def update(self, db: AsyncSession, item_id: int, data: dict) -> ModelType:
        """Partial update — only keys present in `data` are changed."""
        item = await self.get(db, item_id)
        for key, value in data.items():
            setattr(item, key, value)
        await db.commit()
        await db.refresh(item)
        return item

    async def delete(self, db: AsyncSession, item_id: int) -> None:
        """Delete by ID. Raises 404 if missing."""
        item = await self.get(db, item_id)
        await db.delete(item)
        await db.commit()