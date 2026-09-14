from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: str = "medium"
    deadline: datetime | None = None
    project: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    deadline: datetime | None = None
    project: str | None = None


class TaskRead(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    priority: str
    deadline: datetime | None
    project: str | None

    model_config = {"from_attributes": True}
