import uuid
from datetime import date, datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

SCHEMA = "finance"


class Account(Base):
    __tablename__ = "account"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    balance_kopecks: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )


class Category(Base):
    __tablename__ = "category"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    type: Mapped[str] = mapped_column(sa.String(10), nullable=False)  # income | expense


class Transaction(Base):
    __tablename__ = "transaction"
    __table_args__ = (
        sa.Index("ix_transaction_user_account_date", "user_id", "account_id", "occurred_at"),
        sa.Index("ix_transaction_user_category_date", "user_id", "category_id", "occurred_at"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    amount_kopecks: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    occurred_at: Mapped[date] = mapped_column(sa.Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    recurring_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    source: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="manual"
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )


class RecurringRule(Base):
    __tablename__ = "recurring_rule"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    amount_kopecks: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    frequency: Mapped[str] = mapped_column(sa.String(10), nullable=False)  # monthly | weekly
    day_of_month: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    day_of_week: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    next_due_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    active: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("true")
    )


class Budget(Base):
    __tablename__ = "budget"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    period: Mapped[str] = mapped_column(sa.String(7), nullable=False)  # YYYY-MM
    limit_kopecks: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
