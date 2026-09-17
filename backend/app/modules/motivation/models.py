import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

SCHEMA = "motivation"


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    xp_total: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )


class Achievement(Base):
    __tablename__ = "achievement"
    __table_args__ = {"schema": SCHEMA}

    code: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)


class UserAchievement(Base):
    __tablename__ = "user_achievement"
    __table_args__ = (
        sa.PrimaryKeyConstraint("user_id", "achievement_code"),
        {"schema": SCHEMA},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    achievement_code: Mapped[str] = mapped_column(
        sa.Text,
        sa.ForeignKey(f"{SCHEMA}.achievement.code"),
        nullable=False,
    )
    unlocked_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
