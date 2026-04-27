"""SQLAlchemy engine factory."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def make_engine(database_url: str) -> Engine:
    """Create and return a SQLAlchemy engine for the given URL.

    For SQLite we enable WAL mode and foreign key enforcement.
    """
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        echo=False,
    )

    if database_url.startswith("sqlite"):
        from sqlalchemy import event, text

        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine
