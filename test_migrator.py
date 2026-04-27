"""Tests for the core migration logic."""

import pytest
from sqlalchemy import inspect, text

from db_migrator import migrator


class TestUpgrade:
    def test_upgrade_to_head_applies_all_migrations(self, engine, migrations_dir):
        migrator.upgrade(engine, migrations_dir)
        current = migrator.current_revision(engine)
        assert current == "0003_add_movements"

    def test_upgrade_creates_expected_tables(self, upgraded_engine):
        tables = inspect(upgraded_engine).get_table_names()
        assert "locations" in tables
        assert "products" in tables
        assert "stock" in tables
        assert "movements" in tables

    def test_upgrade_to_specific_revision(self, engine, migrations_dir):
        migrator.upgrade(engine, migrations_dir, "0001_initial")
        current = migrator.current_revision(engine)
        assert current == "0001_initial"
        tables = inspect(engine).get_table_names()
        assert "locations" in tables
        assert "products" in tables
        assert "stock" not in tables

    def test_upgrade_is_idempotent(self, engine, migrations_dir):
        migrator.upgrade(engine, migrations_dir)
        migrator.upgrade(engine, migrations_dir)  # should not raise
        assert migrator.current_revision(engine) == "0003_add_movements"


class TestDowngrade:
    def test_downgrade_one_step(self, upgraded_engine, migrations_dir):
        migrator.downgrade(upgraded_engine, migrations_dir, "-1")
        current = migrator.current_revision(upgraded_engine)
        assert current == "0002_add_stock"
        tables = inspect(upgraded_engine).get_table_names()
        assert "movements" not in tables

    def test_downgrade_to_base_removes_all_tables(self, upgraded_engine, migrations_dir):
        migrator.downgrade(upgraded_engine, migrations_dir, "base")
        current = migrator.current_revision(upgraded_engine)
        assert current is None
        tables = [t for t in inspect(upgraded_engine).get_table_names()
                  if t != "alembic_version"]
        assert tables == []

    def test_downgrade_then_upgrade_roundtrip(self, upgraded_engine, migrations_dir):
        migrator.downgrade(upgraded_engine, migrations_dir, "base")
        assert migrator.current_revision(upgraded_engine) is None
        migrator.upgrade(upgraded_engine, migrations_dir)
        assert migrator.current_revision(upgraded_engine) == "0003_add_movements"


class TestStatus:
    def test_current_revision_is_none_before_any_migration(self, engine):
        assert migrator.current_revision(engine) is None

    def test_current_revision_after_first_migration(self, engine, migrations_dir):
        migrator.upgrade(engine, migrations_dir, "0001_initial")
        assert migrator.current_revision(engine) == "0001_initial"


class TestHistory:
    def test_history_returns_all_revisions(self, engine, migrations_dir):
        history = migrator.get_history(engine, migrations_dir)
        assert len(history) == 3

    def test_history_shows_pending_before_upgrade(self, engine, migrations_dir):
        history = migrator.get_history(engine, migrations_dir)
        assert all(not r["applied"] for r in history)

    def test_history_shows_applied_after_upgrade(self, upgraded_engine, migrations_dir):
        history = migrator.get_history(upgraded_engine, migrations_dir)
        assert all(r["applied"] for r in history)

    def test_history_current_flag(self, engine, migrations_dir):
        migrator.upgrade(engine, migrations_dir, "0002_add_stock")
        history = migrator.get_history(engine, migrations_dir)
        current_entries = [r for r in history if r["is_current"]]
        assert len(current_entries) == 1
        assert current_entries[0]["revision"] == "0002_add_stock"

    def test_pending_count_decreases_after_upgrade(self, engine, migrations_dir):
        assert migrator.pending_count(engine, migrations_dir) == 3
        migrator.upgrade(engine, migrations_dir, "0001_initial")
        assert migrator.pending_count(engine, migrations_dir) == 2
        migrator.upgrade(engine, migrations_dir)
        assert migrator.pending_count(engine, migrations_dir) == 0


class TestSchema:
    def test_stock_table_has_expected_columns(self, upgraded_engine):
        cols = {c["name"] for c in inspect(upgraded_engine).get_columns("stock")}
        assert {"id", "location_id", "product_id", "quantity", "batch_ref", "updated_at"} <= cols

    def test_movements_table_has_expected_columns(self, upgraded_engine):
        cols = {c["name"] for c in inspect(upgraded_engine).get_columns("movements")}
        assert {"id", "product_id", "from_location_id", "to_location_id",
                "movement_type", "quantity", "occurred_at"} <= cols

    def test_can_insert_and_query_location(self, upgraded_engine):
        with upgraded_engine.begin() as conn:
            conn.execute(
                text("INSERT INTO locations (code, zone, aisle, bay, level) "
                     "VALUES ('A-01-01-1', 'A', '01', 1, 1)")
            )
            result = conn.execute(text("SELECT code FROM locations")).fetchone()
        assert result[0] == "A-01-01-1"
