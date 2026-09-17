"""motivation schema: user_progress, achievement, user_achievement tables

Revision ID: e2f3a4b5c6d7
Revises: c1f2e3d4a5b6
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, None] = "c1f2e3d4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS motivation")

    op.create_table(
        "achievement",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
        schema="motivation",
    )

    op.create_table(
        "user_progress",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("xp_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        schema="motivation",
    )

    op.create_table(
        "user_achievement",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("achievement_code", sa.Text(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["achievement_code"], ["motivation.achievement.code"]
        ),
        sa.PrimaryKeyConstraint("user_id", "achievement_code"),
        schema="motivation",
    )

    # Seed catalog
    from app.modules.motivation.catalog import ACHIEVEMENTS
    op.bulk_insert(
        sa.table(
            "achievement",
            sa.column("code", sa.Text),
            sa.column("name", sa.Text),
            sa.column("description", sa.Text),
            schema="motivation",
        ),
        ACHIEVEMENTS,
    )


def downgrade() -> None:
    op.drop_table("user_achievement", schema="motivation")
    op.drop_table("user_progress", schema="motivation")
    op.drop_table("achievement", schema="motivation")
    op.execute("DROP SCHEMA IF EXISTS motivation CASCADE")
