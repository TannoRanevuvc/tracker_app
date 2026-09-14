import uuid
from collections import defaultdict

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

from app.core.auth.service import create_access_token
from tests.conftest import test_engine, test_session_factory


@pytest_asyncio.fixture(autouse=True)
async def clean_habits_tables(create_tables):
    yield
    async with test_engine.begin() as conn:
        # habits.habit CASCADE захватывает habits.checkin через ON DELETE CASCADE.
        # DO-блок защищает от UndefinedTableError до завершения реализации (стаб
        # содержит устаревшее имя таблицы); после реализации ветка EXCEPTION не
        # выполняется никогда.
        await conn.execute(text("""
            DO $$ BEGIN
                TRUNCATE habits.habit CASCADE;
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$
        """))


@pytest_asyncio.fixture
async def authed_client(client: AsyncClient, test_user) -> AsyncClient:
    """AsyncClient с JWT access_token пользователя test_user в cookies."""
    token = create_access_token(test_user.id)
    client.cookies.set("access_token", token)
    return client


@pytest_asyncio.fixture
async def captured_events():
    """Подписывается на все события habits-модуля, возвращает словарь накопленных payload'ов."""
    from app.core.events.bus import bus

    events: dict[str, list[dict]] = defaultdict(list)
    handlers = {}

    def make_handler(name: str):
        async def handler(payload: dict) -> None:
            events[name].append(payload)
        return handler

    for event_name in ("habit.completed", "habit.streak_broken"):
        h = make_handler(event_name)
        handlers[event_name] = h
        bus.subscribe(event_name, h)

    yield events

    for event_name, h in handlers.items():
        try:
            bus._subscribers[event_name].remove(h)
        except ValueError:
            pass
