"""food.product: add unique constraint on external_id

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_food_product_external_id",
        "product",
        ["external_id"],
        schema="food",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_food_product_external_id",
        "product",
        schema="food",
    )
