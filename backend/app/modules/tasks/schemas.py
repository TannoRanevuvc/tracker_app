import uuid
import datetime as _dt
from typing import Optional

from pydantic import BaseModel

_Date = _dt.date
_Datetime = _dt.datetime


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[_Date] = None
    tag: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[_Date] = None
    tag: Optional[str] = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    tag: Optional[str] = None
    due_date: Optional[_Date] = None
    created_at: _Datetime
    completed_at: Optional[_Datetime] = None
    is_overdue: bool = False

    model_config = {"from_attributes": True}


class HabitTaskLinkCreate(BaseModel):
    habit_id: uuid.UUID
    task_title_template: str


class HabitTaskLinkUpdate(BaseModel):
    enabled: Optional[bool] = None
    task_title_template: Optional[str] = None


class HabitTaskLinkResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    habit_id: uuid.UUID
    task_title_template: str
    enabled: bool

    model_config = {"from_attributes": True}
