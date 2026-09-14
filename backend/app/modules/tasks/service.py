import uuid
from datetime import UTC, date, datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.bus import EventBus
from app.modules.tasks.models import HabitTaskLink, Task

# Дедупликация task.overdue: (task_id_str, date) — обнуляется при смене даты естественным образом
_overdue_notified_today: dict[tuple[str, date], bool] = {}


def is_task_overdue(
    due_date: Optional[date], task_status: str, today: date
) -> bool:
    if due_date is None:
        return False
    return due_date < today and task_status != "done"


class TaskService:
    def __init__(self, session: AsyncSession, bus: EventBus) -> None:
        self.session = session
        self.bus = bus

    # ------------------------------------------------------------------
    # Внутренние хелперы
    # ------------------------------------------------------------------

    async def _get_task_for_user(
        self, user_id: uuid.UUID, task_id: uuid.UUID
    ) -> Task:
        result = await self.session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        task = result.scalars().first()
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return task

    async def _enrich(self, task: Task) -> Task:
        """Вычисляет is_overdue, публикует task.overdue при первом обнаружении за день."""
        today = date.today()
        overdue = is_task_overdue(task.due_date, task.status, today)
        if overdue:
            key = (str(task.id), today)
            if key not in _overdue_notified_today:
                _overdue_notified_today[key] = True
                await self.bus.publish(
                    "task.overdue",
                    {
                        "task_id": str(task.id),
                        "user_id": str(task.user_id),
                        "due_date": str(task.due_date),
                    },
                )
        task.is_overdue = overdue  # Python-атрибут; не маппится в БД
        return task

    async def _get_link_for_user(
        self, user_id: uuid.UUID, link_id: uuid.UUID
    ) -> HabitTaskLink:
        result = await self.session.execute(
            select(HabitTaskLink).where(
                HabitTaskLink.id == link_id,
                HabitTaskLink.user_id == user_id,
            )
        )
        link = result.scalars().first()
        if link is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return link

    async def _save(self, obj):
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    # ------------------------------------------------------------------
    # Tasks CRUD
    # ------------------------------------------------------------------

    async def create_task(
        self,
        user_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        due_date: Optional[date] = None,
        tag: Optional[str] = None,
    ) -> Task:
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            status="todo",
            priority=priority,
            due_date=due_date,
            tag=tag,
        )
        self.session.add(task)
        await self._save(task)
        # is_overdue вычисляется для ответа, но task.overdue не публикуется:
        # событие должно уходить только на GET-запросах (спека §6)
        task.is_overdue = is_task_overdue(task.due_date, task.status, date.today())
        return task

    async def get_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> Task:
        task = await self._get_task_for_user(user_id, task_id)
        return await self._enrich(task)

    async def list_tasks(
        self,
        user_id: uuid.UUID,
        status_filter: Optional[str] = None,
        tag: Optional[str] = None,
        overdue_only: bool = False,
    ) -> list[Task]:
        q = select(Task).where(Task.user_id == user_id)
        if status_filter is not None:
            q = q.where(Task.status == status_filter)
        if tag is not None:
            q = q.where(Task.tag == tag)
        result = await self.session.execute(q)
        tasks = [await self._enrich(t) for t in result.scalars().all()]
        if overdue_only:
            tasks = [t for t in tasks if t.is_overdue]
        return tasks

    async def update_task(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        new_status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[date] = None,
        tag: Optional[str] = None,
    ) -> Task:
        task = await self._get_task_for_user(user_id, task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if new_status is not None:
            task.status = new_status
        if priority is not None:
            task.priority = priority
        if due_date is not None:
            task.due_date = due_date
        if tag is not None:
            task.tag = tag
        await self._save(task)
        return await self._enrich(task)

    async def complete_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Task:
        task = await self._get_task_for_user(user_id, task_id)
        if task.status == "done":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)
        task.status = "done"
        task.completed_at = datetime.now(UTC)
        await self._save(task)
        await self.bus.publish(
            "task.completed",
            {
                "task_id": str(task.id),
                "user_id": str(task.user_id),
                "completed_at": task.completed_at.isoformat(),
                "priority": task.priority,
            },
        )
        return await self._enrich(task)

    async def reopen_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Task:
        task = await self._get_task_for_user(user_id, task_id)
        if task.status != "done":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)
        task.status = "todo"
        task.completed_at = None
        await self._save(task)
        return await self._enrich(task)

    async def delete_task(
        self, user_id: uuid.UUID, task_id: uuid.UUID
    ) -> None:
        task = await self._get_task_for_user(user_id, task_id)
        await self.session.delete(task)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Habit-task links
    # ------------------------------------------------------------------

    async def create_habit_link(
        self,
        user_id: uuid.UUID,
        habit_id: uuid.UUID,
        task_title_template: str,
    ) -> HabitTaskLink:
        link = HabitTaskLink(
            user_id=user_id,
            habit_id=habit_id,
            task_title_template=task_title_template,
            enabled=True,
        )
        self.session.add(link)
        return await self._save(link)

    async def list_habit_links(self, user_id: uuid.UUID) -> list[HabitTaskLink]:
        result = await self.session.execute(
            select(HabitTaskLink).where(HabitTaskLink.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_habit_link(
        self,
        user_id: uuid.UUID,
        link_id: uuid.UUID,
        enabled: Optional[bool] = None,
        task_title_template: Optional[str] = None,
    ) -> HabitTaskLink:
        link = await self._get_link_for_user(user_id, link_id)
        if enabled is not None:
            link.enabled = enabled
        if task_title_template is not None:
            link.task_title_template = task_title_template
        return await self._save(link)

    async def delete_habit_link(
        self, user_id: uuid.UUID, link_id: uuid.UUID
    ) -> None:
        link = await self._get_link_for_user(user_id, link_id)
        await self.session.delete(link)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Обработчик события habit.completed
    # ------------------------------------------------------------------

    async def on_habit_completed(self, payload: dict) -> None:
        try:
            habit_id = uuid.UUID(payload["habit_id"])
            user_id = uuid.UUID(payload["user_id"])
        except (KeyError, ValueError):
            return

        result = await self.session.execute(
            select(HabitTaskLink).where(
                HabitTaskLink.habit_id == habit_id,
                HabitTaskLink.user_id == user_id,
                HabitTaskLink.enabled.is_(True),
            )
        )
        link = result.scalars().first()
        if link is None:
            return

        task = Task(
            user_id=user_id,
            title=link.task_title_template,
            status="todo",
            priority="medium",
        )
        self.session.add(task)
        await self.session.commit()
