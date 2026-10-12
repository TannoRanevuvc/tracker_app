import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.bus import EventBus
from app.modules.calendar.models import Event


class CalendarService:
    def __init__(self, session: AsyncSession, bus: EventBus) -> None:
        self.session = session
        self.bus = bus

    async def _get_event_for_user(
        self, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> Event:
        result = await self.session.execute(
            select(Event).where(Event.id == event_id, Event.user_id == user_id)
        )
        event = result.scalars().first()
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return event

    async def _save(self, obj):
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_events_for_range(
        self, user_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[Event]:
        result = await self.session.execute(
            select(Event).where(
                Event.user_id == user_id,
                Event.start_at >= start,
                Event.start_at < end,
            ).order_by(Event.start_at)
        )
        return list(result.scalars().all())

    async def create_event(
        self,
        user_id: uuid.UUID,
        title: str,
        start_at: datetime,
        end_at: Optional[datetime] = None,
        all_day: bool = False,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Event:
        event = Event(
            user_id=user_id,
            title=title,
            start_at=start_at,
            end_at=end_at,
            all_day=all_day,
            color=color,
            description=description,
        )
        self.session.add(event)
        await self._save(event)
        await self.bus.publish(
            "calendar.event_created",
            {"event_id": str(event.id), "user_id": str(event.user_id)},
        )
        return event

    async def get_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> Event:
        return await self._get_event_for_user(user_id, event_id)

    async def update_event(
        self,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        title: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        all_day: Optional[bool] = None,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Event:
        event = await self._get_event_for_user(user_id, event_id)
        if title is not None:
            event.title = title
        if start_at is not None:
            event.start_at = start_at
        if end_at is not None:
            event.end_at = end_at
        if all_day is not None:
            event.all_day = all_day
        if color is not None:
            event.color = color
        if description is not None:
            event.description = description
        event.updated_at = datetime.now(event.start_at.tzinfo)
        return await self._save(event)

    async def delete_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> None:
        event = await self._get_event_for_user(user_id, event_id)
        await self.session.delete(event)
        await self.session.commit()
        await self.bus.publish(
            "calendar.event_deleted",
            {"event_id": str(event_id), "user_id": str(user_id)},
        )
