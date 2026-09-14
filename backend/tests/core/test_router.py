"""
Интеграционные тесты API core-модуля.
httpx.AsyncClient + тестовая Postgres-схема через фикстуры conftest.py.

Покрывает AC#1–AC#6, AC#8 из specs/core.md §8.
"""
import pytest
from httpx import AsyncClient


LOGIN_URL = "/api/auth/login"
LOGOUT_URL = "/api/auth/logout"
REFRESH_URL = "/api/auth/refresh"
ME_URL = "/api/auth/me"
MODULES_URL = "/api/core/modules"

VALID_CREDENTIALS = {"email": "test@example.com", "password": "testpassword123"}


# ---------------------------------------------------------------------------
# AC#1 — Login с верными данными → 200 + cookies + запись refresh_token в БД
# ---------------------------------------------------------------------------

class TestLoginSuccess:
    async def test_returns_200(self, client: AsyncClient, test_user):
        resp = await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        assert resp.status_code == 200

    async def test_sets_access_token_cookie(self, client: AsyncClient, test_user):
        resp = await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        assert "access_token" in resp.cookies

    async def test_sets_refresh_token_cookie(self, client: AsyncClient, test_user):
        resp = await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        assert "refresh_token" in resp.cookies

    async def test_access_token_cookie_is_httponly(self, client: AsyncClient, test_user):
        resp = await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        cookie_header = resp.headers.get("set-cookie", "")
        assert "HttpOnly" in cookie_header

    async def test_creates_refresh_token_record_in_db(
        self, client: AsyncClient, test_user, db_session
    ):
        from sqlalchemy import select
        from app.core.auth.models import RefreshToken

        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)

        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == test_user.id)
        )
        assert result.scalars().first() is not None

    async def test_response_body_contains_user_info(self, client: AsyncClient, test_user):
        resp = await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        data = resp.json()
        assert "user" in data or "email" in data  # зависит от схемы ответа реализации


# ---------------------------------------------------------------------------
# AC#2 — Неверный пароль → 401, cookies не устанавливаются
# ---------------------------------------------------------------------------

