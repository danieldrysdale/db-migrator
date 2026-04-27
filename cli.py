"""Command-line interface for db-migrator."""

from __future__ import annotations

import argparse
import sys

from db_migrator.config import get_database_url, get_migrations_dir
from db_migrator.engine import make_engine
from db_migrator import migrator


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    engine = make_engine(get_database_url())
    current = migrator.current_revision(engine)
    pending = migrator.pending_count(engine, get_migrations_dir())

    if current is None:
        print("Status : no migrations applied")
    else:
        print(f"Status : current revision → {current}")

    if pending == 0:
        print("         database is up to date")
    else:
        print(f"         {pending} pending migration(s)")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    engine = make_engine(get_database_url())
    history = migrator.get_history(engine, get_migrations_dir())

    if not history:
        print("No migrations found.")
        return 0

    print(f"{'Rev':>12}  {'Status':<10}  Description")
    print("-" * 60)
    for entry in history:
        marker = "* current" if entry["is_current"] else ("applied" if entry["applied"] else "pending")
        rev_short = entry["revision"][:8]
        print(f"{rev_short:>12}  {marker:<10}  {entry['description']}")
    return 0


def cmd_upgrade(args: argparse.Namespace) -> int:
    revision = args.revision or "head"
    engine = make_engine(get_database_url())

    pending = migrator.pending_count(engine, get_migrations_dir())
    if pending == 0:
        print("Nothing to do — database is already up to date.")
        return 0

    print(f"Upgrading to: {revision}")
    try:
        migrator.upgrade(engine, get_migrations_dir(), revision)
    except Exception as exc:
        print(f"ERROR: upgrade failed — {exc}", file=sys.stderr)
        return 1

    current = migrator.current_revision(engine)
    print(f"Done. Current revision: {current}")
    return 0


def cmd_downgrade(args: argparse.Namespace) -> int:
    revision = args.revision or "-1"
    engine = make_engine(get_database_url())

    current = migrator.current_revision(engine)
    if current is None:
        print("Nothing to roll back — no migrations applied.")
        return 0

    label = "one step" if revision == "-1" else f"revision {revision}"
    print(f"Rolling back: {label}")
    try:
        migrator.downgrade(engine, get_migrations_dir(), revision)
    except Exception as exc:
        print(f"ERROR: downgrade failed — {exc}", file=sys.stderr)
        return 1

    current = migrator.current_revision(engine)
    if current is None:
        print("Done. All migrations rolled back (database at base).")
    else:
        print(f"Done. Current revision: {current}")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="db-migrator",
        description="Alembic-backed database migration tool with rollback support.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    sub.add_parser("status", help="Show current migration status")
    sub.add_parser("history", help="List all migrations and their applied state")

    up = sub.add_parser("upgrade", help="Apply migrations (default: all)")
    up.add_argument(
        "revision",
        nargs="?",
        help="Target revision hash or 'head' (default: head)",
    )

    down = sub.add_parser("downgrade", help="Roll back migrations (default: one step)")
    down.add_argument(
        "revision",
        nargs="?",
        help="Target revision hash, '-1' (one step), or 'base' (all)",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "status": cmd_status,
        "history": cmd_history,
        "upgrade": cmd_upgrade,
        "downgrade": cmd_downgrade,
    }

    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
