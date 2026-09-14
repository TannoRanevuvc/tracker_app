from fastapi import FastAPI

from app.core.auth.router import router as auth_router
from app.core.router import router as core_router
from app.core.db import async_session_factory
from app.core.events.bus import bus
from app.modules.habits.router import router as habits_router
from app.modules.tasks.router import router as tasks_router
from app.modules.finance.router import router as finance_router
from app.modules.food.router import router as food_router
from app.modules.motivation.router import router as motivation_router

import app.modules.habits.events as habits_events
import app.modules.tasks.events as tasks_events
import app.modules.finance.events as finance_events
import app.modules.food.events as food_events
import app.modules.motivation.events as motivation_events

app = FastAPI(title="tracker-app")

app.include_router(auth_router)
app.include_router(core_router)
app.include_router(habits_router)
app.include_router(tasks_router)
app.include_router(finance_router)
app.include_router(food_router)
app.include_router(motivation_router)


# Регистрируем обработчики входящих событий для модуля tasks
async def _tasks_on_habit_completed(payload: dict) -> None:
    from app.modules.tasks.service import TaskService
    async with async_session_factory() as session:
        svc = TaskService(session, bus)
        await svc.on_habit_completed(payload)


bus.subscribe("habit.completed", _tasks_on_habit_completed)


# Регистрируем обработчики входящих событий для модуля finance
async def _finance_on_food_meal_logged(payload: dict) -> None:
    from app.modules.finance.service import FinanceService
    async with async_session_factory() as session:
        svc = FinanceService(session, bus)
        await svc.on_food_meal_logged(payload)


bus.subscribe("food.meal_logged", _finance_on_food_meal_logged)


# Регистрируем обработчики входящих событий для модуля motivation
import app.modules.motivation.handlers as motivation_handlers

bus.subscribe("habit.completed", motivation_handlers.on_habit_completed)
bus.subscribe("habit.streak_broken", motivation_handlers.on_streak_broken)
bus.subscribe("task.completed", motivation_handlers.on_task_completed)
bus.subscribe("food.daily_goal_reached", motivation_handlers.on_food_daily_goal_reached)
bus.subscribe("finance.budget_exceeded", motivation_handlers.on_budget_exceeded)