class TestLoginFailure:
    async def test_wrong_password_returns_401(self, client: AsyncClient, test_user):
        resp = await client.post(
            LOGIN_URL, json={"email": "test@example.com", "password": "wrongpassword"}
        )
        assert resp.status_code == 401

    async def test_wrong_password_no_access_token_cookie(self, client: AsyncClient, test_user):
        resp = await client.post(
            LOGIN_URL, json={"email": "test@example.com", "password": "wrongpassword"}
        )
        assert "access_token" not in resp.cookies

    async def test_wrong_password_no_refresh_token_cookie(self, client: AsyncClient, test_user):
        resp = await client.post(
            LOGIN_URL, json={"email": "test@example.com", "password": "wrongpassword"}
        )
        assert "refresh_token" not in resp.cookies

    async def test_unknown_email_returns_401(self, client: AsyncClient):
        resp = await client.post(
            LOGIN_URL, json={"email": "ghost@example.com", "password": "password"}
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# AC#3 — Нет cookie → GET /me → 401
# ---------------------------------------------------------------------------

class TestMeUnauthenticated:
    async def test_me_without_cookie_returns_401(self, client: AsyncClient):
        resp = await client.get(ME_URL)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# AC#4 — Валидный access_token → GET /me → 200 + данные пользователя
# ---------------------------------------------------------------------------

class TestMeAuthenticated:
    async def test_me_after_login_returns_200(self, client: AsyncClient, test_user):
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        resp = await client.get(ME_URL)
        assert resp.status_code == 200

    async def test_me_returns_email(self, client: AsyncClient, test_user):
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        resp = await client.get(ME_URL)
        assert resp.json()["email"] == "test@example.com"

    async def test_me_returns_id(self, client: AsyncClient, test_user):
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        resp = await client.get(ME_URL)
        assert "id" in resp.json()

    async def test_me_does_not_return_password_hash(self, client: AsyncClient, test_user):
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        resp = await client.get(ME_URL)
        assert "password_hash" not in resp.json()


# ---------------------------------------------------------------------------
# AC#5 — Валидный refresh_token → POST /refresh → 200 + новый access_token cookie
# ---------------------------------------------------------------------------

class TestRefresh:
    async def test_refresh_with_valid_cookie_returns_200(self, client: AsyncClient, test_user):
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        resp = await client.post(REFRESH_URL)
        assert resp.status_code == 200

    async def test_refresh_sets_new_access_token_cookie(self, client: AsyncClient, test_user):
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        resp = await client.post(REFRESH_URL)
        assert "access_token" in resp.cookies

    async def test_refresh_without_cookie_returns_401(self, client: AsyncClient):
        resp = await client.post(REFRESH_URL)
        assert resp.status_code == 401

    async def test_refresh_me_works_after_refresh(self, client: AsyncClient, test_user):
        """Новый access_token, полученный через /refresh, принимается в /me."""
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        await client.post(REFRESH_URL)
        resp = await client.get(ME_URL)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# AC#6 — После logout тот же refresh_token → 401
# ---------------------------------------------------------------------------

class TestLogout:
    async def test_logout_returns_204(self, client: AsyncClient, test_user):
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        resp = await client.post(LOGOUT_URL)
        assert resp.status_code == 204

    async def test_refresh_after_logout_returns_401(self, client: AsyncClient, test_user):
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        await client.post(LOGOUT_URL)
        resp = await client.post(REFRESH_URL)
        assert resp.status_code == 401

    async def test_me_after_logout_returns_401(self, client: AsyncClient, test_user):
        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        await client.post(LOGOUT_URL)
        resp = await client.get(ME_URL)
        assert resp.status_code == 401

    async def test_logout_marks_refresh_token_revoked_in_db(
        self, client: AsyncClient, test_user, db_session
    ):
        from sqlalchemy import select
        from app.core.auth.models import RefreshToken

        await client.post(LOGIN_URL, json=VALID_CREDENTIALS)
        await client.post(LOGOUT_URL)

        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == test_user.id)
        )
        token_record = result.scalars().first()
        assert token_record is not None
        assert token_record.revoked_at is not None


# ---------------------------------------------------------------------------
# AC#8 — GET /api/core/modules отдаёт список модулей с флагом enabled
# ---------------------------------------------------------------------------

class TestModules:
    async def test_modules_returns_200(self, client: AsyncClient):
        resp = await client.get(MODULES_URL)
        assert resp.status_code == 200

    async def test_modules_does_not_require_auth(self, client: AsyncClient):
        """Эндпоинт публичный — нет cookie, всё равно 200 (specs/core.md §7)."""
        resp = await client.get(MODULES_URL)
        assert resp.status_code == 200

    async def test_modules_returns_list(self, client: AsyncClient):
        resp = await client.get(MODULES_URL)
        assert isinstance(resp.json(), list)

    async def test_modules_items_have_name_and_enabled(self, client: AsyncClient):
        resp = await client.get(MODULES_URL)
        for item in resp.json():
            assert "name" in item
            assert "enabled" in item

    async def test_finance_is_present_and_enabled(self, client: AsyncClient):
        """specs/core.md §6 — finance.enabled = True (модуль реализован и подключён)."""
        resp = await client.get(MODULES_URL)
        by_name = {m["name"]: m["enabled"] for m in resp.json()}
        assert "finance" in by_name
        assert by_name["finance"] is True

    async def test_food_is_present_and_disabled(self, client: AsyncClient):
        """specs/core.md §6 — food.enabled = False."""
        resp = await client.get(MODULES_URL)
        by_name = {m["name"]: m["enabled"] for m in resp.json()}
        assert "food" in by_name
        assert by_name["food"] is False

    async def test_habits_is_present_and_enabled(self, client: AsyncClient):
        """habits зарегистрирован — модуль должен быть enabled."""
        resp = await client.get(MODULES_URL)
        by_name = {m["name"]: m["enabled"] for m in resp.json()}
        assert "habits" in by_name
        assert by_name["habits"] is True
