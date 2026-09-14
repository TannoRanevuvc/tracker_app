"""
Контрактные тесты событий модуля habits.

Уровень 1 — статические: PUBLISHES/SUBSCRIBES_TO соответствуют спеке.
Уровень 2 — функциональные: реальная публикация на шину с правильным payload.

Покрытие критериев приёмки:
  AC#2 (habit.completed при запланированном чекине) — TestHabitCompleted
  AC#5 (habit.streak_broken при обнаружении пропуска) — TestHabitStreakBroken
  AC#6 (habit.completed НЕ публикуется для незапланированного дня) — TestHabitCompleted
"""

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio

from app.core.events.bus import EventBus
from app.modules.habits import events as habits_events


# ---------------------------------------------------------------------------
# Статический контракт
# ---------------------------------------------------------------------------

class TestEventContract:
    def test_publishes_habit_completed(self):
        assert "habit.completed" in habits_events.PUBLISHES

    def test_publishes_habit_streak_broken(self):
        assert "habit.streak_broken" in habits_events.PUBLISHES

    def test_no_extra_published_events(self):
        assert set(habits_events.PUBLISHES) == {"habit.completed", "habit.streak_broken"}

    def test_subscribes_to_nothing(self):
        assert len(habits_events.SUBSCRIBES_TO) == 0


# ---------------------------------------------------------------------------
# Функциональный контракт — habit.completed
# ---------------------------------------------------------------------------

class TestHabitCompleted:
    # AC#2: чекин в запланированный день → habit.completed с правильным payload
    async def test_scheduled_checkin_publishes_event(self, db_session, authed_client, test_user, captured_events):
        from app.modules.habits.service import HabitService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("habit.completed", capture)

        svc = HabitService(db_session, test_bus)
        habit = await svc.create_habit(
            user_id=test_user.id,
            name="Бег",
            frequency_type="daily",
            weekly_days=None,
        )
        today = date.today()
        await svc.create_checkin(habit_id=habit.id, user_id=test_user.id, checkin_date=today)

        assert len(received) == 1
        payload = received[0]
        assert payload["habit_id"] == str(habit.id)
        assert payload["user_id"] == str(test_user.id)
        assert payload["date"] == str(today)
        assert payload["current_streak"] == 1

    # AC#6: чекин в незапланированный день → habit.completed НЕ публикуется
    async def test_unscheduled_checkin_does_not_publish_event(self, db_session, test_user):
        from app.modules.habits.service import HabitService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("habit.completed", capture)

        svc = HabitService(db_session, test_bus)
        habit = await svc.create_habit(
            user_id=test_user.id,
            name="Тест weekly",
            frequency_type="weekly_days",
            weekly_days=[0, 2, 4],  # пн/ср/пт
        )
        tuesday = date(2024, 1, 2)  # вторник — не в расписании
        await svc.create_checkin(habit_id=habit.id, user_id=test_user.id, checkin_date=tuesday)

        assert len(received) == 0

    # payload содержит обновлённый current_streak, а не нулевой
    async def test_event_payload_current_streak_reflects_total(self, db_session, test_user):
        from app.modules.habits.service import HabitService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("habit.completed", capture)

        svc = HabitService(db_session, test_bus)
        habit = await svc.create_habit(
            user_id=test_user.id,
            name="Ежедневная",
            frequency_type="daily",
            weekly_days=None,
        )
        today = date.today()
        yesterday = today - timedelta(days=1)

        # добавляем вчерашний чекин напрямую, затем сегодняшний через сервис
        await svc.create_checkin(habit_id=habit.id, user_id=test_user.id, checkin_date=yesterday)
        received.clear()  # сбрасываем предыдущее событие
        await svc.create_checkin(habit_id=habit.id, user_id=test_user.id, checkin_date=today)

        assert len(received) == 1
        assert received[0]["current_streak"] == 2


# ---------------------------------------------------------------------------
# Функциональный контракт — habit.streak_broken
# ---------------------------------------------------------------------------

class TestHabitStreakBroken:
    # AC#5: при GET с прерванным стриком → habit.streak_broken публикуется
    async def test_streak_broken_published_on_detection(self, db_session, test_user):
        from app.modules.habits.service import HabitService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("habit.streak_broken", capture)

        svc = HabitService(db_session, test_bus)
        habit = await svc.create_habit(
            user_id=test_user.id,
            name="Ежедневная",
            frequency_type="daily",
            weekly_days=None,
        )
        today = date.today()
        day_before_yesterday = today - timedelta(days=2)

        # был чекин позавчера, вчера пропущено
        await svc.create_checkin(habit_id=habit.id, user_id=test_user.id, checkin_date=day_before_yesterday)

        await svc.list_habits(user_id=test_user.id)

        assert len(received) == 1
        payload = received[0]
        assert payload["habit_id"] == str(habit.id)
        assert payload["user_id"] == str(test_user.id)
        assert payload["previous_streak"] == 1

    # AC#5 дедупликация: повторный GET в тот же день не публикует событие повторно
    async def test_streak_broken_deduplicated_within_same_day(self, db_session, test_user):
        from app.modules.habits.service import HabitService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("habit.streak_broken", capture)

        svc = HabitService(db_session, test_bus)
        habit = await svc.create_habit(
            user_id=test_user.id,
            name="Ежедневная",
            frequency_type="daily",
            weekly_days=None,
        )
        today = date.today()
        day_before_yesterday = today - timedelta(days=2)
        await svc.create_checkin(habit_id=habit.id, user_id=test_user.id, checkin_date=day_before_yesterday)

        await svc.list_habits(user_id=test_user.id)
        await svc.list_habits(user_id=test_user.id)  # второй вызов в тот же день

        assert len(received) == 1  # событие опубликовано ровно один раз

    # payload содержит предыдущий стрик до прерывания
    async def test_streak_broken_payload_previous_streak(self, db_session, test_user):
        from app.modules.habits.service import HabitService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("habit.streak_broken", capture)

        svc = HabitService(db_session, test_bus)
        habit = await svc.create_habit(
            user_id=test_user.id,
            name="Ежедневная",
            frequency_type="daily",
            weekly_days=None,
        )
        today = date.today()
        # три дня подряд, потом пропуск вчера
        checkin_days = [today - timedelta(days=d) for d in range(4, 1, -1)]  # -4, -3, -2
        for d in checkin_days:
            await svc.create_checkin(habit_id=habit.id, user_id=test_user.id, checkin_date=d)

        await svc.list_habits(user_id=test_user.id)

        assert received[0]["previous_streak"] == 3
