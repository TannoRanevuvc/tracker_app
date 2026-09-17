from collections import defaultdict

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

from app.core.auth.service import create_access_token
from tests.conftest import test_engine, test_session_factory


@pytest_asyncio.fixture(autouse=True)
async def clean_motivation_tables(create_tables):
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text("""
            DO $$ BEGIN
                TRUNCATE motivation.user_achievement CASCADE;
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                TRUNCATE motivation.user_progress CASCADE;
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$
        """))
        # achievement — статический каталог, очищается только если нужна перезасевка
        await conn.execute(text("""
            DO $$ BEGIN
                TRUNCATE motivation.achievement CASCADE;
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$
        """))


@pytest_asyncio.fixture
async def seed_catalog(create_tables):
    """Заполняет таблицу motivation.achievement из Python-константы catalog.ACHIEVEMENTS."""
    from app.modules.motivation.catalog import ACHIEVEMENTS

    async with test_session_factory() as session:
        for item in ACHIEVEMENTS:
            await session.execute(
                text("""
                    INSERT INTO motivation.achievement (code, name, description)
                    VALUES (:code, :name, :description)
                    ON CONFLICT (code) DO NOTHING
                """),
                {"code": item["code"], "name": item["name"], "description": item["description"]},
            )
        await session.commit()


@pytest_asyncio.fixture
async def authed_client(client: AsyncClient, test_user) -> AsyncClient:
    token = create_access_token(test_user.id)
    client.cookies.set("access_token", token)
    return client


@pytest_asyncio.fixture
async def captured_motivation_events():
    """Подписывается на все события motivation-модуля, возвращает словарь накопленных payload'ов."""
    from app.core.events.bus import bus

    events: dict[str, list[dict]] = defaultdict(list)
    handlers = {}

    def make_handler(name: str):
        async def handler(payload: dict) -> None:
            events[name].append(payload)
        return handler

    for event_name in (
        "motivation.xp_awarded",
        "motivation.level_up",
        "motivation.achievement_unlocked",
    ):
        h = make_handler(event_name)
        handlers[event_name] = h
        bus.subscribe(event_name, h)

    yield events

    for event_name, h in handlers.items():
        try:
            bus._subscribers[event_name].remove(h)
        except ValueError:
            pass
