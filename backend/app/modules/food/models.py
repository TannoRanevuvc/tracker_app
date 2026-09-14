import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

SCHEMA = "food"


class Product(Base):
    __tablename__ = "product"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    kcal_per_100g: Mapped[float] = mapped_column(sa.Numeric(6, 2), nullable=False)
    protein_g_per_100g: Mapped[float] = mapped_column(sa.Numeric(6, 2), nullable=False)
    fat_g_per_100g: Mapped[float] = mapped_column(sa.Numeric(6, 2), nullable=False)
    carbs_g_per_100g: Mapped[float] = mapped_column(sa.Numeric(6, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )


class MealEntry(Base):
    __tablename__ = "meal_entry"
    __table_args__ = (
        sa.Index("ix_meal_entry_user_logged_at", "user_id", "logged_at"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(f"{SCHEMA}.product.id"),
        nullable=False,
    )
    quantity_g: Mapped[float] = mapped_column(sa.Numeric(6, 1), nullable=False)
    meal_type: Mapped[str] = mapped_column(sa.String(10), nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
    price_kopecks: Mapped[Optional[int]] = mapped_column(sa.BigInteger, nullable=True)
    # Денормализованные КБЖУ на момент создания (не пересчитываются при редактировании продукта)
    kcal: Mapped[float] = mapped_column(sa.Numeric(8, 1), nullable=False)
    protein_g: Mapped[float] = mapped_column(sa.Numeric(6, 1), nullable=False)
    fat_g: Mapped[float] = mapped_column(sa.Numeric(6, 1), nullable=False)
    carbs_g: Mapped[float] = mapped_column(sa.Numeric(6, 1), nullable=False)


class DailyGoal(Base):
    __tablename__ = "daily_goal"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    kcal_goal: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    protein_goal_g: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    fat_goal_g: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    carbs_goal_g: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    effective_from: Mapped[sa.Date] = mapped_column(sa.Date, nullable=False)
