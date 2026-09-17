"""
Интеграционные тесты API motivation-модуля.
httpx.AsyncClient + тестовая Postgres-схема через фикстуры conftest.py.

Покрытие критериев приёмки из specs/motivation.md §7:
  AC#1 — TestSummaryEndpoint (xp_total=0 → 0; после habit.completed → 10)
  AC#2 — TestLevelUpViaApi (level меняется при пересечении порога)
  AC#3 — TestAchievementsEndpoint (streak_7 → achievement unlocked)
  AC#4 — TestAchievementsEndpoint (дубликат streak_7 не создаётся)
  AC#5 — TestSummaryEndpoint (task high/low → разный XP)
  AC#6 — TestBudgetExceededViaApi (finance.budget_exceeded → XP не меняется)
  AC#7 — проверяется в test_events.py на уровне сервиса
"""

import uuid

import pytest
from httpx import AsyncClient

SUMMARY_URL = "/api/motivation/summary"
ACHIEVEMENTS_URL = "/api/motivation/achievements"


# ---------------------------------------------------------------------------
# Авторизация
# ---------------------------------------------------------------------------

class TestAuth:
    async def test_summary_without_auth_returns_401(self, client: AsyncClient):
        resp = await client.get(SUMMARY_URL)
        assert resp.status_code == 401

    async def test_achievements_without_auth_returns_401(self, client: AsyncClient):
        resp = await client.get(ACHIEVEMENTS_URL)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/motivation/summary — структура ответа
# ---------------------------------------------------------------------------

class TestSummaryEndpoint:
    async def test_returns_200(self, authed_client: AsyncClient, seed_catalog):
        resp = await authed_client.get(SUMMARY_URL)
        assert resp.status_code == 200

    async def test_initial_summary_xp_zero(self, authed_client: AsyncClient, seed_catalog):
        resp = await authed_client.get(SUMMARY_URL)
        body = resp.json()
        assert body["xp_total"] == 0

    async def test_initial_summary_level_one(self, authed_client: AsyncClient, seed_catalog):
        resp = await authed_client.get(SUMMARY_URL)
        assert resp.json()["level"] == 1

    async def test_initial_summary_xp_to_next_level_100(self, authed_client: AsyncClient, seed_catalog):
        resp = await authed_client.get(SUMMARY_URL)
        assert resp.json()["xp_to_next_level"] == 100

    async def test_initial_summary_recent_achievements_empty(self, authed_client: AsyncClient, seed_catalog):
        resp = await authed_client.get(SUMMARY_URL)
        assert resp.json()["recent_achievements"] == []

    # AC#1: после habit.completed xp_total = 10
    async def test_xp_increases_after_habit_completed(
        self, authed_client: AsyncClient, test_user, seed_catalog
    ):
        from app.core.events.bus import bus
        from app.modules.motivation.service import MotivationService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = MotivationService(session, bus)
            await svc.on_habit_completed({
                "habit_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "date": "2024-01-10",
                "current_streak": 1,
            })

        resp = await authed_client.get(SUMMARY_URL)
        assert resp.json()["xp_total"] == 10

    # AC#5: task high → xp=10
    async def test_xp_increases_after_high_priority_task(
        self, authed_client: AsyncClient, test_user, seed_catalog
    ):
        from app.core.events.bus import bus
        from app.modules.motivation.service import MotivationService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = MotivationService(session, bus)
            await svc.on_task_completed({
                "task_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "completed_at": "2024-01-10T10:00:00",
                "priority": "high",
            })

        resp = await authed_client.get(SUMMARY_URL)
        assert resp.json()["xp_total"] == 10

    # AC#5: task low → xp=5
    async def test_xp_increases_after_low_priority_task(
        self, authed_client: AsyncClient, test_user, seed_catalog
    ):
        from app.core.events.bus import bus
        from app.modules.motivation.service import MotivationService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = MotivationService(session, bus)
            await svc.on_task_completed({
                "task_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "completed_at": "2024-01-10T10:00:00",
                "priority": "low",
            })

        resp = await authed_client.get(SUMMARY_URL)
        assert resp.json()["xp_total"] == 5

    # xp_to_next_level вычисляется корректно после начисления
    async def test_xp_to_next_level_reflects_current_xp(
        self, authed_client: AsyncClient, test_user, seed_catalog
    ):
        from app.core.events.bus import bus
        from app.modules.motivation.service import MotivationService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = MotivationService(session, bus)
            await svc.award_xp(test_user.id, amount=95, reason="setup")

        resp = await authed_client.get(SUMMARY_URL)
        assert resp.json()["xp_to_next_level"] == 5

    # recent_achievements содержит последние 5 (не больше)
    async def test_recent_achievements_max_5(
        self, authed_client: AsyncClient, test_user, seed_catalog
    ):
        from app.core.events.bus import bus
        from app.modules.motivation.service import MotivationService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = MotivationService(session, bus)
            # Разблокируем streak_7 и streak_30 — больше нет в каталоге MVP
            await svc.unlock_achievement(test_user.id, "streak_7")
            await svc.unlock_achievement(test_user.id, "streak_30")

        resp = await authed_client.get(SUMMARY_URL)
        body = resp.json()
        assert len(body["recent_achievements"]) <= 5


