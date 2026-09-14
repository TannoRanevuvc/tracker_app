from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

SCHEMA = "habits"


class Habit(Base):
    __tablename__ = "habits"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)  # daily | weekly
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    checks: Mapped[list["HabitCheck"]] = relationship(back_populates="habit")


class HabitCheck(Base):
    __tablename__ = "habit_checks"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.habits.id"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)

    habit: Mapped["Habit"] = relationship(back_populates="checks")
