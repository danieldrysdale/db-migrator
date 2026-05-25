"""SQLAlchemy engine factory."""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def make_engine(database_url: str) -> Engine:
    """Create and return a SQLAlchemy engine for the given URL.

    For SQLite we enable WAL mode and foreign key enforcement.
    For SQL Server we enable fast_executemany for performance.
    """
    connect_args = {}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            echo=False,
        )
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    if database_url.startswith("mssql"):
        engine = create_engine(
            database_url,
            fast_executemany=True,
            echo=False,
        )
        return engine

    # Default: PostgreSQL, MySQL, etc.
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        echo=False,
    )
    return engine