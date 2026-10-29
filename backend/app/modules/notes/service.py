import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.bus import EventBus
from app.modules.notes.models import Note


def parse_date_from_title(title: str) -> Optional[datetime]:
    """Extract a datetime from note title patterns like '05.10 в 13:00' or '15.03.2027'."""
    date_match = re.search(r'(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?', title)
    if not date_match:
        return None

    day = int(date_match.group(1))
    month = int(date_match.group(2))
    year_raw = date_match.group(3)

    if year_raw:
        year = int(year_raw)
        if year < 100:
            year += 2000
    else:
        year = datetime.now(timezone.utc).year

    # Look for time after the date match position, or anywhere in title
    remaining = title[date_match.end():]
    time_match = re.search(r'(?:в\s+)?(\d{1,2}):(\d{2})', remaining)
    if not time_match:
        # Try full title in case time appears before the date
        time_match = re.search(r'(\d{1,2}):(\d{2})', title)

    hour, minute = 0, 0
    if time_match:
        h = int(time_match.group(1))
        m = int(time_match.group(2))
        if 0 <= h <= 23 and 0 <= m <= 59:
            hour, minute = h, m

    try:
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    except ValueError:
        return None


class NoteService:
    def __init__(self, session: AsyncSession, bus: EventBus) -> None:
        self.session = session
        self.bus = bus

    async def _get_note_for_user(self, user_id: uuid.UUID, note_id: uuid.UUID) -> Note:
        result = await self.session.execute(
            select(Note).where(Note.id == note_id, Note.user_id == user_id)
        )
        note = result.scalars().first()
        if note is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return note

    async def _save(self, obj: Note) -> Note:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def list_notes(
        self,
        user_id: uuid.UUID,
        archived: bool = False,
        has_pin: Optional[bool] = None,
    ) -> list[Note]:
        q = select(Note).where(Note.user_id == user_id, Note.archived == archived)
        if has_pin is True:
            q = q.where(Note.pinned_at.is_not(None))
        elif has_pin is False:
            q = q.where(Note.pinned_at.is_(None))
        q = q.order_by(Note.pinned_at.nulls_last(), Note.created_at.desc())
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def create_note(
        self,
        user_id: uuid.UUID,
        title: str,
        body: Optional[str] = None,
        color: Optional[str] = None,
        pinned_at: Optional[datetime] = None,
    ) -> Note:
        resolved_pin = pinned_at if pinned_at is not None else parse_date_from_title(title)
        note = Note(
            user_id=user_id,
            title=title,
            body=body,
            color=color,
            pinned_at=resolved_pin,
        )
        self.session.add(note)
        await self._save(note)
        if resolved_pin is not None:
            await self.bus.publish(
                "note.pinned",
                {"note_id": str(note.id), "user_id": str(user_id), "pinned_at": resolved_pin.isoformat()},
            )
        return note

    async def get_note(self, user_id: uuid.UUID, note_id: uuid.UUID) -> Note:
        return await self._get_note_for_user(user_id, note_id)

    async def update_note(
        self,
        user_id: uuid.UUID,
        note_id: uuid.UUID,
        title: Optional[str] = None,
        body: Optional[str] = None,
        color: Optional[str] = None,
        pinned_at: Optional[datetime] = None,
        archived: Optional[bool] = None,
        clear_pin: bool = False,
    ) -> Note:
        note = await self._get_note_for_user(user_id, note_id)
        if title is not None:
            note.title = title
            # Re-parse date from new title only if pinned_at not explicitly provided
            if pinned_at is None and not clear_pin:
                parsed = parse_date_from_title(title)
                if parsed is not None:
                    note.pinned_at = parsed
        if pinned_at is not None:
            note.pinned_at = pinned_at
        if clear_pin:
            note.pinned_at = None
        if body is not None:
            note.body = body
        if color is not None:
            note.color = color
        if archived is not None:
            note.archived = archived
        note.updated_at = datetime.now(timezone.utc)
        return await self._save(note)

    async def delete_note(self, user_id: uuid.UUID, note_id: uuid.UUID) -> None:
        note = await self._get_note_for_user(user_id, note_id)
        await self.session.delete(note)
        await self.session.commit()
