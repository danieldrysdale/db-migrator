"""Shared pytest fixtures."""

import pytest
from sqlalchemy import inspect

from db_migrator.config import get_migrations_dir
from db_migrator.engine import make_engine
from db_migrator import migrator


@pytest.fixture
def db_url(tmp_path):
    """A fresh SQLite database URL in a temporary directory."""
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def engine(db_url):
    """A SQLAlchemy engine connected to the temp database."""
    return make_engine(db_url)


@pytest.fixture
def migrations_dir():
    return get_migrations_dir()


@pytest.fixture
def upgraded_engine(engine, migrations_dir):
    """An engine with all migrations already applied."""
    migrator.upgrade(engine, migrations_dir)
    return engine
