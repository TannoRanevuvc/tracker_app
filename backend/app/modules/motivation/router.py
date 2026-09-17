import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.core.db import get_session
from app.core.events.bus import bus
from app.modules.motivation.schemas import AchievementResponse, SummaryResponse
from app.modules.motivation.service import MotivationService

router = APIRouter(prefix="/api/motivation", tags=["motivation"])

_UserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


def _svc(session: AsyncSession = Depends(get_session)) -> MotivationService:
    return MotivationService(session, bus)


_Svc = Annotated[MotivationService, Depends(_svc)]


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(user_id: _UserId, svc: _Svc):
    return await svc.get_summary(user_id)


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(user_id: _UserId, svc: _Svc):
    return await svc.get_achievements(user_id)
