"""finance schema: account, category, transaction, recurring_rule, budget tables

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS finance")

    op.create_table(
        "account",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("balance_kopecks", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="finance",
    )

    op.create_table(
        "category",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="finance",
    )

    op.create_table(
        "transaction",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("amount_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("occurred_at", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("recurring_rule_id", sa.UUID(), nullable=True),
        sa.Column(
            "source", sa.String(20), nullable=False, server_default="manual"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="finance",
    )
    op.create_index(
        "ix_transaction_user_account_date",
        "transaction",
        ["user_id", "account_id", "occurred_at"],
        schema="finance",
    )
    op.create_index(
        "ix_transaction_user_category_date",
        "transaction",
        ["user_id", "category_id", "occurred_at"],
        schema="finance",
    )

    op.create_table(
        "recurring_rule",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("amount_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("frequency", sa.String(10), nullable=False),
        sa.Column("day_of_month", sa.Integer(), nullable=True),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("next_due_date", sa.Date(), nullable=False),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="finance",
    )

    op.create_table(
        "budget",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("limit_kopecks", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="finance",
    )


def downgrade() -> None:
    op.drop_table("budget", schema="finance")
    op.drop_index(
        "ix_transaction_user_category_date", table_name="transaction", schema="finance"
    )
    op.drop_index(
        "ix_transaction_user_account_date", table_name="transaction", schema="finance"
    )
    op.drop_table("recurring_rule", schema="finance")
    op.drop_table("transaction", schema="finance")
    op.drop_table("category", schema="finance")
    op.drop_table("account", schema="finance")
    op.execute("DROP SCHEMA IF EXISTS finance CASCADE")
