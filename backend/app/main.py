from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.encoders import ENCODERS_BY_TYPE
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.items import router as items_router
from app.config import settings
from app.db.connection import init_db


# ── Ensure all naive datetimes are serialised with a trailing "Z" ──
def _utc_datetime_encoder(dt: datetime) -> str:
    return dt.isoformat() + "Z"


ENCODERS_BY_TYPE[datetime] = _utc_datetime_encoder


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables in development
    if settings.env == "development":
        await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if settings.env == "production" else "/docs",
    redoc_url=None if settings.env == "production" else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────────────────────
# Health/status at root level
app.include_router(health_router, prefix="/api", tags=["System"])
# Entity routers under /api
app.include_router(items_router, prefix="/api/items", tags=["Items"])


# ── Root ────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": settings.app_name, "status": "running", "version": "0.1.0"}
