import uuid
import datetime as _dt
from typing import Optional

from pydantic import BaseModel, model_validator

# Alias-импорт нужен, чтобы Pydantic v2 не путал имя поля `date` с типом
# datetime.date при разрешении аннотаций (в противном случае Optional[date]
# резолвится в дескриптор поля вместо типа и вызывает none_required).
_Date = _dt.date
_Datetime = _dt.datetime


class HabitCreate(BaseModel):
    name: str
    frequency_type: str
    weekly_days: Optional[list[int]] = None

    @model_validator(mode="after")
    def validate_weekly_days(self):
        if self.frequency_type == "weekly_days" and not self.weekly_days:
            raise ValueError("weekly_days is required when frequency_type is 'weekly_days'")
        return self


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    frequency_type: Optional[str] = None
    weekly_days: Optional[list[int]] = None


class HabitResponse(BaseModel):
    id: uuid.UUID
    name: str
    frequency_type: str
    weekly_days: Optional[list[int]] = None
    created_at: _Datetime
    archived_at: Optional[_Datetime] = None
    current_streak: int = 0
    done_today: bool = False

    model_config = {"from_attributes": True}


class CheckinCreate(BaseModel):
    date: Optional[_Date] = None


class CheckinResponse(BaseModel):
    id: uuid.UUID
    habit_id: uuid.UUID
    date: _Date
    note: Optional[str] = None
    created_at: _Datetime

    model_config = {"from_attributes": True}
