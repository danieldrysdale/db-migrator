# db-migrator

An Alembic-backed database migration tool with rollback support, built as a clean Python CLI package. Supports SQLite (default), PostgreSQL, MySQL, and SQL Server via environment variable.

## Features

- **Upgrade** — apply all pending migrations or target a specific revision
- **Downgrade** — roll back one step, to a specific revision, or all the way to base
- **Status** — see current revision and pending count at a glance
- **History** — list all migrations with applied/pending/current markers
- Multi-database support: SQLite, PostgreSQL, MySQL, SQL Server (pyodbc)
- Real warehouse schema across three migrations (locations → products → stock → movements)
- WCS schema migration (zones → locations → equipment → carriers → orders → commands → events)
- 31 pytest tests: 17 SQLite + 14 SQL Server integration tests
- SQL Server integration tests skip automatically when no server is configured
- Conventional Commits throughout

## Project structure

    db-migrator/
    ├── src/db_migrator/
    │   ├── __init__.py
    │   ├── cli.py          # argparse CLI entry point
    │   ├── config.py       # DB URL and path resolution
    │   ├── engine.py       # SQLAlchemy engine factory (SQLite, SQL Server, default)
    │   └── migrator.py     # Core Alembic wrapper
    ├── migrations/
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/
    │       ├── 0001_initial.py         # locations + products tables
    │       ├── 0002_add_stock.py       # stock table with FK constraints
    │       ├── 0003_add_movements.py   # movements audit table
    │       └── 0004_wcs_schema.py      # WCS domain model (8 tables, 6 indexes)
    ├── tests/
    │   ├── conftest.py
    │   ├── test_migrator.py            # SQLite tests (17)
    │   └── test_mssql.py               # SQL Server integration tests (14)
    └── pyproject.toml

## Installation

    git clone https://github.com/danieldrysdale/db-migrator
    cd db-migrator
    pip install -e ".[dev]"

    # SQL Server support
    pip install -e ".[dev,mssql]"

## Usage

    # Check current state
    db-migrator status

    # Show full migration history
    db-migrator history

    # Apply all pending migrations
    db-migrator upgrade

    # Apply up to a specific revision
    db-migrator upgrade 0001_initial

    # Roll back one step
    db-migrator downgrade

    # Roll back to a specific revision
    db-migrator downgrade 0001_initial

    # Roll back everything
    db-migrator downgrade base

## Database configuration

By default the tool writes to ./warehouse.db. Override with an environment variable:

    # SQLite (default)
    DB_MIGRATOR_URL="sqlite:///./warehouse.db"

    # PostgreSQL
    DB_MIGRATOR_URL="postgresql+psycopg2://user:pass@localhost/mydb"

    # SQL Server
    DB_MIGRATOR_URL="mssql+pyodbc://user:pass@localhost/mydb?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

## Running tests

    # SQLite tests only (no setup required)
    pytest tests/test_migrator.py -v

    # SQL Server integration tests
    DB_MIGRATOR_MSSQL_URL="mssql+pyodbc://user:pass@localhost/mydb?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    pytest tests/test_mssql.py -v

    # Full suite
    pytest -v

SQL Server tests skip automatically if DB_MIGRATOR_MSSQL_URL is not set or the server is unreachable.

## SQL Server compatibility notes

- Uses NO ACTION instead of RESTRICT for foreign key constraints
- Engine factory enables fast_executemany=True for SQL Server connections
- Requires pyodbc and ODBC Driver 17 or 18 for SQL Server
- TrustServerCertificate=yes required for local/development instances