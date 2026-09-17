from app.core.db import async_session_factory
from app.core.events.bus import bus
from app.modules.motivation.service import MotivationService


async def on_habit_completed(payload: dict) -> None:
    async with async_session_factory() as session:
        await MotivationService(session, bus).on_habit_completed(payload)


async def on_streak_broken(payload: dict) -> None:
    pass


async def on_task_completed(payload: dict) -> None:
    async with async_session_factory() as session:
        await MotivationService(session, bus).on_task_completed(payload)


async def on_food_daily_goal_reached(payload: dict) -> None:
    async with async_session_factory() as session:
        await MotivationService(session, bus).on_food_daily_goal_reached(payload)


async def on_budget_exceeded(payload: dict) -> None:
    pass
