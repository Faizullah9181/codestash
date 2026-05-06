"""
Async database session management.

Provides:
- `init_db()` — create all tables (dev convenience)
- `async_session()` — async context manager for manual queries
- `get_db()` — FastAPI dependency that yields an AsyncSession
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.env == "development",
    pool_size=5,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables. Use only in development."""
    from app.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session for use outside of FastAPI routes."""
    async with async_session_maker() as session:
        yield session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an AsyncSession."""
    async with async_session_maker() as session:
        yield session