# ---------------------------------------------------------------------------
# AC#2 — level_up отражается в summary
# ---------------------------------------------------------------------------

class TestLevelUpViaApi:
    async def test_level_updates_after_xp_threshold(
        self, authed_client: AsyncClient, test_user, seed_catalog
    ):
        from app.core.events.bus import bus
        from app.modules.motivation.service import MotivationService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = MotivationService(session, bus)
            await svc.award_xp(test_user.id, amount=95, reason="setup")
            await svc.on_habit_completed({
                "habit_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "date": "2024-01-10",
                "current_streak": 1,
            })

        resp = await authed_client.get(SUMMARY_URL)
        body = resp.json()
        assert body["xp_total"] == 105
        assert body["level"] == 2
        assert body["xp_to_next_level"] == 95  # 200 - 105


# ---------------------------------------------------------------------------
# GET /api/motivation/achievements — список с флагом unlocked
# ---------------------------------------------------------------------------

class TestAchievementsEndpoint:
    async def test_returns_200(self, authed_client: AsyncClient, seed_catalog):
        resp = await authed_client.get(ACHIEVEMENTS_URL)
        assert resp.status_code == 200

    async def test_returns_list(self, authed_client: AsyncClient, seed_catalog):
        resp = await authed_client.get(ACHIEVEMENTS_URL)
        assert isinstance(resp.json(), list)

    async def test_all_catalog_achievements_present(self, authed_client: AsyncClient, seed_catalog):
        from app.modules.motivation.catalog import ACHIEVEMENTS

        resp = await authed_client.get(ACHIEVEMENTS_URL)
        returned_codes = {a["code"] for a in resp.json()}
        catalog_codes = {a["code"] for a in ACHIEVEMENTS}
        assert catalog_codes == returned_codes

    async def test_unlocked_false_by_default(self, authed_client: AsyncClient, seed_catalog):
        resp = await authed_client.get(ACHIEVEMENTS_URL)
        for ach in resp.json():
            assert ach["unlocked"] is False
            assert ach["unlocked_at"] is None

    # AC#3: streak=7 → unlocked=True
    async def test_achievement_marked_unlocked_after_streak_7(
        self, authed_client: AsyncClient, test_user, seed_catalog
    ):
        from app.core.events.bus import bus
        from app.modules.motivation.service import MotivationService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = MotivationService(session, bus)
            await svc.on_habit_completed({
                "habit_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "date": "2024-01-10",
                "current_streak": 7,
            })

        resp = await authed_client.get(ACHIEVEMENTS_URL)
        streak_7 = next(a for a in resp.json() if a["code"] == "streak_7")
        assert streak_7["unlocked"] is True
        assert streak_7["unlocked_at"] is not None

    # AC#4: повторный streak=7 → всё ещё одна запись, unlocked_at не обнуляется
    async def test_duplicate_streak_7_single_record(
        self, authed_client: AsyncClient, test_user, seed_catalog
    ):
        from app.core.events.bus import bus
        from app.modules.motivation.service import MotivationService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = MotivationService(session, bus)
            await svc.on_habit_completed({
                "habit_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "date": "2024-01-10",
                "current_streak": 7,
            })
            await svc.on_habit_completed({
                "habit_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "date": "2024-01-11",
                "current_streak": 7,
            })

        resp = await authed_client.get(ACHIEVEMENTS_URL)
        streak_7_entries = [a for a in resp.json() if a["code"] == "streak_7"]
        assert len(streak_7_entries) == 1
        assert streak_7_entries[0]["unlocked"] is True


# ---------------------------------------------------------------------------
# AC#6 — finance.budget_exceeded → XP не начисляется
# ---------------------------------------------------------------------------

class TestBudgetExceededViaApi:
    async def test_budget_exceeded_no_xp(
        self, authed_client: AsyncClient, test_user, seed_catalog
    ):
        from app.core.events.bus import bus
        from app.modules.motivation.service import MotivationService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = MotivationService(session, bus)
            await svc.on_budget_exceeded({
                "user_id": str(test_user.id),
                "category": "food",
                "amount": 5000,
            })

        resp = await authed_client.get(SUMMARY_URL)
        assert resp.json()["xp_total"] == 0
