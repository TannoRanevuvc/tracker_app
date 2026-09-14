"""food schema: product, meal_entry, daily_goal tables

Revision ID: a1b2c3d4e5f6
Revises: f3a4b5c6d7e8
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS food")

    op.create_table(
        "product",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("external_id", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kcal_per_100g", sa.Numeric(6, 2), nullable=False),
        sa.Column("protein_g_per_100g", sa.Numeric(6, 2), nullable=False),
        sa.Column("fat_g_per_100g", sa.Numeric(6, 2), nullable=False),
        sa.Column("carbs_g_per_100g", sa.Numeric(6, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="food",
    )

    op.create_table(
        "meal_entry",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity_g", sa.Numeric(6, 1), nullable=False),
        sa.Column("meal_type", sa.String(10), nullable=False),
        sa.Column(
            "logged_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("price_kopecks", sa.BigInteger(), nullable=True),
        sa.Column("kcal", sa.Numeric(8, 1), nullable=False),
        sa.Column("protein_g", sa.Numeric(6, 1), nullable=False),
        sa.Column("fat_g", sa.Numeric(6, 1), nullable=False),
        sa.Column("carbs_g", sa.Numeric(6, 1), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["food.product.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="food",
    )
    op.create_index(
        "ix_meal_entry_user_logged_at",
        "meal_entry",
        ["user_id", "logged_at"],
        schema="food",
    )

    op.create_table(
        "daily_goal",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("kcal_goal", sa.Integer(), nullable=False),
        sa.Column("protein_goal_g", sa.Integer(), nullable=True),
        sa.Column("fat_goal_g", sa.Integer(), nullable=True),
        sa.Column("carbs_goal_g", sa.Integer(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="food",
    )


def downgrade() -> None:
    op.drop_index("ix_meal_entry_user_logged_at", table_name="meal_entry", schema="food")
    op.drop_table("meal_entry", schema="food")
    op.drop_table("daily_goal", schema="food")
    op.drop_table("product", schema="food")
    op.execute("DROP SCHEMA IF EXISTS food CASCADE")
