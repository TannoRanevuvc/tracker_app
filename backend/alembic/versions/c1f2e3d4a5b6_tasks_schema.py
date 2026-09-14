"""tasks schema: task and habit_task_link tables

Revision ID: c1f2e3d4a5b6
Revises: b3e9f1a2c4d5
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1f2e3d4a5b6"
down_revision: Union[str, None] = "b3e9f1a2c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS tasks")

    op.create_table(
        "task",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="todo"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("tag", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="tasks",
    )
    op.create_index(
        "ix_task_user_status", "task", ["user_id", "status"], schema="tasks"
    )
    op.create_index(
        "ix_task_user_due_date", "task", ["user_id", "due_date"], schema="tasks"
    )

    op.create_table(
        "habit_task_link",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("habit_id", sa.UUID(), nullable=False),
        sa.Column("task_title_template", sa.Text(), nullable=False),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="tasks",
    )


def downgrade() -> None:
    op.drop_table("habit_task_link", schema="tasks")
    op.drop_index("ix_task_user_due_date", table_name="task", schema="tasks")
    op.drop_index("ix_task_user_status", table_name="task", schema="tasks")
    op.drop_table("task", schema="tasks")
    op.execute("DROP SCHEMA IF EXISTS tasks CASCADE")
