"""SQL Server integration tests for db-migrator.

These tests require a running SQL Server instance and the DB_MIGRATOR_MSSQL_URL
environment variable to be set. They are skipped automatically if the variable
is not present or the connection fails.

Usage:
    $env:DB_MIGRATOR_MSSQL_URL = "mssql+pyodbc://wcs_app:WcsApp#2026!@localhost/WCS_TEST?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    py -m pytest tests/test_mssql.py -v
"""
from __future__ import annotations
import os
import pytest
from sqlalchemy import inspect, text

from db_migrator.engine import make_engine
from db_migrator.migrator import upgrade, downgrade, get_history, pending_count
from db_migrator.config import get_migrations_dir


MSSQL_URL = os.environ.get("DB_MIGRATOR_MSSQL_URL")


def mssql_available() -> bool:
    """Return True if SQL Server is reachable with the configured URL."""
    if not MSSQL_URL:
        return False
    try:
        engine = make_engine(MSSQL_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


skip_if_no_mssql = pytest.mark.skipif(
    not mssql_available(),
    reason="DB_MIGRATOR_MSSQL_URL not set or SQL Server not reachable"
)


@pytest.fixture(scope="module")
def mssql_engine():
    """Engine connected to the SQL Server test database.
    
    Resets to base before each test module and upgrades to head afterwards.
    """
    engine = make_engine(MSSQL_URL)
    migrations_dir = get_migrations_dir()
    # Start from a clean state
    downgrade(engine, migrations_dir, "base")
    yield engine
    # Leave at head after tests
    upgrade(engine, migrations_dir)
    engine.dispose()


@pytest.fixture(autouse=True)
def reset_to_base(mssql_engine):
    """Reset to base before each test."""
    migrations_dir = get_migrations_dir()
    downgrade(mssql_engine, migrations_dir, "base")
    yield


@skip_if_no_mssql
class TestMSSQLUpgrade:

    def test_upgrade_to_head_applies_all_migrations(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        assert pending_count(mssql_engine, migrations_dir) == 0

    def test_upgrade_creates_warehouse_tables(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        inspector = inspect(mssql_engine)
        tables = inspector.get_table_names()
        assert "locations" in tables
        assert "products" in tables
        assert "stock" in tables
        assert "movements" in tables

    def test_upgrade_creates_wcs_tables(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        inspector = inspect(mssql_engine)
        tables = inspector.get_table_names()
        assert "wcs_zone" in tables
        assert "wcs_location" in tables
        assert "wcs_equipment" in tables
        assert "wcs_carrier" in tables
        assert "wcs_carrier_item" in tables
        assert "wcs_transport_order" in tables
        assert "wcs_move_command" in tables
        assert "wcs_equipment_event" in tables

    def test_upgrade_to_specific_revision(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir, "0001_initial")
        assert pending_count(mssql_engine, migrations_dir) == 3

    def test_upgrade_is_idempotent(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        upgrade(mssql_engine, migrations_dir)
        assert pending_count(mssql_engine, migrations_dir) == 0


@skip_if_no_mssql
class TestMSSQLDowngrade:

    def test_downgrade_one_step(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        downgrade(mssql_engine, migrations_dir)
        history = get_history(mssql_engine, migrations_dir)
        applied = [r for r in history if r["applied"]]
        assert applied[-1]["revision"].startswith("0003")

    def test_downgrade_to_base_removes_all_tables(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        downgrade(mssql_engine, migrations_dir, "base")
        inspector = inspect(mssql_engine)
        tables = inspector.get_table_names()
        wcs_tables = [t for t in tables if t.startswith("wcs_")]
        assert len(wcs_tables) == 0

    def test_downgrade_then_upgrade_roundtrip(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        downgrade(mssql_engine, migrations_dir, "base")
        upgrade(mssql_engine, migrations_dir)
        assert pending_count(mssql_engine, migrations_dir) == 0


@skip_if_no_mssql
class TestMSSQLSchema:

    def test_wcs_zone_has_expected_columns(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        inspector = inspect(mssql_engine)
        columns = {c["name"] for c in inspector.get_columns("wcs_zone")}
        assert {"zone_id", "zone_code", "zone_name", "zone_type", "parent_zone_id", "active"} <= columns

    def test_wcs_equipment_has_expected_columns(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        inspector = inspect(mssql_engine)
        columns = {c["name"] for c in inspector.get_columns("wcs_equipment")}
        assert {"equipment_id", "equipment_code", "equipment_type", "status", "plc_address", "last_heartbeat"} <= columns

    def test_can_insert_and_query_wcs_zone(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        with mssql_engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO wcs_zone (zone_code, zone_name, zone_type) "
                "VALUES ('TEST-Z1', 'Test Zone', 'CONVEYOR')"
            ))
            result = conn.execute(
                text("SELECT zone_name FROM wcs_zone WHERE zone_code = 'TEST-Z1'")
            )
            row = result.fetchone()
        assert row is not None
        assert row[0] == "Test Zone"


@skip_if_no_mssql
class TestMSSQLHistory:

    def test_history_returns_all_revisions(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        history = get_history(mssql_engine, migrations_dir)
        assert len(history) == 4

    def test_history_shows_pending_before_upgrade(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        history = get_history(mssql_engine, migrations_dir)
        assert all(not r["applied"] for r in history)

    def test_history_shows_applied_after_upgrade(self, mssql_engine):
        migrations_dir = get_migrations_dir()
        upgrade(mssql_engine, migrations_dir)
        history = get_history(mssql_engine, migrations_dir)
        assert all(r["applied"] for r in history)