"""add stock table

Revision ID: 0002_add_stock
Revises: 0001_initial
Create Date: 2026-04-27 09:00:00.000000
"""
from __future__ import annotations
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_stock"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "stock",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "location_id",
            sa.Integer,
            sa.ForeignKey("locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer,
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("batch_ref", sa.String(50), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint("location_id", "product_id", "batch_ref", name="uq_stock_slot"),
    )

    op.create_index("ix_stock_location_id", "stock", ["location_id"])
    op.create_index("ix_stock_product_id", "stock", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_stock_product_id", table_name="stock")
    op.drop_index("ix_stock_location_id", table_name="stock")
    op.drop_table("stock")
