"""
Контрактные тесты событий модуля motivation.

Уровень 1 — статические: PUBLISHES/SUBSCRIBES_TO соответствуют спеке.
Уровень 2 — функциональные: реальная обработка входящих событий через MotivationService.

Покрытие критериев приёмки:
  AC#1 (habit.completed → +10 XP, публикуется motivation.xp_awarded) — TestHabitCompletedHandler
  AC#2 (xp_total=95 + событие → level_up публикуется) — TestLevelUp
  AC#3 (streak=7 → achievement_unlocked) — TestAchievementUnlock
  AC#4 (streak_7 уже есть → дубликат не создаётся) — TestAchievementUnlock
  AC#5 (task high→10 XP, low→5 XP) — TestTaskCompletedHandler
  AC#6 (finance.budget_exceeded → XP не меняется) — TestBudgetExceededHandler
  AC#7 (исключение в обработчике не пробрасывается наружу) — TestHandlerIsolation
"""

import uuid

import pytest

from app.core.events.bus import EventBus
from app.modules.motivation import events as motivation_events


# ---------------------------------------------------------------------------
# Статический контракт
# ---------------------------------------------------------------------------

class TestEventContract:
    # PUBLISHES
    def test_publishes_xp_awarded(self):
        assert "motivation.xp_awarded" in motivation_events.PUBLISHES

    def test_publishes_level_up(self):
        assert "motivation.level_up" in motivation_events.PUBLISHES

    def test_publishes_achievement_unlocked(self):
        assert "motivation.achievement_unlocked" in motivation_events.PUBLISHES

    def test_no_extra_published_events(self):
        assert set(motivation_events.PUBLISHES) == {
            "motivation.xp_awarded",
            "motivation.level_up",
            "motivation.achievement_unlocked",
        }

    # SUBSCRIBES_TO
    def test_subscribes_to_habit_completed(self):
        assert "habit.completed" in motivation_events.SUBSCRIBES_TO

    def test_subscribes_to_habit_streak_broken(self):
        assert "habit.streak_broken" in motivation_events.SUBSCRIBES_TO

    def test_subscribes_to_task_completed(self):
        assert "task.completed" in motivation_events.SUBSCRIBES_TO

    def test_subscribes_to_food_daily_goal_reached(self):
        assert "food.daily_goal_reached" in motivation_events.SUBSCRIBES_TO

    def test_subscribes_to_finance_budget_exceeded(self):
        assert "finance.budget_exceeded" in motivation_events.SUBSCRIBES_TO

    def test_no_extra_subscriptions(self):
        assert set(motivation_events.SUBSCRIBES_TO.keys()) == {
            "habit.completed",
            "habit.streak_broken",
            "task.completed",
            "food.daily_goal_reached",
            "finance.budget_exceeded",
        }


# ---------------------------------------------------------------------------
# AC#1 — habit.completed → +10 XP, публикует motivation.xp_awarded
# ---------------------------------------------------------------------------

class TestHabitCompletedHandler:
    async def test_awards_10_xp(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        svc = MotivationService(db_session, bus)

        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 1,
        })

        progress = await svc.get_or_create_progress(test_user.id)
        assert progress.xp_total == 10

    async def test_publishes_xp_awarded_event(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        received = []

        async def _h(p): received.append(p)
        bus.subscribe("motivation.xp_awarded", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 1,
        })

        assert len(received) == 1
        payload = received[0]
        assert str(payload["user_id"]) == str(test_user.id)
        assert payload["amount"] == 10
        assert payload["reason"] == "habit_completed"

    async def test_xp_accumulates_across_calls(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        svc = MotivationService(db_session, bus)

        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 1,
        })
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-11",
            "current_streak": 2,
        })

        progress = await svc.get_or_create_progress(test_user.id)
        assert progress.xp_total == 20


# ---------------------------------------------------------------------------
# AC#2 — xp_total пересекает порог уровня → level_up публикуется
# ---------------------------------------------------------------------------

