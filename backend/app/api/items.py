"""
Item controller — thin HTTP layer.

Pattern: Controller → Service → Repository → Model
- Controller: validates request, calls service, returns response
- Service: business logic (app/services/item_service.py)
- Repository: data access (app/repositories/item_repository.py)
- Model: SQLAlchemy model (app/db/models.py)

Copy this file for each new resource.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import PaginatedResponse, SchemaBase
from app.db.connection import get_db
from app.services.item_service import item_service

router = APIRouter()

# ── Schemas ──────────────────────────────────────────────────────


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: str = "active"


class ItemUpdate(BaseModel):
    """All fields optional — only sent fields are updated."""

    name: str | None = None
    description: str | None = None
    status: str | None = None


class ItemResponse(SchemaBase):
    name: str
    description: str | None
    status: str


# ── Routes ───────────────────────────────────────────────────────


@router.get("/", response_model=PaginatedResponse[ItemResponse])
async def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List items with pagination and optional status filter."""
    return await item_service.list_items(db, page=page, limit=limit, status=status)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single item by ID."""
    return await item_service.get_item(db, item_id)


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(body: ItemCreate, db: AsyncSession = Depends(get_db)):
    """Create a new item."""
    return await item_service.create_item(db, body.model_dump(exclude_unset=True))


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    body: ItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Partially update an item. Only sent fields are changed."""
    return await item_service.update_item(db, item_id, body.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an item."""
    await item_service.delete_item(db, item_id)
    return {"message": "Item deleted"}
