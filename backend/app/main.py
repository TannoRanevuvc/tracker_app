from fastapi import FastAPI

from app.core.auth.router import router as auth_router
from app.core.router import router as core_router
from app.core.db import async_session_factory
from app.core.events.bus import bus
from app.modules.habits.router import router as habits_router
from app.modules.tasks.router import router as tasks_router
from app.modules.finance.router import router as finance_router
from app.modules.food.router import router as food_router

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


# Регистрируем обработчики входящих событий для модуля tasks
async def _on_habit_completed(payload: dict) -> None:
    from app.modules.tasks.service import TaskService
    async with async_session_factory() as session:
        svc = TaskService(session, bus)
        await svc.on_habit_completed(payload)


bus.subscribe("habit.completed", _on_habit_completed)
