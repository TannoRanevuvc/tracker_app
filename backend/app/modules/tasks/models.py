from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

SCHEMA = "tasks"


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="todo")  # todo | in_progress | done
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low | medium | high
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    project: Mapped[str | None] = mapped_column(String(255))
