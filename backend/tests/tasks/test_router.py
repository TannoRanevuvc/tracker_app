"""
Интеграционные тесты API tasks-модуля.
httpx.AsyncClient + тестовая Postgres-схема через фикстуры conftest.py.

Покрытие критериев приёмки из specs/tasks.md §7:
  AC#1 — TestCreateTask
  AC#2 — TestCompleteTask
  AC#3 — TestCompleteTask (уже завершена → 409)
  AC#4 — TestOverdueTask
  AC#5 — TestOverdueTask (дедупликация)
  AC#6 — TestHabitLinks (активная связка создаёт задачу)
  AC#7 — TestHabitLinks (disabled → задача не создаётся)
  AC#8 — TestHabitLinks (нет связки → без ошибок)
  AC#9 — TestOwnershipIsolation
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

TASKS_URL = "/api/tasks"
LINKS_URL = "/api/tasks/habit-links"


def task_url(task_id) -> str:
    return f"{TASKS_URL}/{task_id}"


def complete_url(task_id) -> str:
    return f"{TASKS_URL}/{task_id}/complete"


def reopen_url(task_id) -> str:
    return f"{TASKS_URL}/{task_id}/reopen"


def link_url(link_id) -> str:
    return f"{LINKS_URL}/{link_id}"


# ---------------------------------------------------------------------------
# AC#1 — Создание задачи
# ---------------------------------------------------------------------------

class TestCreateTask:
    # AC#1: POST с title → 201, status=todo, priority=medium
    async def test_create_returns_201(self, authed_client: AsyncClient):
        resp = await authed_client.post(TASKS_URL, json={"title": "Купить билеты"})
        assert resp.status_code == 201

    async def test_create_default_status_todo(self, authed_client: AsyncClient):
        resp = await authed_client.post(TASKS_URL, json={"title": "Купить билеты"})
        assert resp.json()["status"] == "todo"

    async def test_create_default_priority_medium(self, authed_client: AsyncClient):
        resp = await authed_client.post(TASKS_URL, json={"title": "Купить билеты"})
        assert resp.json()["priority"] == "medium"

    async def test_create_returns_title(self, authed_client: AsyncClient):
        resp = await authed_client.post(TASKS_URL, json={"title": "Купить билеты"})
        assert resp.json()["title"] == "Купить билеты"

    async def test_create_without_auth_returns_401(self, client: AsyncClient):
        resp = await client.post(TASKS_URL, json={"title": "Купить билеты"})
        assert resp.status_code == 401

    async def test_create_without_title_returns_422(self, authed_client: AsyncClient):
        resp = await authed_client.post(TASKS_URL, json={"description": "без заголовка"})
        assert resp.status_code == 422

    async def test_create_with_optional_fields(self, authed_client: AsyncClient):
        tomorrow = str(date.today() + timedelta(days=1))
        resp = await authed_client.post(TASKS_URL, json={
            "title": "Задача с параметрами",
            "description": "подробности",
            "priority": "high",
            "due_date": tomorrow,
            "tag": "работа",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["priority"] == "high"
        assert body["tag"] == "работа"
        assert body["due_date"] == tomorrow


# ---------------------------------------------------------------------------
# AC#2, AC#3 — Завершение задачи
# ---------------------------------------------------------------------------

class TestCompleteTask:
    # AC#2: todo → /complete → status=done, completed_at заполнен
    async def test_complete_todo_returns_200(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        resp = await authed_client.post(complete_url(task["id"]))
        assert resp.status_code == 200

    async def test_complete_sets_status_done(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        resp = await authed_client.post(complete_url(task["id"]))
        assert resp.json()["status"] == "done"

    async def test_complete_sets_completed_at(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        resp = await authed_client.post(complete_url(task["id"]))
        assert resp.json()["completed_at"] is not None

    # AC#2: task.completed публикуется
    async def test_complete_publishes_event(
        self, authed_client: AsyncClient, captured_events
    ):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        await authed_client.post(complete_url(task["id"]))
        assert len(captured_events["task.completed"]) == 1

    async def test_completed_event_payload(
        self, authed_client: AsyncClient, captured_events
    ):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        await authed_client.post(complete_url(task["id"]))
        payload = captured_events["task.completed"][0]
        assert str(payload["task_id"]) == str(task["id"])
        assert "completed_at" in payload
        assert "priority" in payload

    # AC#3: уже done → /complete → 409
    async def test_complete_already_done_returns_409(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        await authed_client.post(complete_url(task["id"]))
        resp = await authed_client.post(complete_url(task["id"]))
        assert resp.status_code == 409

    # AC#3: повторное /complete не публикует второй event
    async def test_complete_duplicate_no_second_event(
        self, authed_client: AsyncClient, captured_events
    ):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        await authed_client.post(complete_url(task["id"]))
        await authed_client.post(complete_url(task["id"]))  # 409, событие не должно уходить
        assert len(captured_events["task.completed"]) == 1


# ---------------------------------------------------------------------------
# Переоткрытие задачи (reopen)
# ---------------------------------------------------------------------------

class TestReopenTask:
    async def test_reopen_done_task_returns_200(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        await authed_client.post(complete_url(task["id"]))
        resp = await authed_client.post(reopen_url(task["id"]))
        assert resp.status_code == 200

    async def test_reopen_sets_status_todo(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        await authed_client.post(complete_url(task["id"]))
        resp = await authed_client.post(reopen_url(task["id"]))
        assert resp.json()["status"] == "todo"

    async def test_reopen_clears_completed_at(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        await authed_client.post(complete_url(task["id"]))
        resp = await authed_client.post(reopen_url(task["id"]))
        assert resp.json()["completed_at"] is None

    # reopen задачи, которая не done → 409
    async def test_reopen_not_done_returns_409(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        resp = await authed_client.post(reopen_url(task["id"]))
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# AC#4, AC#5 — Просроченные задачи
# ---------------------------------------------------------------------------

class TestOverdueTask:
    # AC#4: задача с due_date вчера → GET возвращает is_overdue=true
    async def test_overdue_task_is_overdue_true(self, authed_client: AsyncClient):
        yesterday = str(date.today() - timedelta(days=1))
        await authed_client.post(TASKS_URL, json={"title": "Просрочена", "due_date": yesterday})

        resp = await authed_client.get(TASKS_URL)
        task = resp.json()[0]
        assert task["is_overdue"] is True

    # AC#4: task.overdue публикуется при GET
    async def test_overdue_task_publishes_event_on_get(
        self, authed_client: AsyncClient, captured_events
    ):
        yesterday = str(date.today() - timedelta(days=1))
        await authed_client.post(TASKS_URL, json={"title": "Просрочена", "due_date": yesterday})

        await authed_client.get(TASKS_URL)

        assert len(captured_events["task.overdue"]) == 1

    async def test_overdue_event_payload_contains_due_date(
        self, authed_client: AsyncClient, captured_events
    ):
        yesterday = str(date.today() - timedelta(days=1))
        task = (await authed_client.post(
            TASKS_URL, json={"title": "Просрочена", "due_date": yesterday}
        )).json()

        await authed_client.get(TASKS_URL)

        payload = captured_events["task.overdue"][0]
        assert str(payload["task_id"]) == str(task["id"])
        assert "due_date" in payload

    # AC#5: повторный GET в тот же день → task.overdue не публикуется снова
    async def test_overdue_event_not_duplicated_same_day(
        self, authed_client: AsyncClient, captured_events
    ):
        yesterday = str(date.today() - timedelta(days=1))
        await authed_client.post(TASKS_URL, json={"title": "Просрочена", "due_date": yesterday})

        await authed_client.get(TASKS_URL)
        await authed_client.get(TASKS_URL)  # второй GET в тот же день

        assert len(captured_events["task.overdue"]) == 1

    # Задача с дедлайном сегодня — не просрочена
    async def test_today_due_date_not_overdue(self, authed_client: AsyncClient):
        today = str(date.today())
        await authed_client.post(TASKS_URL, json={"title": "Сегодня", "due_date": today})

        resp = await authed_client.get(TASKS_URL)
        task = resp.json()[0]
        assert task["is_overdue"] is False

    # Done-задача с прошедшим дедлайном — не помечается is_overdue
    async def test_done_task_not_overdue(self, authed_client: AsyncClient):
        yesterday = str(date.today() - timedelta(days=1))
        task = (await authed_client.post(
            TASKS_URL, json={"title": "Завершённая", "due_date": yesterday}
        )).json()
        await authed_client.post(complete_url(task["id"]))

        resp = await authed_client.get(TASKS_URL)
        found = next(t for t in resp.json() if t["id"] == task["id"])
        assert found["is_overdue"] is False


# ---------------------------------------------------------------------------
# Фильтрация задач
# ---------------------------------------------------------------------------

class TestTaskFilters:
    async def test_filter_by_status(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Задача"})).json()
        await authed_client.post(complete_url(task["id"]))

        resp = await authed_client.get(f"{TASKS_URL}?status=done")
        ids = [t["id"] for t in resp.json()]
        assert task["id"] in ids

        resp = await authed_client.get(f"{TASKS_URL}?status=todo")
        ids = [t["id"] for t in resp.json()]
        assert task["id"] not in ids

    async def test_filter_by_tag_exact_match(self, authed_client: AsyncClient):
        await authed_client.post(TASKS_URL, json={"title": "Работа", "tag": "work"})
        await authed_client.post(TASKS_URL, json={"title": "Личное", "tag": "personal"})

        resp = await authed_client.get(f"{TASKS_URL}?tag=work")
        titles = [t["title"] for t in resp.json()]
        assert "Работа" in titles
        assert "Личное" not in titles

    async def test_filter_overdue_only(self, authed_client: AsyncClient):
        yesterday = str(date.today() - timedelta(days=1))
        tomorrow = str(date.today() + timedelta(days=1))
        await authed_client.post(TASKS_URL, json={"title": "Просрочена", "due_date": yesterday})
        await authed_client.post(TASKS_URL, json={"title": "Актуальная", "due_date": tomorrow})

        resp = await authed_client.get(f"{TASKS_URL}?overdue_only=true")
        titles = [t["title"] for t in resp.json()]
        assert "Просрочена" in titles
        assert "Актуальная" not in titles


# ---------------------------------------------------------------------------
# PATCH и DELETE
# ---------------------------------------------------------------------------

class TestUpdateDeleteTask:
    async def test_patch_title_returns_200(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Старый заголовок"})).json()
        resp = await authed_client.patch(task_url(task["id"]), json={"title": "Новый заголовок"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Новый заголовок"

    async def test_patch_partial_keeps_other_fields(self, authed_client: AsyncClient):
        task = (await authed_client.post(
            TASKS_URL, json={"title": "Задача", "priority": "high"}
        )).json()
        resp = await authed_client.patch(task_url(task["id"]), json={"title": "Переименована"})
        assert resp.json()["priority"] == "high"

    async def test_patch_nonexistent_returns_404(self, authed_client: AsyncClient):
        resp = await authed_client.patch(task_url(uuid.uuid4()), json={"title": "X"})
        assert resp.status_code == 404

    async def test_delete_returns_204(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Удалить меня"})).json()
        resp = await authed_client.delete(task_url(task["id"]))
        assert resp.status_code == 204

    async def test_deleted_task_not_in_list(self, authed_client: AsyncClient):
        task = (await authed_client.post(TASKS_URL, json={"title": "Удалить меня"})).json()
        await authed_client.delete(task_url(task["id"]))
        resp = await authed_client.get(TASKS_URL)
        ids = [t["id"] for t in resp.json()]
        assert task["id"] not in ids

    async def test_delete_nonexistent_returns_404(self, authed_client: AsyncClient):
        resp = await authed_client.delete(task_url(uuid.uuid4()))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Habit-links CRUD
# ---------------------------------------------------------------------------

class TestHabitLinks:
    async def test_create_link_returns_201(self, authed_client: AsyncClient):
        resp = await authed_client.post(LINKS_URL, json={
            "habit_id": str(uuid.uuid4()),
            "task_title_template": "Внести вес",
        })
        assert resp.status_code == 201

    async def test_create_link_enabled_by_default(self, authed_client: AsyncClient):
        resp = await authed_client.post(LINKS_URL, json={
            "habit_id": str(uuid.uuid4()),
            "task_title_template": "Внести вес",
        })
        assert resp.json()["enabled"] is True

    async def test_list_links_returns_created(self, authed_client: AsyncClient):
        habit_id = str(uuid.uuid4())
        await authed_client.post(LINKS_URL, json={
            "habit_id": habit_id,
            "task_title_template": "Внести вес",
        })
        resp = await authed_client.get(LINKS_URL)
        assert any(l["habit_id"] == habit_id for l in resp.json())

    async def test_patch_link_enabled_false(self, authed_client: AsyncClient):
        link = (await authed_client.post(LINKS_URL, json={
            "habit_id": str(uuid.uuid4()),
            "task_title_template": "Внести вес",
        })).json()
        resp = await authed_client.patch(link_url(link["id"]), json={"enabled": False})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    async def test_patch_link_template(self, authed_client: AsyncClient):
        link = (await authed_client.post(LINKS_URL, json={
            "habit_id": str(uuid.uuid4()),
            "task_title_template": "Старый шаблон",
        })).json()
        resp = await authed_client.patch(link_url(link["id"]), json={"task_title_template": "Новый шаблон"})
        assert resp.json()["task_title_template"] == "Новый шаблон"

    async def test_delete_link_returns_204(self, authed_client: AsyncClient):
        link = (await authed_client.post(LINKS_URL, json={
            "habit_id": str(uuid.uuid4()),
            "task_title_template": "Внести вес",
        })).json()
        resp = await authed_client.delete(link_url(link["id"]))
        assert resp.status_code == 204

    async def test_patch_nonexistent_link_returns_404(self, authed_client: AsyncClient):
        resp = await authed_client.patch(link_url(uuid.uuid4()), json={"enabled": False})
        assert resp.status_code == 404

    # AC#6: активная связка + событие из bus → задача создаётся
    async def test_active_link_habit_event_creates_task(
        self, authed_client: AsyncClient, test_user
    ):
        from app.core.events.bus import bus
        from app.modules.tasks.service import TaskService
        from tests.conftest import test_session_factory

        habit_id = uuid.uuid4()
        await authed_client.post(LINKS_URL, json={
            "habit_id": str(habit_id),
            "task_title_template": "Взвеситься",
        })

        # Публикуем событие через сервис напрямую, имитируя подписчика
        async with test_session_factory() as session:
            svc = TaskService(session, bus)
            await svc.on_habit_completed({
                "habit_id": str(habit_id),
                "user_id": str(test_user.id),
                "date": str(date.today()),
                "current_streak": 1,
            })

        resp = await authed_client.get(TASKS_URL)
        titles = [t["title"] for t in resp.json()]
        assert "Взвеситься" in titles

    # AC#7: disabled связка → задача не создаётся
    async def test_disabled_link_habit_event_no_task(
        self, authed_client: AsyncClient, test_user
    ):
        from app.core.events.bus import bus
        from app.modules.tasks.service import TaskService
        from tests.conftest import test_session_factory

        habit_id = uuid.uuid4()
        link = (await authed_client.post(LINKS_URL, json={
            "habit_id": str(habit_id),
            "task_title_template": "Взвеситься",
        })).json()
        await authed_client.patch(link_url(link["id"]), json={"enabled": False})

        async with test_session_factory() as session:
            svc = TaskService(session, bus)
            await svc.on_habit_completed({
                "habit_id": str(habit_id),
                "user_id": str(test_user.id),
                "date": str(date.today()),
                "current_streak": 1,
            })

        resp = await authed_client.get(TASKS_URL)
        assert len(resp.json()) == 0

    # AC#8: нет связки → нет ошибок, нет задач
    async def test_no_link_habit_event_no_error(
        self, authed_client: AsyncClient, test_user
    ):
        from app.core.events.bus import bus
        from app.modules.tasks.service import TaskService
        from tests.conftest import test_session_factory

        async with test_session_factory() as session:
            svc = TaskService(session, bus)
            await svc.on_habit_completed({
                "habit_id": str(uuid.uuid4()),
                "user_id": str(test_user.id),
                "date": str(date.today()),
                "current_streak": 1,
            })

        resp = await authed_client.get(TASKS_URL)
        assert len(resp.json()) == 0


# ---------------------------------------------------------------------------
# AC#9 — Изоляция по owner
# ---------------------------------------------------------------------------

class TestOwnershipIsolation:
    # AC#9: GET чужой задачи → 404
    async def test_foreign_task_get_returns_404(
        self, authed_client: AsyncClient, client: AsyncClient, create_tables
    ):
        from app.core.auth.models import User
        from app.core.auth.service import create_access_token, hash_password
        from tests.conftest import test_session_factory

        task = (await authed_client.post(TASKS_URL, json={"title": "Моя задача"})).json()

        other = User(
            id=uuid.uuid4(),
            email="other_tasks@example.com",
            password_hash=hash_password("pass"),
        )
        async with test_session_factory() as s:
            s.add(other)
            await s.commit()

        client.cookies.set("access_token", create_access_token(other.id))
        resp = await client.get(task_url(task["id"]))
        assert resp.status_code == 404

    # PATCH чужой задачи → 404
    async def test_foreign_task_patch_returns_404(
        self, authed_client: AsyncClient, client: AsyncClient, create_tables
    ):
        from app.core.auth.models import User
        from app.core.auth.service import create_access_token, hash_password
        from tests.conftest import test_session_factory

        task = (await authed_client.post(TASKS_URL, json={"title": "Моя задача"})).json()

        other = User(
            id=uuid.uuid4(),
            email="other_tasks2@example.com",
            password_hash=hash_password("pass"),
        )
        async with test_session_factory() as s:
            s.add(other)
            await s.commit()

        client.cookies.set("access_token", create_access_token(other.id))
        resp = await client.patch(task_url(task["id"]), json={"title": "Взлом"})
        assert resp.status_code == 404

    # DELETE чужой задачи → 404
    async def test_foreign_task_delete_returns_404(
        self, authed_client: AsyncClient, client: AsyncClient, create_tables
    ):
        from app.core.auth.models import User
        from app.core.auth.service import create_access_token, hash_password
        from tests.conftest import test_session_factory

        task = (await authed_client.post(TASKS_URL, json={"title": "Моя задача"})).json()

        other = User(
            id=uuid.uuid4(),
            email="other_tasks3@example.com",
            password_hash=hash_password("pass"),
        )
        async with test_session_factory() as s:
            s.add(other)
            await s.commit()

        client.cookies.set("access_token", create_access_token(other.id))
        resp = await client.delete(task_url(task["id"]))
        assert resp.status_code == 404

    # GET списка возвращает только свои задачи (чужие не видны)
    async def test_list_returns_only_own_tasks(
        self, authed_client: AsyncClient, client: AsyncClient, create_tables
    ):
        from app.core.auth.models import User
        from app.core.auth.service import create_access_token, hash_password
        from tests.conftest import test_session_factory

        await authed_client.post(TASKS_URL, json={"title": "Задача test_user"})

        other = User(
            id=uuid.uuid4(),
            email="other_tasks4@example.com",
            password_hash=hash_password("pass"),
        )
        async with test_session_factory() as s:
            s.add(other)
            await s.commit()

        client.cookies.set("access_token", create_access_token(other.id))
        resp = await client.get(TASKS_URL)
        assert resp.json() == []
