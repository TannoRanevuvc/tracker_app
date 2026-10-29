import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.core.db import get_session
from app.core.events.bus import bus
from app.modules.notes.schemas import NoteCreate, NoteResponse, NoteUpdate
from app.modules.notes.service import NoteService

router = APIRouter(prefix="/api/notes", tags=["notes"])

_UserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


def _svc(session: AsyncSession = Depends(get_session)) -> NoteService:
    return NoteService(session, bus)


_Svc = Annotated[NoteService, Depends(_svc)]


@router.get("", response_model=list[NoteResponse])
async def list_notes(
    user_id: _UserId,
    svc: _Svc,
    archived: bool = Query(False),
    has_pin: Optional[bool] = Query(None),
):
    return await svc.list_notes(user_id=user_id, archived=archived, has_pin=has_pin)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=NoteResponse)
async def create_note(body: NoteCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_note(
        user_id=user_id,
        title=body.title,
        body=body.body,
        color=body.color,
        pinned_at=body.pinned_at,
    )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    return await svc.get_note(user_id=user_id, note_id=note_id)


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: uuid.UUID, body: NoteUpdate, user_id: _UserId, svc: _Svc):
    return await svc.update_note(
        user_id=user_id,
        note_id=note_id,
        title=body.title,
        body=body.body,
        color=body.color,
        pinned_at=body.pinned_at,
        archived=body.archived,
    )


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    await svc.delete_note(user_id=user_id, note_id=note_id)
