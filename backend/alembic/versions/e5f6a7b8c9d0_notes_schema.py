"""notes schema: note table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-29 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS notes")

    op.create_table(
        "note",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("pinned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column(
            "archived", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="notes",
    )
    op.create_index(
        "ix_notes_note_user_pinned",
        "note",
        ["user_id", "pinned_at"],
        schema="notes",
    )
    op.create_index(
        "ix_notes_note_user_created",
        "note",
        ["user_id", "created_at"],
        schema="notes",
    )


def downgrade() -> None:
    op.drop_index("ix_notes_note_user_created", table_name="note", schema="notes")
    op.drop_index("ix_notes_note_user_pinned", table_name="note", schema="notes")
    op.drop_table("note", schema="notes")
    op.execute("DROP SCHEMA IF EXISTS notes CASCADE")
