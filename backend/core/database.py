from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

from backend.core.config import settings

connect_args = {}
db_url = settings.get_database_url
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)


def enable_sqlite_foreign_keys(sqlalchemy_engine) -> None:
    """Enable SQLite foreign-key enforcement for every connection from an engine."""
    if sqlalchemy_engine.dialect.name != "sqlite":
        return

    @event.listens_for(sqlalchemy_engine, "connect")
    def _set_sqlite_foreign_keys(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")


enable_sqlite_foreign_keys(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
