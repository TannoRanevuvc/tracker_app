from collections import defaultdict
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

from app.core.auth.service import create_access_token
from tests.conftest import test_engine, test_session_factory

# ---------------------------------------------------------------------------
# Эталонный продукт из Open Food Facts (используется во всех OFF-моках)
# ---------------------------------------------------------------------------

_OFF_NUTELLA = {
    "external_id": "3017620422003",
    "name": "Nutella",
    "kcal_per_100g": 539.0,
    "protein_g_per_100g": 6.3,
    "fat_g_per_100g": 30.9,
    "carbs_g_per_100g": 57.5,
}


@pytest_asyncio.fixture(autouse=True)
async def clean_food_tables(create_tables):
    yield
    async with test_engine.begin() as conn:
        for table in (
            "food.meal_entry",
            "food.daily_goal",
            "food.product",
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
async def captured_food_events():
    """Подписывается на события food-модуля, накапливает payload'ы."""
    from app.core.events.bus import bus

    events: dict[str, list[dict]] = defaultdict(list)
    handlers = {}

    def make_handler(name: str):
        async def handler(payload: dict) -> None:
            events[name].append(payload)
        return handler

    for event_name in ("food.meal_logged", "food.daily_goal_reached"):
        h = make_handler(event_name)
        handlers[event_name] = h
        bus.subscribe(event_name, h)

    yield events

    for event_name, h in handlers.items():
        try:
            bus._subscribers[event_name].remove(h)
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# Моки Open Food Facts (этап 2)
# Патчим на уровне off_client, чтобы не делать реальных HTTP-запросов.
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_off_search():
    """OFF search → возвращает один продукт (Nutella)."""
    with patch(
        "app.modules.food.off_client.search_products", new_callable=AsyncMock
    ) as m:
        m.return_value = [_OFF_NUTELLA]
        yield m


@pytest.fixture
def mock_off_search_unavailable():
    """OFF search → таймаут (недоступность сервиса)."""
    with patch(
        "app.modules.food.off_client.search_products", new_callable=AsyncMock
    ) as m:
        m.side_effect = httpx.TimeoutException("OFF timeout")
        yield m


@pytest.fixture
def mock_off_get_found():
    """OFF get_product → продукт найден (Nutella)."""
    with patch(
        "app.modules.food.off_client.get_product", new_callable=AsyncMock
    ) as m:
        m.return_value = _OFF_NUTELLA
        yield m


@pytest.fixture
def mock_off_get_not_found():
    """OFF get_product → продукт не найден (API ответил, но такого external_id нет)."""
    with patch(
        "app.modules.food.off_client.get_product", new_callable=AsyncMock
    ) as m:
        m.return_value = None
        yield m


@pytest.fixture
def mock_off_get_unavailable():
    """OFF get_product → таймаут (недоступность сервиса)."""
    with patch(
        "app.modules.food.off_client.get_product", new_callable=AsyncMock
    ) as m:
        m.side_effect = httpx.TimeoutException("OFF timeout")
        yield m
