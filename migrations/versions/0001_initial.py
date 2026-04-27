"""create locations and products tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-27 08:00:00.000000
"""
from __future__ import annotations
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("zone", sa.String(10), nullable=False),
        sa.Column("aisle", sa.String(5), nullable=False),
        sa.Column("bay", sa.Integer, nullable=False),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sku", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("unit_of_measure", sa.String(20), nullable=False, server_default="EA"),
        sa.Column("weight_kg", sa.Numeric(10, 3), nullable=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )


def downgrade() -> None:
    op.drop_table("products")
    op.drop_table("locations")
