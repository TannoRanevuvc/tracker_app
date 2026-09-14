import uuid
from datetime import date, datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

SCHEMA = "habits"


class Habit(Base):
    __tablename__ = "habit"
    __table_args__ = (
        sa.CheckConstraint(
            "(frequency_type = 'daily' AND weekly_days IS NULL) OR "
            "(frequency_type = 'weekly_days' AND weekly_days IS NOT NULL)",
            name="ck_habit_weekly_days_consistency",
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    frequency_type: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    weekly_days: Mapped[Optional[list[int]]] = mapped_column(
        ARRAY(sa.Integer), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    checkins: Mapped[list["Checkin"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan"
    )


class Checkin(Base):
    __tablename__ = "checkin"
    __table_args__ = (
        sa.UniqueConstraint("habit_id", "date", name="uq_checkin_habit_date"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    habit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(f"{SCHEMA}.habit.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )

    habit: Mapped["Habit"] = relationship(back_populates="checkins")
