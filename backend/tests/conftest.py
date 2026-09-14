import os
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.db import Base, get_session
from app.main import app as fastapi_app

_default_test_url = settings.database_url.replace("/tracker", "/tracker_test")
TEST_DATABASE_URL = os.getenv("DATABASE_URL_TEST", _default_test_url)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def create_tables():
    """Создаёт схемы и таблицы один раз на всю сессию."""
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS habits"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS tasks"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP SCHEMA IF EXISTS tasks CASCADE"))
        await conn.execute(text("DROP SCHEMA IF EXISTS habits CASCADE"))
        await conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE"))
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(create_tables):
    """Очищает таблицы после каждого теста — изоляция без nested transactions."""
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text('TRUNCATE core.refresh_token, core."user" CASCADE'))


@pytest_asyncio.fixture
async def db_session(create_tables):
    """Отдельная сессия для проверок состояния БД в тестах (читает committed данные)."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(create_tables):
    """HTTP-клиент. Роутер получает независимые сессии из test_session_factory."""
    async def override_get_session():
        async with test_session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(create_tables):
    """Создаёт тестового пользователя и коммитит — роутер должен видеть его в своей сессии."""
    from app.core.auth.models import User
    from app.core.auth.service import hash_password

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
    )
    async with test_session_factory() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user
