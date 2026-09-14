import uuid
from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.core.db import get_session
from app.core.events.bus import bus
from app.modules.habits.schemas import (
    CheckinCreate,
    CheckinResponse,
    HabitCreate,
    HabitResponse,
    HabitUpdate,
)
from app.modules.habits.service import HabitService

router = APIRouter(prefix="/api/habits", tags=["habits"])

_UserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


def _svc(session: AsyncSession = Depends(get_session)) -> HabitService:
    return HabitService(session, bus)


_Svc = Annotated[HabitService, Depends(_svc)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=HabitResponse)
async def create_habit(body: HabitCreate, user_id: _UserId, svc: _Svc):
    habit = await svc.create_habit(
        user_id=user_id,
        name=body.name,
        frequency_type=body.frequency_type,
        weekly_days=body.weekly_days,
    )
    return await svc.get_habit(user_id, habit.id)


@router.get("", response_model=list[HabitResponse])
async def list_habits(
    user_id: _UserId,
    svc: _Svc,
    include_archived: bool = Query(default=False),
):
    return await svc.list_habits(user_id=user_id, include_archived=include_archived)


@router.get("/{habit_id}", response_model=HabitResponse)
async def get_habit(habit_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    return await svc.get_habit(user_id=user_id, habit_id=habit_id)


@router.patch("/{habit_id}", response_model=HabitResponse)
async def update_habit(habit_id: uuid.UUID, body: HabitUpdate, user_id: _UserId, svc: _Svc):
    return await svc.update_habit(
        user_id=user_id,
        habit_id=habit_id,
        name=body.name,
        frequency_type=body.frequency_type,
        weekly_days=body.weekly_days,
    )


@router.post("/{habit_id}/archive", response_model=HabitResponse)
async def archive_habit(habit_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    return await svc.archive_habit(user_id=user_id, habit_id=habit_id)


@router.post(
    "/{habit_id}/checkins",
    status_code=status.HTTP_201_CREATED,
    response_model=CheckinResponse,
)
async def create_checkin(
    habit_id: uuid.UUID,
    user_id: _UserId,
    svc: _Svc,
    body: Optional[CheckinCreate] = Body(default=None),
):
    return await svc.create_checkin(
        user_id=user_id,
        habit_id=habit_id,
        checkin_date=body.date if body is not None else None,
    )


@router.delete(
    "/{habit_id}/checkins/{checkin_date}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_checkin(
    habit_id: uuid.UUID, checkin_date: date, user_id: _UserId, svc: _Svc
):
    await svc.delete_checkin(
        user_id=user_id, habit_id=habit_id, checkin_date=checkin_date
    )


@router.get("/{habit_id}/checkins", response_model=list[CheckinResponse])
async def list_checkins(
    habit_id: uuid.UUID,
    user_id: _UserId,
    svc: _Svc,
    from_date: Optional[date] = Query(default=None, alias="from"),
    to_date: Optional[date] = Query(default=None, alias="to"),
):
    return await svc.list_checkins(
        user_id=user_id,
        habit_id=habit_id,
        from_date=from_date,
        to_date=to_date,
    )
