import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.core.db import get_session
from app.core.events.bus import bus
from app.modules.calendar.schemas import EventCreate, EventResponse, EventUpdate
from app.modules.calendar.service import CalendarService

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

_UserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


def _svc(session: AsyncSession = Depends(get_session)) -> CalendarService:
    return CalendarService(session, bus)


_Svc = Annotated[CalendarService, Depends(_svc)]


@router.get("/events", response_model=list[EventResponse])
async def list_events(
    user_id: _UserId,
    svc: _Svc,
    start: str = Query(..., description="ISO 8601 datetime"),
    end: str = Query(..., description="ISO 8601 datetime"),
):
    from datetime import datetime, timezone
    start_dt = datetime.fromisoformat(start).replace(tzinfo=timezone.utc) if datetime.fromisoformat(start).tzinfo is None else datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end).replace(tzinfo=timezone.utc) if datetime.fromisoformat(end).tzinfo is None else datetime.fromisoformat(end)
    return await svc.get_events_for_range(user_id=user_id, start=start_dt, end=end_dt)


@router.post("/events", status_code=status.HTTP_201_CREATED, response_model=EventResponse)
async def create_event(body: EventCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_event(
        user_id=user_id,
        title=body.title,
        start_at=body.start_at,
        end_at=body.end_at,
        all_day=body.all_day,
        color=body.color,
        description=body.description,
    )


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    return await svc.get_event(user_id=user_id, event_id=event_id)


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: uuid.UUID, body: EventUpdate, user_id: _UserId, svc: _Svc
):
    return await svc.update_event(
        user_id=user_id,
        event_id=event_id,
        title=body.title,
        start_at=body.start_at,
        end_at=body.end_at,
        all_day=body.all_day,
        color=body.color,
        description=body.description,
    )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    await svc.delete_event(user_id=user_id, event_id=event_id)
