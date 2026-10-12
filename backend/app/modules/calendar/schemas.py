import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EventCreate(BaseModel):
    title: str
    start_at: datetime
    end_at: Optional[datetime] = None
    all_day: bool = False
    color: Optional[str] = None
    description: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    all_day: Optional[bool] = None
    color: Optional[str] = None
    description: Optional[str] = None


class EventResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    start_at: datetime
    end_at: Optional[datetime] = None
    all_day: bool
    color: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
