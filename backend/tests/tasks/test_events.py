"""
Контрактные тесты событий модуля tasks.

Уровень 1 — статические: PUBLISHES/SUBSCRIBES_TO соответствуют спеке.
Уровень 2 — функциональные: реальная публикация на шину с правильным payload.

Покрытие критериев приёмки:
  AC#2 (task.completed при /complete) — TestTaskCompleted
  AC#4 (task.overdue при list_tasks с просроченной задачей) — TestTaskOverdue
  AC#5 (task.overdue не дублируется в тот же день) — TestTaskOverdue
  AC#6 (habit.completed + активная связка → создаётся задача) — TestHabitCompletedHandler
  AC#7 (habit.completed + disabled → задача не создаётся) — TestHabitCompletedHandler
  AC#8 (habit.completed без связки → ничего, без ошибок) — TestHabitCompletedHandler
"""

import uuid
from datetime import date, timedelta

import pytest

from app.core.events.bus import EventBus
from app.modules.tasks import events as tasks_events


# ---------------------------------------------------------------------------
# Статический контракт
# ---------------------------------------------------------------------------

class TestEventContract:
    def test_publishes_task_completed(self):
        assert "task.completed" in tasks_events.PUBLISHES

    def test_publishes_task_overdue(self):
        assert "task.overdue" in tasks_events.PUBLISHES

    def test_no_extra_published_events(self):
        assert set(tasks_events.PUBLISHES) == {"task.completed", "task.overdue"}

    def test_subscribes_to_habit_completed(self):
        assert "habit.completed" in tasks_events.SUBSCRIBES_TO

    def test_no_extra_subscriptions(self):
        assert set(tasks_events.SUBSCRIBES_TO.keys()) == {"habit.completed"}


# ---------------------------------------------------------------------------
# Функциональный контракт — task.completed
# ---------------------------------------------------------------------------

