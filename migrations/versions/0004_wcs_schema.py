"""create WCS schema - zones, locations, equipment, carriers, orders, commands, events

Revision ID: 0004_wcs_schema
Revises: 0003_add_movements
Create Date: 2026-05-25 20:00:00.000000
"""
from __future__ import annotations
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_wcs_schema"
down_revision: Union[str, None] = "0003_add_movements"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "wcs_zone",
        sa.Column("zone_id",        sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("zone_code",      sa.String(20),   nullable=False, unique=True),
        sa.Column("zone_name",      sa.String(100),  nullable=False),
        sa.Column("zone_type",      sa.String(30),   nullable=False),
        sa.Column("parent_zone_id", sa.Integer,      sa.ForeignKey("wcs_zone.zone_id"), nullable=True),
        sa.Column("active",         sa.SmallInteger, nullable=False, server_default="1"),
    )

    op.create_table(
        "wcs_location",
        sa.Column("location_id",   sa.Integer,     primary_key=True, autoincrement=True),
        sa.Column("zone_id",       sa.Integer,     sa.ForeignKey("wcs_zone.zone_id"), nullable=False),
        sa.Column("location_code", sa.String(30),  nullable=False, unique=True),
        sa.Column("location_type", sa.String(30),  nullable=False),
        sa.Column("aisle",         sa.SmallInteger, nullable=True),
        sa.Column("bay",           sa.SmallInteger, nullable=True),
        sa.Column("level",         sa.SmallInteger, nullable=True),
        sa.Column("occupied",      sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("enabled",       sa.SmallInteger, nullable=False, server_default="1"),
    )

    op.create_table(
        "wcs_equipment",
        sa.Column("equipment_id",   sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("zone_id",        sa.Integer,      sa.ForeignKey("wcs_zone.zone_id"), nullable=False),
        sa.Column("equipment_code", sa.String(30),   nullable=False, unique=True),
        sa.Column("equipment_type", sa.String(30),   nullable=False),
        sa.Column("plc_address",    sa.String(50),   nullable=True),
        sa.Column("status",         sa.String(20),   nullable=False, server_default="'OFFLINE'"),
        sa.Column("last_heartbeat", sa.DateTime,     nullable=True),
        sa.Column("enabled",        sa.SmallInteger, nullable=False, server_default="1"),
    )

    op.create_table(
        "wcs_carrier",
        sa.Column("carrier_id",          sa.Integer,   primary_key=True, autoincrement=True),
        sa.Column("barcode",             sa.String(50), nullable=False, unique=True),
        sa.Column("carrier_type",        sa.String(30), nullable=False),
        sa.Column("current_location_id", sa.Integer,   sa.ForeignKey("wcs_location.location_id"), nullable=True),
        sa.Column("status",              sa.String(20), nullable=False, server_default="'UNTRACKED'"),
        sa.Column("last_seen",           sa.DateTime,  nullable=True),
    )

    op.create_table(
        "wcs_carrier_item",
        sa.Column("item_id",     sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("carrier_id",  sa.Integer,      sa.ForeignKey("wcs_carrier.carrier_id"), nullable=False),
        sa.Column("reference",   sa.String(50),   nullable=False),
        sa.Column("description", sa.String(200),  nullable=True),
        sa.Column("weight_kg",   sa.Numeric(8,3), nullable=True),
        sa.Column("status",      sa.String(20),   nullable=False, server_default="'ACTIVE'"),
    )

    op.create_table(
        "wcs_transport_order",
        sa.Column("order_id",            sa.Integer,   primary_key=True, autoincrement=True),
        sa.Column("order_ref",           sa.String(50), nullable=False, unique=True),
        sa.Column("carrier_id",          sa.Integer,   sa.ForeignKey("wcs_carrier.carrier_id"), nullable=False),
        sa.Column("origin_location_id",  sa.Integer,   sa.ForeignKey("wcs_location.location_id"), nullable=False),
        sa.Column("dest_location_id",    sa.Integer,   sa.ForeignKey("wcs_location.location_id"), nullable=False),
        sa.Column("priority",            sa.String(10), nullable=False, server_default="'NORMAL'"),
        sa.Column("status",              sa.String(20), nullable=False, server_default="'PENDING'"),
        sa.Column("created_at",          sa.DateTime,  nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("completed_at",        sa.DateTime,  nullable=True),
    )

    op.create_table(
        "wcs_move_command",
        sa.Column("command_id",       sa.Integer,   primary_key=True, autoincrement=True),
        sa.Column("order_id",         sa.Integer,   sa.ForeignKey("wcs_transport_order.order_id"), nullable=False),
        sa.Column("equipment_id",     sa.Integer,   sa.ForeignKey("wcs_equipment.equipment_id"), nullable=False),
        sa.Column("carrier_id",       sa.Integer,   sa.ForeignKey("wcs_carrier.carrier_id"), nullable=False),
        sa.Column("from_location_id", sa.Integer,   sa.ForeignKey("wcs_location.location_id"), nullable=False),
        sa.Column("to_location_id",   sa.Integer,   sa.ForeignKey("wcs_location.location_id"), nullable=False),
        sa.Column("direction",        sa.String(10), nullable=True),
        sa.Column("status",           sa.String(20), nullable=False, server_default="'QUEUED'"),
        sa.Column("issued_at",        sa.DateTime,  nullable=True),
        sa.Column("acked_at",         sa.DateTime,  nullable=True),
        sa.Column("completed_at",     sa.DateTime,  nullable=True),
    )

    op.create_table(
        "wcs_equipment_event",
        sa.Column("event_id",      sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("equipment_id",  sa.Integer,      sa.ForeignKey("wcs_equipment.equipment_id"), nullable=False),
        sa.Column("event_type",    sa.String(30),   nullable=False),
        sa.Column("severity",      sa.String(10),   nullable=False, server_default="'INFO'"),
        sa.Column("message",       sa.String(500),  nullable=True),
        sa.Column("raw_plc_data",  sa.Text,         nullable=True),
        sa.Column("occurred_at",   sa.DateTime,     nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("acknowledged",  sa.SmallInteger, nullable=False, server_default="0"),
    )

    # Indexes
    op.create_index("ix_wcs_location_zone",     "wcs_location",        ["zone_id"])
    op.create_index("ix_wcs_carrier_location",  "wcs_carrier",         ["current_location_id"])
    op.create_index("ix_wcs_carrier_status",    "wcs_carrier",         ["status"])
    op.create_index("ix_wcs_order_status",      "wcs_transport_order", ["status"])
    op.create_index("ix_wcs_command_status",    "wcs_move_command",    ["status"])
    op.create_index("ix_wcs_event_equipment",   "wcs_equipment_event", ["equipment_id", "occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_wcs_event_equipment",  "wcs_equipment_event")
    op.drop_index("ix_wcs_command_status",   "wcs_move_command")
    op.drop_index("ix_wcs_order_status",     "wcs_transport_order")
    op.drop_index("ix_wcs_carrier_status",   "wcs_carrier")
    op.drop_index("ix_wcs_carrier_location", "wcs_carrier")
    op.drop_index("ix_wcs_location_zone",    "wcs_location")

    op.drop_table("wcs_equipment_event")
    op.drop_table("wcs_move_command")
    op.drop_table("wcs_transport_order")
    op.drop_table("wcs_carrier_item")
    op.drop_table("wcs_carrier")
    op.drop_table("wcs_equipment")
    op.drop_table("wcs_location")
    op.drop_table("wcs_zone")