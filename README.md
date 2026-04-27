# db-migrator

An Alembic-backed database migration tool with rollback support, built as a clean Python CLI package. Uses SQLite out of the box; drop-in replaceable with PostgreSQL or MySQL via environment variable.

## Features

- **Upgrade** — apply all pending migrations or target a specific revision
- **Downgrade** — roll back one step, to a specific revision, or all the way to base
- **Status** — see current revision and pending count at a glance
- **History** — list all migrations with applied/pending/current markers
- Real warehouse schema across three migrations (locations → products → stock → movements)
- 17 pytest tests covering upgrade, downgrade, roundtrip, schema, and edge cases
- Conventional Commits throughout

## Project structure

```
db-migrator/
├── src/db_migrator/
│   ├── __init__.py
│   ├── cli.py          # argparse CLI entry point
│   ├── config.py       # DB URL and path resolution
│   ├── engine.py       # SQLAlchemy engine factory
│   └── migrator.py     # Core Alembic wrapper
├── migrations/
│   ├── env.py          # Alembic environment (supports connection injection)
│   ├── script.py.mako  # Revision template
│   └── versions/
│       ├── 0001_initial.py         # locations + products tables
│       ├── 0002_add_stock.py       # stock table with FK constraints
│       └── 0003_add_movements.py   # movements audit table
├── tests/
│   ├── conftest.py
│   └── test_migrator.py
└── pyproject.toml
```

## Installation

```bash
git clone https://github.com/danieldrysdale/db-migrator
cd db-migrator
pip install -e ".[dev]"
```

## Usage

```bash
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
```

## Custom database

By default the tool writes to `./warehouse.db`. Override with an environment variable:

```bash
export DB_MIGRATOR_URL="sqlite:////absolute/path/to/my.db"
# or PostgreSQL:
export DB_MIGRATOR_URL="postgresql+psycopg2://user:pass@localhost/mydb"
db-migrator upgrade
```

## Running tests

```bash
pytest -v
```

Tests use isolated `tmp_path` SQLite databases — no cleanup required.

## Example migration

```python
# migrations/versions/0001_initial.py
def upgrade() -> None:
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("zone", sa.String(10), nullable=False),
        ...
    )

def downgrade() -> None:
    op.drop_table("locations")
```
