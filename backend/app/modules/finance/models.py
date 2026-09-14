from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

SCHEMA = "finance"


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    balance_kopecks: Mapped[int] = mapped_column(Integer, default=0)  # always integer, never float


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # income | expense


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.accounts.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.categories.id"), nullable=False)
    amount_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)  # always integer, never float
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
