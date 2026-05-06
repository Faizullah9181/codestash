"""
Health and system status endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.api.schemas import HealthResponse

router = APIRouter()


@router.get("/status", response_model=HealthResponse)
async def status(db: AsyncSession = Depends(get_db)):
    """System status including database connectivity."""
    db_status = "connected"
    try:
        await db.scalar(select(func.now()))
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="ok",
        version="0.1.0",
        database=db_status,
    )


@router.get("/health")
async def health():
    """Simple health check for load balancers."""
    return {"status": "healthy"}
