"""
Health and system status endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agentic.agent import Agent
from app.agentic.config import AgentConfig, AgentOpsConfig
from app.agentic.telemetry import agentops_telemetry
from app.config import settings
from app.db.connection import get_db
from app.api.schemas import AgentResponse, HealthResponse

router = APIRouter()


@router.get("/status", response_model=HealthResponse)
async def status(db: AsyncSession = Depends(get_db)):
    """System status including database connectivity."""
    db_status = "connected"
    try:
        await db.scalar(select(func.now()))
    except SQLAlchemyError:
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


@router.get("/agent", response_model=AgentResponse)
async def agent_info(probe: bool = False):
    """Report agent runtime configuration and telemetry state."""
    cfg = AgentConfig.from_env(name=settings.app_name)
    info = {
        "name": cfg.name,
        "provider": {
            "type": cfg.provider.type.value,
            "model": cfg.provider.model,
            "base_url": cfg.provider.base_url or "(default)",
            "configured": bool(cfg.provider.api_key.strip()),
        },
        "orchestration": {"framework": cfg.orchestration.framework.value},
        "pattern": {"type": cfg.pattern.type.value},
        "memory": {"backend": cfg.memory.backend.value},
        "telemetry": cfg.telemetry.describe(),
        "agentops": {
            **AgentOpsConfig(
                enabled=cfg.agentops.enabled,
                api_key=cfg.agentops.api_key,
                capture_content=cfg.agentops.capture_content,
                default_tags=cfg.agentops.default_tags,
                environment=cfg.agentops.environment,
                export_flush_interval=cfg.agentops.export_flush_interval,
                max_wait_time=cfg.agentops.max_wait_time,
                max_queue_size=cfg.agentops.max_queue_size,
            ).describe(),
            **agentops_telemetry.describe(),
        },
    }

    if probe:
        if cfg.provider.api_key.strip():
            try:
                agent = Agent.from_config(cfg.name, cfg)
                reply = await agent.chat("Reply with the single word: pong")
                info["probe"] = {"ok": True, "reply": (reply or "").strip()[:80]}
            except (RuntimeError, ValueError, TypeError) as exc:
                info["probe"] = {"ok": False, "error": str(exc)[:200]}
        else:
            info["probe"] = {
                "ok": False,
                "error": f"{cfg.provider.type.value} is not configured",
            }
    return info
