from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.agentic.config import AgentOpsConfig
from app.agentic.telemetry import agentops_telemetry
from app.api.health import router as health_router
from app.api.items import router as items_router
from app.config import settings
from app.db.connection import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
for noisy_logger in ("sqlalchemy.engine", "sqlalchemy.pool", "sqlalchemy.dialects", "asyncpg"):
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

api_docs_enabled = settings.api_docs_enabled or settings.env != "production"


@asynccontextmanager
async def lifespan(_: FastAPI):
    agentops_config = AgentOpsConfig()
    agentops_telemetry.initialize(
        enabled=agentops_config.enabled,
        api_key=agentops_config.api_key,
        capture_content=agentops_config.capture_content,
        default_tags=agentops_config.tags,
        environment=agentops_config.environment,
        export_flush_interval=agentops_config.export_flush_interval,
        max_wait_time=agentops_config.max_wait_time,
        max_queue_size=agentops_config.max_queue_size,
    )
    # Create tables in development
    if settings.env == "development":
        await init_db()
    try:
        yield
    finally:
        agentops_telemetry.shutdown()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if api_docs_enabled else None,
    redoc_url="/redoc" if api_docs_enabled else None,
    openapi_url="/openapi.json" if api_docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("codestash.api")
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "api_error method=%s path=%s elapsed_ms=%s",
            request.method,
            request.url.path,
            round((time.perf_counter() - started) * 1000, 2),
        )
        raise
    logger.info(
        "api_response method=%s path=%s status=%s elapsed_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        round((time.perf_counter() - started) * 1000, 2),
    )
    return response


# ── Routes ──────────────────────────────────────────────────────────
# Health/status at root level
app.include_router(health_router, prefix="/api", tags=["System"])
# Entity routers under /api
app.include_router(items_router, prefix="/api/items", tags=["Items"])


# ── Root ────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": settings.app_name,
        "status": "running",
        "version": "0.1.0",
        "docs_enabled": api_docs_enabled,
    }
