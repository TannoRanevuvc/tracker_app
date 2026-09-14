"""
Интеграционные тесты API habits-модуля.
httpx.AsyncClient + тестовая Postgres-схема через фикстуры conftest.py.

Покрытие критериев приёмки из specs/habits.md §7:
  AC#1 — TestCreateHabit
  AC#2 — TestCreateCheckin
  AC#3 — TestCreateCheckin (дубликат → 409)
  AC#4 — TestStreakCalculation
  AC#5 — TestStreakBroken
  AC#6 — TestUnscheduledCheckin
  AC#7 — TestArchive
  AC#8 — TestOwnershipIsolation
  AC#9 — TestDeleteCheckin
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

HABITS_URL = "/api/habits"


def habit_url(habit_id) -> str:
    return f"{HABITS_URL}/{habit_id}"


def checkins_url(habit_id) -> str:
    return f"{HABITS_URL}/{habit_id}/checkins"


def checkin_url(habit_id, d: str) -> str:
    return f"{HABITS_URL}/{habit_id}/checkins/{d}"


# ---------------------------------------------------------------------------
# AC#1 — Создание привычки
# ---------------------------------------------------------------------------

class TestCreateHabit:
    async def test_create_daily_returns_201(self, authed_client: AsyncClient):
        resp = await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})
        assert resp.status_code == 201

    async def test_create_returns_habit_with_name(self, authed_client: AsyncClient):
        resp = await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})
        assert resp.json()["name"] == "Бег"

    async def test_create_returns_current_streak_zero(self, authed_client: AsyncClient):
        resp = await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})
        assert resp.json()["current_streak"] == 0

    async def test_create_weekly_returns_201(self, authed_client: AsyncClient):
        resp = await authed_client.post(
            HABITS_URL,
            json={"name": "Зарядка", "frequency_type": "weekly_days", "weekly_days": [0, 2, 4]},
        )
        assert resp.status_code == 201

    async def test_create_weekly_without_days_returns_422(self, authed_client: AsyncClient):
        resp = await authed_client.post(
            HABITS_URL,
            json={"name": "Зарядка", "frequency_type": "weekly_days"},
        )
        assert resp.status_code == 422

    async def test_create_without_auth_returns_401(self, client: AsyncClient):
        resp = await client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# AC#2 — Создание чекина (запланированный день)
# ---------------------------------------------------------------------------

class TestCreateCheckin:
    async def test_checkin_today_returns_201(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        resp = await authed_client.post(checkins_url(habit["id"]))
        assert resp.status_code == 201

    async def test_checkin_returns_date(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        resp = await authed_client.post(checkins_url(habit["id"]))
        assert resp.json()["date"] == str(date.today())

    # AC#2: событие habit.completed публикуется при чекине в запланированный день
    async def test_checkin_scheduled_publishes_completed_event(
        self, authed_client: AsyncClient, captured_events
    ):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        await authed_client.post(checkins_url(habit["id"]))
        assert len(captured_events["habit.completed"]) == 1

    async def test_checkin_completed_event_current_streak_one(
        self, authed_client: AsyncClient, captured_events
    ):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        await authed_client.post(checkins_url(habit["id"]))
        assert captured_events["habit.completed"][0]["current_streak"] == 1

    # AC#3: повторный чекин на ту же дату → 409
    async def test_duplicate_checkin_returns_409(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        await authed_client.post(checkins_url(habit["id"]))
        resp = await authed_client.post(checkins_url(habit["id"]))
        assert resp.status_code == 409

    async def test_duplicate_checkin_not_persisted(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        today_str = str(date.today())
        await authed_client.post(checkins_url(habit["id"]), json={"date": today_str})
        await authed_client.post(checkins_url(habit["id"]), json={"date": today_str})
        resp = await authed_client.get(f"{checkins_url(habit['id'])}?from={today_str}&to={today_str}")
        assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# AC#4 — Стрик не прерван, если сегодня ещё нет чекина
# ---------------------------------------------------------------------------

class TestStreakCalculation:
    async def test_streak_intact_when_today_not_checked(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        today = date.today()
        for delta in (3, 2, 1):  # 3 дня назад, 2 дня назад, вчера
            d = today - timedelta(days=delta)
            await authed_client.post(checkins_url(habit["id"]), json={"date": str(d)})

        resp = await authed_client.get(HABITS_URL)
        habits = resp.json()
        found = next(h for h in habits if h["id"] == habit["id"])
        assert found["current_streak"] == 3

    async def test_done_today_false_when_no_checkin_today(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        resp = await authed_client.get(HABITS_URL)
        habits = resp.json()
        found = next(h for h in habits if h["id"] == habit["id"])
        assert found["done_today"] is False

    async def test_done_today_true_after_checkin(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        await authed_client.post(checkins_url(habit["id"]))
        resp = await authed_client.get(HABITS_URL)
        habits = resp.json()
        found = next(h for h in habits if h["id"] == habit["id"])
        assert found["done_today"] is True


# ---------------------------------------------------------------------------
# AC#5 — Прерванный стрик + событие streak_broken
# ---------------------------------------------------------------------------

class TestStreakBroken:
    async def test_streak_zero_when_yesterday_missed(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        day_before_yesterday = date.today() - timedelta(days=2)
        await authed_client.post(checkins_url(habit["id"]), json={"date": str(day_before_yesterday)})

        resp = await authed_client.get(HABITS_URL)
        found = next(h for h in resp.json() if h["id"] == habit["id"])
        assert found["current_streak"] == 0

    async def test_streak_broken_event_published_on_get(
        self, authed_client: AsyncClient, captured_events
    ):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        day_before_yesterday = date.today() - timedelta(days=2)
        await authed_client.post(checkins_url(habit["id"]), json={"date": str(day_before_yesterday)})

        await authed_client.get(HABITS_URL)

        assert len(captured_events["habit.streak_broken"]) == 1

    async def test_streak_broken_event_previous_streak_value(
        self, authed_client: AsyncClient, captured_events
    ):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        day_before_yesterday = date.today() - timedelta(days=2)
        await authed_client.post(checkins_url(habit["id"]), json={"date": str(day_before_yesterday)})

        await authed_client.get(HABITS_URL)

        assert captured_events["habit.streak_broken"][0]["previous_streak"] == 1

    async def test_streak_broken_not_duplicated_same_day(
        self, authed_client: AsyncClient, captured_events
    ):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        day_before_yesterday = date.today() - timedelta(days=2)
        await authed_client.post(checkins_url(habit["id"]), json={"date": str(day_before_yesterday)})

        await authed_client.get(HABITS_URL)
        await authed_client.get(HABITS_URL)  # второй GET в тот же день

        assert len(captured_events["habit.streak_broken"]) == 1


# ---------------------------------------------------------------------------
# AC#6 — Чекин в незапланированный день
# ---------------------------------------------------------------------------

class TestUnscheduledCheckin:
    async def test_unscheduled_checkin_created_201(self, authed_client: AsyncClient):
        habit = (await authed_client.post(
            HABITS_URL,
            json={"name": "Зарядка", "frequency_type": "weekly_days", "weekly_days": [0, 2, 4]},
        )).json()
        tuesday = "2024-01-02"  # вторник, не в [0,2,4]
        resp = await authed_client.post(checkins_url(habit["id"]), json={"date": tuesday})
        assert resp.status_code == 201

    async def test_unscheduled_checkin_streak_unchanged(self, authed_client: AsyncClient):
        habit = (await authed_client.post(
            HABITS_URL,
            json={"name": "Зарядка", "frequency_type": "weekly_days", "weekly_days": [0, 2, 4]},
        )).json()
        tuesday = "2024-01-02"
        await authed_client.post(checkins_url(habit["id"]), json={"date": tuesday})

        resp = await authed_client.get(habit_url(habit["id"]))
        assert resp.json()["current_streak"] == 0

    async def test_unscheduled_checkin_no_completed_event(
        self, authed_client: AsyncClient, captured_events
    ):
        habit = (await authed_client.post(
            HABITS_URL,
            json={"name": "Зарядка", "frequency_type": "weekly_days", "weekly_days": [0, 2, 4]},
        )).json()
        tuesday = "2024-01-02"
        await authed_client.post(checkins_url(habit["id"]), json={"date": tuesday})

        assert len(captured_events["habit.completed"]) == 0


# ---------------------------------------------------------------------------
# AC#7 — Архивация
# ---------------------------------------------------------------------------

class TestArchive:
    async def test_archived_habit_not_in_default_list(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        await authed_client.post(f"{habit_url(habit['id'])}/archive")

        resp = await authed_client.get(HABITS_URL)
        ids = [h["id"] for h in resp.json()]
        assert habit["id"] not in ids

    async def test_archived_habit_visible_with_flag(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        await authed_client.post(f"{habit_url(habit['id'])}/archive")

        resp = await authed_client.get(f"{HABITS_URL}?include_archived=true")
        ids = [h["id"] for h in resp.json()]
        assert habit["id"] in ids

    async def test_archive_returns_200_with_habit(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        resp = await authed_client.post(f"{habit_url(habit['id'])}/archive")
        assert resp.status_code == 200
        assert resp.json()["id"] == habit["id"]

    async def test_archived_habit_checkins_preserved(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        await authed_client.post(checkins_url(habit["id"]))
        await authed_client.post(f"{habit_url(habit['id'])}/archive")

        today_str = str(date.today())
        resp = await authed_client.get(f"{checkins_url(habit['id'])}?from={today_str}&to={today_str}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# AC#8 — Изоляция по owner (чужая привычка → 404)
# ---------------------------------------------------------------------------

class TestOwnershipIsolation:
    async def test_foreign_habit_returns_404(self, authed_client: AsyncClient, client: AsyncClient, create_tables):
        from app.core.auth.models import User
        from app.core.auth.service import create_access_token, hash_password
        from tests.conftest import test_session_factory

        # Создаём привычку для test_user (authed_client)
        resp = await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})
        habit_id = resp.json()["id"]

        # Создаём второго пользователя
        other = User(
            id=uuid.uuid4(),
            email="other@example.com",
            password_hash=hash_password("pass"),
        )
        async with test_session_factory() as s:
            s.add(other)
            await s.commit()

        # Делаем запрос от имени второго пользователя
        client.cookies.set("access_token", create_access_token(other.id))
        resp = await client.get(habit_url(habit_id))
        assert resp.status_code == 404

    async def test_foreign_checkin_post_returns_404(self, authed_client: AsyncClient, client: AsyncClient, create_tables):
        from app.core.auth.models import User
        from app.core.auth.service import create_access_token, hash_password
        from tests.conftest import test_session_factory

        resp = await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})
        habit_id = resp.json()["id"]

        other = User(
            id=uuid.uuid4(),
            email="other2@example.com",
            password_hash=hash_password("pass"),
        )
        async with test_session_factory() as s:
            s.add(other)
            await s.commit()

        client.cookies.set("access_token", create_access_token(other.id))
        resp = await client.post(checkins_url(habit_id))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# AC#9 — Удаление чекина
# ---------------------------------------------------------------------------

class TestDeleteCheckin:
    async def test_delete_checkin_returns_204(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        today_str = str(date.today())
        await authed_client.post(checkins_url(habit["id"]), json={"date": today_str})

        resp = await authed_client.delete(checkin_url(habit["id"], today_str))
        assert resp.status_code == 204

    async def test_deleted_checkin_not_in_history(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        today_str = str(date.today())
        await authed_client.post(checkins_url(habit["id"]), json={"date": today_str})
        await authed_client.delete(checkin_url(habit["id"], today_str))

        resp = await authed_client.get(f"{checkins_url(habit['id'])}?from={today_str}&to={today_str}")
        assert resp.json() == []

    async def test_delete_nonexistent_checkin_returns_404(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        resp = await authed_client.delete(checkin_url(habit["id"], "2024-01-01"))
        assert resp.status_code == 404

    async def test_deleted_checkin_resets_streak(self, authed_client: AsyncClient):
        habit = (await authed_client.post(HABITS_URL, json={"name": "Бег", "frequency_type": "daily"})).json()
        today_str = str(date.today())
        await authed_client.post(checkins_url(habit["id"]), json={"date": today_str})
        await authed_client.delete(checkin_url(habit["id"], today_str))

        resp = await authed_client.get(habit_url(habit["id"]))
        assert resp.json()["current_streak"] == 0
