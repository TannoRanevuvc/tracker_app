import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.core.db import get_session
from app.core.events.bus import bus
from app.modules.tasks.schemas import (
    HabitTaskLinkCreate,
    HabitTaskLinkResponse,
    HabitTaskLinkUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

_UserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


def _svc(session: AsyncSession = Depends(get_session)) -> TaskService:
    return TaskService(session, bus)


_Svc = Annotated[TaskService, Depends(_svc)]


# ------------------------------------------------------------------
# Tasks (коллекция)
# ------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED, response_model=TaskResponse)
async def create_task(body: TaskCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_task(
        user_id=user_id,
        title=body.title,
        description=body.description,
        priority=body.priority,
        due_date=body.due_date,
        tag=body.tag,
    )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    user_id: _UserId,
    svc: _Svc,
    status: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    overdue_only: bool = Query(default=False),
):
    return await svc.list_tasks(
        user_id=user_id,
        status_filter=status,
        tag=tag,
        overdue_only=overdue_only,
    )


# ------------------------------------------------------------------
# Habit-links — статические пути ПЕРЕД /{task_id}, иначе FastAPI
# попытается разобрать "habit-links" как UUID и вернёт 422
# ------------------------------------------------------------------

@router.post(
    "/habit-links",
    status_code=status.HTTP_201_CREATED,
    response_model=HabitTaskLinkResponse,
)
async def create_habit_link(
    body: HabitTaskLinkCreate, user_id: _UserId, svc: _Svc
):
    return await svc.create_habit_link(
        user_id=user_id,
        habit_id=body.habit_id,
        task_title_template=body.task_title_template,
    )


@router.get("/habit-links", response_model=list[HabitTaskLinkResponse])
async def list_habit_links(user_id: _UserId, svc: _Svc):
    return await svc.list_habit_links(user_id=user_id)


@router.patch(
    "/habit-links/{link_id}", response_model=HabitTaskLinkResponse
)
async def update_habit_link(
    link_id: uuid.UUID, body: HabitTaskLinkUpdate, user_id: _UserId, svc: _Svc
):
    return await svc.update_habit_link(
        user_id=user_id,
        link_id=link_id,
        enabled=body.enabled,
        task_title_template=body.task_title_template,
    )


@router.delete("/habit-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit_link(link_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    await svc.delete_habit_link(user_id=user_id, link_id=link_id)


# ------------------------------------------------------------------
# Tasks (конкретный ресурс) — после статических путей
# ------------------------------------------------------------------

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    return await svc.get_task(user_id=user_id, task_id=task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID, body: TaskUpdate, user_id: _UserId, svc: _Svc
):
    return await svc.update_task(
        user_id=user_id,
        task_id=task_id,
        title=body.title,
        description=body.description,
        new_status=body.status,
        priority=body.priority,
        due_date=body.due_date,
        tag=body.tag,
    )


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    return await svc.complete_task(task_id=task_id, user_id=user_id)


@router.post("/{task_id}/reopen", response_model=TaskResponse)
async def reopen_task(task_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    return await svc.reopen_task(task_id=task_id, user_id=user_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    await svc.delete_task(user_id=user_id, task_id=task_id)
