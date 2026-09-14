"""habits schema: habit and checkin tables

Revision ID: b3e9f1a2c4d5
Revises: 0d8f44af58c0
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "b3e9f1a2c4d5"
down_revision: Union[str, None] = "0d8f44af58c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS habits")

    op.create_table(
        "habit",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("frequency_type", sa.String(20), nullable=False),
        sa.Column("weekly_days", ARRAY(sa.Integer()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(frequency_type = 'daily' AND weekly_days IS NULL) OR "
            "(frequency_type = 'weekly_days' AND weekly_days IS NOT NULL)",
            name="ck_habit_weekly_days_consistency",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="habits",
    )

    op.create_table(
        "checkin",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("habit_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["habit_id"], ["habits.habit.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("habit_id", "date", name="uq_checkin_habit_date"),
        schema="habits",
    )


def downgrade() -> None:
    op.drop_table("checkin", schema="habits")
    op.drop_table("habit", schema="habits")
    op.execute("DROP SCHEMA IF EXISTS habits CASCADE")