class TestTaskCompleted:
    # AC#2: complete_task → task.completed с правильным payload
    async def test_complete_publishes_event(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("task.completed", capture)

        svc = TaskService(db_session, test_bus)
        task = await svc.create_task(user_id=test_user.id, title="Купить билеты")
        await svc.complete_task(task_id=task.id, user_id=test_user.id)

        assert len(received) == 1
        payload = received[0]
        assert str(payload["task_id"]) == str(task.id)
        assert str(payload["user_id"]) == str(test_user.id)
        assert "completed_at" in payload
        assert "priority" in payload

    # Создание задачи не публикует task.completed
    async def test_create_does_not_publish_completed(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("task.completed", capture)

        svc = TaskService(db_session, test_bus)
        await svc.create_task(user_id=test_user.id, title="Просто задача")

        assert len(received) == 0


# ---------------------------------------------------------------------------
# Функциональный контракт — task.overdue
# ---------------------------------------------------------------------------

class TestTaskOverdue:
    # AC#4: list_tasks с просроченной → task.overdue публикуется
    async def test_overdue_task_publishes_event_on_list(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("task.overdue", capture)

        yesterday = date.today() - timedelta(days=1)
        svc = TaskService(db_session, test_bus)
        task = await svc.create_task(
            user_id=test_user.id,
            title="Просроченная",
            due_date=yesterday,
        )
        await svc.list_tasks(user_id=test_user.id)

        assert len(received) == 1
        payload = received[0]
        assert str(payload["task_id"]) == str(task.id)
        assert str(payload["user_id"]) == str(test_user.id)
        assert "due_date" in payload

    # AC#5: повторный list в тот же день → task.overdue не публикуется снова
    async def test_overdue_event_deduplicated_same_day(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("task.overdue", capture)

        yesterday = date.today() - timedelta(days=1)
        svc = TaskService(db_session, test_bus)
        await svc.create_task(
            user_id=test_user.id,
            title="Просроченная",
            due_date=yesterday,
        )

        await svc.list_tasks(user_id=test_user.id)
        await svc.list_tasks(user_id=test_user.id)  # второй вызов в тот же день

        assert len(received) == 1

    # Задача без дедлайна — не публикует task.overdue
    async def test_no_due_date_no_overdue_event(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("task.overdue", capture)

        svc = TaskService(db_session, test_bus)
        await svc.create_task(user_id=test_user.id, title="Без дедлайна")
        await svc.list_tasks(user_id=test_user.id)

        assert len(received) == 0

    # Done-задача с прошедшим дедлайном — не публикует task.overdue
    async def test_done_task_with_past_due_date_no_overdue(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("task.overdue", capture)

        yesterday = date.today() - timedelta(days=1)
        svc = TaskService(db_session, test_bus)
        task = await svc.create_task(
            user_id=test_user.id,
            title="Завершённая",
            due_date=yesterday,
        )
        await svc.complete_task(task_id=task.id, user_id=test_user.id)
        await svc.list_tasks(user_id=test_user.id)

        assert len(received) == 0


# ---------------------------------------------------------------------------
# Функциональный контракт — обработчик habit.completed
# ---------------------------------------------------------------------------

class TestHabitCompletedHandler:
    # AC#6: активная связка → задача создаётся с title из шаблона
    async def test_active_link_creates_task(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        svc = TaskService(db_session, test_bus)
        habit_id = uuid.uuid4()

        await svc.create_habit_link(
            user_id=test_user.id,
            habit_id=habit_id,
            task_title_template="Внести вес",
        )

        await svc.on_habit_completed({
            "habit_id": str(habit_id),
            "user_id": str(test_user.id),
            "date": str(date.today()),
            "current_streak": 1,
        })

        tasks = await svc.list_tasks(user_id=test_user.id)
        assert any(t.title == "Внести вес" for t in tasks)

    # AC#6: автосозданная задача — status=todo, priority=medium, due_date=None
    async def test_auto_created_task_defaults(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        svc = TaskService(db_session, test_bus)
        habit_id = uuid.uuid4()

        await svc.create_habit_link(
            user_id=test_user.id,
            habit_id=habit_id,
            task_title_template="Внести вес",
        )

        await svc.on_habit_completed({
            "habit_id": str(habit_id),
            "user_id": str(test_user.id),
            "date": str(date.today()),
            "current_streak": 1,
        })

        tasks = await svc.list_tasks(user_id=test_user.id)
        created = next(t for t in tasks if t.title == "Внести вес")
        assert created.status == "todo"
        assert created.priority == "medium"
        assert created.due_date is None

    # AC#7: связка с enabled=false → задача не создаётся
    async def test_disabled_link_does_not_create_task(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        svc = TaskService(db_session, test_bus)
        habit_id = uuid.uuid4()

        link = await svc.create_habit_link(
            user_id=test_user.id,
            habit_id=habit_id,
            task_title_template="Внести вес",
        )
        await svc.update_habit_link(
            user_id=test_user.id,
            link_id=link.id,
            enabled=False,
        )

        await svc.on_habit_completed({
            "habit_id": str(habit_id),
            "user_id": str(test_user.id),
            "date": str(date.today()),
            "current_streak": 1,
        })

        tasks = await svc.list_tasks(user_id=test_user.id)
        assert not any(t.title == "Внести вес" for t in tasks)

    # AC#8: нет связки для этой привычки → ничего, без ошибок
    async def test_no_link_does_nothing(self, db_session, test_user):
        from app.modules.tasks.service import TaskService

        test_bus = EventBus()
        svc = TaskService(db_session, test_bus)

        await svc.on_habit_completed({
            "habit_id": str(uuid.uuid4()),
            "user_id": str(test_user.id),
            "date": str(date.today()),
            "current_streak": 1,
        })

        tasks = await svc.list_tasks(user_id=test_user.id)
        assert len(tasks) == 0
