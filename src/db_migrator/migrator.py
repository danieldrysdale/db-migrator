"""Core migration logic — thin wrapper around Alembic's programmatic API."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Engine


def _alembic_cfg(engine: Engine, migrations_dir: Path) -> Config:
    """Build an Alembic Config wired to *engine* and *migrations_dir*."""
    cfg = Config()
    cfg.set_main_option("script_location", str(migrations_dir))
    cfg.set_main_option("sqlalchemy.url", str(engine.url))
    # Suppress Alembic's default stdout logging; callers handle output
    cfg.attributes["connection"] = None
    return cfg


def upgrade(engine: Engine, migrations_dir: Path, revision: str = "head") -> None:
    """Apply migrations up to *revision* (default: latest)."""
    cfg = _alembic_cfg(engine, migrations_dir)
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, revision)


def downgrade(engine: Engine, migrations_dir: Path, revision: str = "-1") -> None:
    """Roll back migrations down to *revision* (default: one step back).

    Pass ``"base"`` to roll back everything.
    """
    cfg = _alembic_cfg(engine, migrations_dir)
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, revision)


def current_revision(engine: Engine) -> Optional[str]:
    """Return the current applied revision hash, or None if no migrations applied."""
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        rev = ctx.get_current_revision()
    return rev


def get_history(engine: Engine, migrations_dir: Path) -> list[dict]:
    """Return a list of all revisions with applied status.

    Each entry is a dict with keys: ``revision``, ``description``,
    ``applied``, ``is_current``.
    """
    current = current_revision(engine)
    cfg = _alembic_cfg(engine, migrations_dir)
    script = ScriptDirectory.from_config(cfg)

    history = []
    for rev in script.walk_revisions():
        history.append(
            {
                "revision": rev.revision,
                "description": rev.doc,
                "applied": _is_applied(engine, rev.revision, current, script),
                "is_current": rev.revision == current,
            }
        )
    # walk_revisions yields newest-first; reverse for chronological display
    history.reverse()
    return history


def pending_count(engine: Engine, migrations_dir: Path) -> int:
    """Return the number of unapplied migrations."""
    return sum(1 for r in get_history(engine, migrations_dir) if not r["applied"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_applied(
    engine: Engine,
    revision: str,
    current: Optional[str],
    script: ScriptDirectory,
) -> bool:
    """Return True if *revision* is at or before *current* in the chain."""
    if current is None:
        return False
    if revision == current:
        return True
    # Walk from base toward current; if we pass through revision it is applied
    try:
        for rev in script.iterate_revisions(current, "base"):
            if rev.revision == revision:
                return True
    except Exception:
        pass
    return False
