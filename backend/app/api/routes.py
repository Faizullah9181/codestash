from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def status() -> dict[str, str]:
    return {"service": "backend", "status": "running"}
