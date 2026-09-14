import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.bus import EventBus
from app.modules.habits.models import Checkin, Habit

_APP_TZ = ZoneInfo("Asia/Tomsk")


def today_in_app_tz() -> date:
    return datetime.now(_APP_TZ).date()


def is_scheduled_day(
    frequency_type: str, weekly_days: Optional[list[int]], d: date
) -> bool:
    if frequency_type == "daily":
        return True
    return d.weekday() in (weekly_days or [])


def _prev_scheduled_day(
    d: date, frequency_type: str, weekly_days: Optional[list[int]]
) -> Optional[date]:
    """Most recent scheduled day strictly before d (looks back up to 7 days)."""
    for _ in range(7):
        d = d - timedelta(days=1)
        if is_scheduled_day(frequency_type, weekly_days, d):
            return d
    return None


def calculate_streak(
    checkin_dates: set[date],
    frequency_type: str,
    weekly_days: Optional[list[int]],
    today: date,
) -> tuple[int, bool, int]:
    """Return (current_streak, broken, previous_streak).

    broken is True only when there was a prior scheduled checkin that indicates a
    streak existed, and the most recent completed scheduled day has no checkin.
    previous_streak is the consecutive run that was active just before the break.
    """
    scheduled = {d for d in checkin_dates if is_scheduled_day(frequency_type, weekly_days, d)}

    if not scheduled:
        return (0, False, 0)

    last_complete = _prev_scheduled_day(today, frequency_type, weekly_days)

    if last_complete is None:
        # today is the first ever scheduled day
        if is_scheduled_day(frequency_type, weekly_days, today) and today in scheduled:
            return (1, False, 0)
        return (0, False, 0)

    if last_complete not in scheduled:
        # A scheduled day was missed — but only counts as "broken" if there was
        # previously an active streak (i.e., some checkin on or before last_complete)
        if not any(d <= last_complete for d in scheduled):
            # Habit only has today's or future checkins — streak just starting
            if is_scheduled_day(frequency_type, weekly_days, today) and today in scheduled:
                return (1, False, 0)
            return (0, False, 0)

        # Count the consecutive run that ended before the gap
        most_recent = max(scheduled)
        prev = 0
        d = most_recent
        while d is not None and d in scheduled:
            prev += 1
            d = _prev_scheduled_day(d, frequency_type, weekly_days)
        return (0, True, prev)

    # Streak is intact — walk backwards from today (if checked) or last_complete
    start = (
        today
        if (is_scheduled_day(frequency_type, weekly_days, today) and today in scheduled)
        else last_complete
    )
    count = 0
    d = start
    while d is not None and d in scheduled:
        count += 1
        d = _prev_scheduled_day(d, frequency_type, weekly_days)
    return (count, False, 0)


# In-process dedup: (habit_id_str, date) — resets naturally as the date changes.
_streak_broken_today: dict[tuple[str, date], bool] = {}