class TestLevelUp:
    async def test_level_up_published_when_crossing_threshold(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        level_up_events = []

        async def _h(p): level_up_events.append(p)
        bus.subscribe("motivation.level_up", _h)

        svc = MotivationService(db_session, bus)

        await svc.award_xp(test_user.id, amount=95, reason="setup")
        level_up_events.clear()

        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 1,
        })

        assert len(level_up_events) == 1
        payload = level_up_events[0]
        assert str(payload["user_id"]) == str(test_user.id)
        assert payload["new_level"] == 2

    async def test_level_stored_correctly_after_level_up(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        svc = MotivationService(db_session, bus)

        await svc.award_xp(test_user.id, amount=95, reason="setup")
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 1,
        })

        progress = await svc.get_or_create_progress(test_user.id)
        assert progress.xp_total == 105
        assert progress.level == 2

    async def test_no_level_up_when_not_crossing_threshold(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        level_up_events = []

        async def _h(p): level_up_events.append(p)
        bus.subscribe("motivation.level_up", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 1,
        })

        assert len(level_up_events) == 0


# ---------------------------------------------------------------------------
# AC#3, AC#4 — разблокировка ачивки по стрику
# ---------------------------------------------------------------------------

class TestAchievementUnlock:
    # AC#3: streak=7 → создаётся user_achievement(streak_7), публикуется event
    async def test_streak_7_unlocks_achievement(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        achievement_events = []

        async def _h(p): achievement_events.append(p)
        bus.subscribe("motivation.achievement_unlocked", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 7,
        })

        assert len(achievement_events) == 1
        payload = achievement_events[0]
        assert str(payload["user_id"]) == str(test_user.id)
        assert payload["achievement_code"] == "streak_7"

    async def test_streak_7_creates_user_achievement_record(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        svc = MotivationService(db_session, bus)
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 7,
        })

        achievements = await svc.get_user_achievements(test_user.id)
        codes = [a.achievement_code for a in achievements]
        assert "streak_7" in codes

    # AC#4: streak_7 уже есть → вторая запись не создаётся, событие не публикуется повторно
    async def test_duplicate_streak_7_no_second_record(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        achievement_events = []

        async def _h(p): achievement_events.append(p)
        bus.subscribe("motivation.achievement_unlocked", _h)

        svc = MotivationService(db_session, bus)

        # Первый раз — разблокировать
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 7,
        })

        # Второй раз — другая привычка, тот же streak=7
        achievement_events.clear()
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-11",
            "current_streak": 7,
        })

        assert len(achievement_events) == 0

        achievements = await svc.get_user_achievements(test_user.id)
        streak_7_records = [a for a in achievements if a.achievement_code == "streak_7"]
        assert len(streak_7_records) == 1

    # streak=30 и streak=100 тоже разблокируют свои ачивки
    async def test_streak_30_unlocks_streak_30(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        achievement_events = []

        async def _h(p): achievement_events.append(p)
        bus.subscribe("motivation.achievement_unlocked", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 30,
        })

        codes = [e["achievement_code"] for e in achievement_events]
        assert "streak_30" in codes

    # streak=7 при первом вызове → сразу streak_7, НО не streak_30 или streak_100
    async def test_streak_7_does_not_unlock_higher_achievements(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        achievement_events = []

        async def _h(p): achievement_events.append(p)
        bus.subscribe("motivation.achievement_unlocked", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 7,
        })

        codes = [e["achievement_code"] for e in achievement_events]
        assert "streak_30" not in codes
        assert "streak_100" not in codes

    # streak не на пороге → ачивка не выдаётся
    async def test_non_threshold_streak_no_achievement(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        achievement_events = []

        async def _h(p): achievement_events.append(p)
        bus.subscribe("motivation.achievement_unlocked", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": "2024-01-10",
            "current_streak": 5,
        })

        assert len(achievement_events) == 0


# ---------------------------------------------------------------------------
# AC#5 — task.completed: XP зависит от приоритета
# ---------------------------------------------------------------------------

