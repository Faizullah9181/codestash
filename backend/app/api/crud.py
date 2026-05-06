"""
Reusable CRUD helpers for FastAPI + SQLAlchemy async.

Provides a generic `CRUD` class that handles the five common operations:
list (with pagination), get, create, update, delete.

Usage:
    from app.api.crud import CRUD
    from app.db.models import Item
    from app.db.connection import get_db

    item_crud = CRUD(Item)

    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        return await item_crud.list(db)
"""

from typing import Any, Generic, Type, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import PaginatedResponse

ModelType = TypeVar("ModelType", bound=Any)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class CRUD(Generic[ModelType]):
    """Generic CRUD operations for a SQLAlchemy model."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

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
        """List items with pagination and optional filters."""
        query = select(self.model)

        if filters:
            for col, val in filters.items():
                if hasattr(self.model, col):
                    query = query.where(getattr(self.model, col) == val)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        # Order
        col = getattr(self.model, order_by, self.model.created_at)
        query = query.order_by(col.desc() if descending else col.asc())

        # Paginate
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_more=(offset + limit) < total,
        )

    async def get(self, db: AsyncSession, item_id: int) -> ModelType:
        """Get a single item by ID. Raises 404 if not found."""
        result = await db.execute(select(self.model).where(self.model.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found")
        return item

    async def create(self, db: AsyncSession, schema: CreateSchema) -> ModelType:
        """Create a new item."""
        item = self.model(**schema.model_dump())
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def update(self, db: AsyncSession, item_id: int, schema: UpdateSchema) -> ModelType:
        """Update an item. Only non-None fields are applied."""
        item = await self.get(db, item_id)
        for key, value in schema.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        await db.commit()
        await db.refresh(item)
        return item

    async def delete(self, db: AsyncSession, item_id: int) -> dict[str, str]:
        """Delete an item by ID."""
        item = await self.get(db, item_id)
        await db.delete(item)
        await db.commit()
        return {"message": f"{self.model.__name__} deleted"}
