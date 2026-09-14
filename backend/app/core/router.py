from fastapi import APIRouter

from app.core.events.registry import MODULES

router = APIRouter(prefix="/api/core", tags=["core"])


@router.get("/modules")
async def get_modules():
    return [{"name": m.name, "enabled": m.enabled} for m in MODULES]
