from pydantic import BaseModel


class HabitCreate(BaseModel):
    name: str
    frequency: str


class HabitUpdate(BaseModel):
    name: str | None = None
    frequency: str | None = None
    is_active: bool | None = None


class HabitRead(BaseModel):
    id: int
    name: str
    frequency: str
    is_active: bool

    model_config = {"from_attributes": True}
