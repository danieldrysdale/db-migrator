"""Configuration: database URL and path resolution for Alembic."""

import os
from pathlib import Path

# Root of the installed package — used to locate the migrations/ directory
_PACKAGE_ROOT = Path(__file__).parent.parent.parent  # project root


def get_database_url(override: str | None = None) -> str:
    """Return the SQLite database URL.

    Resolution order:
    1. ``override`` argument (used by tests to inject a temp DB)
    2. ``DB_MIGRATOR_URL`` environment variable
    3. Default: ``./warehouse.db`` relative to the working directory
    """
    if override:
        return override
    env = os.environ.get("DB_MIGRATOR_URL")
    if env:
        return env
    return f"sqlite:///{Path.cwd() / 'warehouse.db'}"


def get_migrations_dir() -> Path:
    """Return the absolute path to the migrations/ directory."""
    return _PACKAGE_ROOT / "migrations"