class HabitService:
    def __init__(self, session: AsyncSession, bus: EventBus) -> None:
        self.session = session
        self.bus = bus

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_habit_for_user(
        self, user_id: uuid.UUID, habit_id: uuid.UUID
    ) -> Habit:
        result = await self.session.execute(
            select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
        )
        habit = result.scalars().first()
        if habit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return habit

    async def _save_and_stats(self, habit: Habit) -> dict:
        await self.session.commit()
        await self.session.refresh(habit)
        return await self._habit_stats(habit)

    async def _habit_stats(self, habit: Habit) -> dict:
        today = today_in_app_tz()
        result = await self.session.execute(
            select(Checkin).where(Checkin.habit_id == habit.id)
        )
        checkin_dates = {c.date for c in result.scalars().all()}

        streak, broken, prev_streak = calculate_streak(
            checkin_dates, habit.frequency_type, habit.weekly_days, today
        )

        if broken:
            key = (str(habit.id), today)
            if key not in _streak_broken_today:
                _streak_broken_today[key] = True
                await self.bus.publish(
                    "habit.streak_broken",
                    {
                        "habit_id": str(habit.id),
                        "user_id": str(habit.user_id),
                        "previous_streak": prev_streak,
                    },
                )

        done_today = (
            is_scheduled_day(habit.frequency_type, habit.weekly_days, today)
            and today in checkin_dates
        )

        return {
            "id": habit.id,
            "name": habit.name,
            "frequency_type": habit.frequency_type,
            "weekly_days": habit.weekly_days,
            "created_at": habit.created_at,
            "archived_at": habit.archived_at,
            "current_streak": streak,
            "done_today": done_today,
        }

    # ------------------------------------------------------------------
    # Habits CRUD
    # ------------------------------------------------------------------

    async def create_habit(
        self,
        user_id: uuid.UUID,
        name: str,
        frequency_type: str,
        weekly_days: Optional[list[int]],
    ) -> Habit:
        habit = Habit(
            user_id=user_id,
            name=name,
            frequency_type=frequency_type,
            weekly_days=weekly_days,
        )
        self.session.add(habit)
        await self.session.commit()
        await self.session.refresh(habit)
        return habit

    async def get_habit(self, user_id: uuid.UUID, habit_id: uuid.UUID) -> dict:
        habit = await self._get_habit_for_user(user_id, habit_id)
        return await self._habit_stats(habit)

    async def list_habits(
        self, user_id: uuid.UUID, include_archived: bool = False
    ) -> list[dict]:
        q = select(Habit).where(Habit.user_id == user_id)
        if not include_archived:
            q = q.where(Habit.archived_at.is_(None))
        result = await self.session.execute(q)
        return [await self._habit_stats(h) for h in result.scalars().all()]

    async def update_habit(
        self,
        user_id: uuid.UUID,
        habit_id: uuid.UUID,
        name: Optional[str],
        frequency_type: Optional[str],
        weekly_days: Optional[list[int]],
    ) -> dict:
        habit = await self._get_habit_for_user(user_id, habit_id)
        if name is not None:
            habit.name = name
        if frequency_type is not None:
            habit.frequency_type = frequency_type
        if weekly_days is not None:
            habit.weekly_days = weekly_days
        return await self._save_and_stats(habit)

    async def archive_habit(self, user_id: uuid.UUID, habit_id: uuid.UUID) -> dict:
        habit = await self._get_habit_for_user(user_id, habit_id)
        habit.archived_at = datetime.now(UTC)
        return await self._save_and_stats(habit)

    # ------------------------------------------------------------------
    # Checkins
    # ------------------------------------------------------------------

    async def create_checkin(
        self,
        user_id: uuid.UUID,
        habit_id: uuid.UUID,
        checkin_date: Optional[date] = None,
    ) -> Checkin:
        habit = await self._get_habit_for_user(user_id, habit_id)
        if checkin_date is None:
            checkin_date = today_in_app_tz()

        checkin = Checkin(habit_id=habit_id, date=checkin_date)
        self.session.add(checkin)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        await self.session.refresh(checkin)

        if is_scheduled_day(habit.frequency_type, habit.weekly_days, checkin_date):
            result = await self.session.execute(
                select(Checkin).where(Checkin.habit_id == habit_id)
            )
            all_dates = {c.date for c in result.scalars().all()}
            today = today_in_app_tz()
            streak, _, _ = calculate_streak(
                all_dates, habit.frequency_type, habit.weekly_days, today
            )
            await self.bus.publish(
                "habit.completed",
                {
                    "habit_id": str(habit.id),
                    "user_id": str(habit.user_id),
                    "date": str(checkin_date),
                    "current_streak": streak,
                },
            )

        return checkin

    async def delete_checkin(
        self, user_id: uuid.UUID, habit_id: uuid.UUID, checkin_date: date
    ) -> None:
        await self._get_habit_for_user(user_id, habit_id)
        result = await self.session.execute(
            select(Checkin).where(
                Checkin.habit_id == habit_id, Checkin.date == checkin_date
            )
        )
        checkin = result.scalars().first()
        if checkin is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await self.session.delete(checkin)
        await self.session.commit()

    async def list_checkins(
        self,
        user_id: uuid.UUID,
        habit_id: uuid.UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[Checkin]:
        await self._get_habit_for_user(user_id, habit_id)
        q = select(Checkin).where(Checkin.habit_id == habit_id)
        if from_date is not None:
            q = q.where(Checkin.date >= from_date)
        if to_date is not None:
            q = q.where(Checkin.date <= to_date)
        result = await self.session.execute(q)
        return result.scalars().all()
