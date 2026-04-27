"""add movements audit table

Revision ID: 0003_add_movements
Revises: 0002_add_stock
Create Date: 2026-04-27 10:00:00.000000
"""
from __future__ import annotations
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_add_movements"
down_revision: Union[str, None] = "0002_add_stock"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None

MOVEMENT_TYPES = ("INBOUND", "OUTBOUND", "TRANSFER", "ADJUSTMENT")


def upgrade() -> None:
    op.create_table(
        "movements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer,
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "from_location_id",
            sa.Integer,
            sa.ForeignKey("locations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "to_location_id",
            sa.Integer,
            sa.ForeignKey("locations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("movement_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("operator", sa.String(50), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )

    op.create_index("ix_movements_product_id", "movements", ["product_id"])
    op.create_index("ix_movements_occurred_at", "movements", ["occurred_at"])
    op.create_index("ix_movements_type", "movements", ["movement_type"])


def downgrade() -> None:
    op.drop_index("ix_movements_type", table_name="movements")
    op.drop_index("ix_movements_occurred_at", table_name="movements")
    op.drop_index("ix_movements_product_id", table_name="movements")
    op.drop_table("movements")
