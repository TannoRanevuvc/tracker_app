import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NoteCreate(BaseModel):
    title: str
    body: Optional[str] = None
    color: Optional[str] = None
    pinned_at: Optional[datetime] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    color: Optional[str] = None
    pinned_at: Optional[datetime] = None
    archived: Optional[bool] = None


class NoteResponse(BaseModel):
    id: uuid.UUID
    title: str
    body: Optional[str] = None
    pinned_at: Optional[datetime] = None
    color: Optional[str] = None
    archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
