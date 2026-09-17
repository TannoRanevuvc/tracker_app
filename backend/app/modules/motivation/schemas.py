import datetime as _dt
from typing import Optional

from pydantic import BaseModel

_Datetime = _dt.datetime


class RecentAchievement(BaseModel):
    code: str
    name: str
    unlocked_at: _Datetime

    model_config = {"from_attributes": True}


class SummaryResponse(BaseModel):
    xp_total: int
    level: int
    xp_to_next_level: int
    recent_achievements: list[RecentAchievement]


class AchievementResponse(BaseModel):
    code: str
    name: str
    description: str
    unlocked: bool
    unlocked_at: Optional[_Datetime] = None