class TestTaskCompletedHandler:
    # AC#5: high priority → 10 XP
    async def test_high_priority_awards_10_xp(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        xp_events = []

        async def _h(p): xp_events.append(p)
        bus.subscribe("motivation.xp_awarded", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_task_completed({
            "task_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "completed_at": "2024-01-10T10:00:00",
            "priority": "high",
        })

        assert len(xp_events) == 1
        assert xp_events[0]["amount"] == 10
        assert xp_events[0]["reason"] == "task_completed_high"

    # AC#5: low priority → 5 XP
    async def test_low_priority_awards_5_xp(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        xp_events = []

        async def _h(p): xp_events.append(p)
        bus.subscribe("motivation.xp_awarded", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_task_completed({
            "task_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "completed_at": "2024-01-10T10:00:00",
            "priority": "low",
        })

        assert len(xp_events) == 1
        assert xp_events[0]["amount"] == 5
        assert xp_events[0]["reason"] == "task_completed_low"

    # AC#5: medium priority → 5 XP (как low)
    async def test_medium_priority_awards_5_xp(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        xp_events = []

        async def _h(p): xp_events.append(p)
        bus.subscribe("motivation.xp_awarded", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_task_completed({
            "task_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "completed_at": "2024-01-10T10:00:00",
            "priority": "medium",
        })

        assert len(xp_events) == 1
        assert xp_events[0]["amount"] == 5

    async def test_task_high_xp_stored_in_db(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        svc = MotivationService(db_session, bus)
        await svc.on_task_completed({
            "task_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "completed_at": "2024-01-10T10:00:00",
            "priority": "high",
        })

        progress = await svc.get_or_create_progress(test_user.id)
        assert progress.xp_total == 10


# ---------------------------------------------------------------------------
# AC#6 — finance.budget_exceeded → no-op
# ---------------------------------------------------------------------------

class TestBudgetExceededHandler:
    async def test_budget_exceeded_does_not_change_xp(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        xp_events = []

        async def _h(p): xp_events.append(p)
        bus.subscribe("motivation.xp_awarded", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_budget_exceeded({
            "user_id": str(test_user.id),
            "category": "food",
            "amount": 5000,
        })

        assert len(xp_events) == 0

    async def test_budget_exceeded_xp_remains_zero(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        svc = MotivationService(db_session, bus)
        await svc.on_budget_exceeded({
            "user_id": str(test_user.id),
            "category": "food",
            "amount": 5000,
        })

        progress = await svc.get_or_create_progress(test_user.id)
        assert progress.xp_total == 0


# ---------------------------------------------------------------------------
# habit.streak_broken — no-op в MVP
# ---------------------------------------------------------------------------

class TestStreakBrokenHandler:
    async def test_streak_broken_does_not_award_xp(self, db_session, test_user, seed_catalog):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        xp_events = []

        async def _h(p): xp_events.append(p)
        bus.subscribe("motivation.xp_awarded", _h)

        svc = MotivationService(db_session, bus)
        await svc.on_streak_broken({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "previous_streak": 5,
        })

        assert len(xp_events) == 0


# ---------------------------------------------------------------------------
# AC#7 — исключение в обработчике не пробрасывается наружу
# ---------------------------------------------------------------------------

class TestHandlerIsolation:
    async def test_exception_in_on_habit_completed_does_not_propagate(
        self, db_session, test_user
    ):
        """AC#7: если внутри on_habit_completed произошло исключение, оно не должно
        подниматься до вызывающего кода (источник события не должен об этом знать)."""
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        svc = MotivationService(db_session, bus)

        async def broken_award(*args, **kwargs):
            raise RuntimeError("simulated DB failure")

        svc.award_xp = broken_award

        try:
            await svc.on_habit_completed({
                "habit_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "date": "2024-01-10",
                "current_streak": 1,
            })
        except Exception as exc:
            pytest.fail(f"on_habit_completed propagated exception: {exc}")

    async def test_exception_in_on_task_completed_does_not_propagate(
        self, db_session, test_user
    ):
        from app.modules.motivation.service import MotivationService

        bus = EventBus()
        svc = MotivationService(db_session, bus)

        async def broken_award(*args, **kwargs):
            raise RuntimeError("simulated DB failure")

        svc.award_xp = broken_award

        try:
            await svc.on_task_completed({
                "task_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "completed_at": "2024-01-10T10:00:00",
                "priority": "high",
            })
        except Exception as exc:
            pytest.fail(f"on_task_completed propagated exception: {exc}")
