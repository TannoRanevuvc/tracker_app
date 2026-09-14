from collections import defaultdict

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

from app.core.auth.service import create_access_token
from tests.conftest import test_engine, test_session_factory


@pytest_asyncio.fixture(autouse=True)
async def clean_finance_tables(create_tables):
    yield
    async with test_engine.begin() as conn:
        for table in (
            "finance.transaction",
            "finance.recurring_rule",
            "finance.budget",
            "finance.category",
            "finance.account",
        ):
            await conn.execute(text(f"""
                DO $$ BEGIN
                    TRUNCATE {table} CASCADE;
                EXCEPTION WHEN undefined_table THEN NULL;
                END $$
            """))


@pytest_asyncio.fixture
async def authed_client(client: AsyncClient, test_user) -> AsyncClient:
    token = create_access_token(test_user.id)
    client.cookies.set("access_token", token)
    return client


@pytest_asyncio.fixture
async def captured_finance_events():
    """Подписывается на события finance-модуля, накапливает payload'ы."""
    from app.core.events.bus import bus

    events: dict[str, list[dict]] = defaultdict(list)
    handlers = {}

    def make_handler(name: str):
        async def handler(payload: dict) -> None:
            events[name].append(payload)
        return handler

    for event_name in ("finance.transaction_added", "finance.budget_exceeded"):
        h = make_handler(event_name)
        handlers[event_name] = h
        bus.subscribe(event_name, h)

    yield events

    for event_name, h in handlers.items():
        try:
            bus._subscribers[event_name].remove(h)
        except ValueError:
            pass
