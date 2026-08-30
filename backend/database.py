"""Database engine and session management for SQLAlchemy 2.0."""

import os
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.core.config import settings


def _build_engine_args(database_url: str) -> dict[str, Any]:
    """Return SQLAlchemy engine arguments tuned for PostgreSQL or SQLite tests."""
    args: dict[str, Any] = {"future": True}
    if database_url.startswith("sqlite"):
        # SQLite is only allowed when PULSE_ALLOW_SQLITE_TESTING is set.
        # The Settings class already enforces this, but we keep the guard here too.
        args["connect_args"] = {"check_same_thread": False}
        if database_url == "sqlite://" or database_url.startswith("sqlite:///:memory:"):
            args["poolclass"] = StaticPool
    else:
        # PostgreSQL / cloud SQL connection tuning
        args["pool_pre_ping"] = True
        args["pool_recycle"] = 300
        args["pool_timeout"] = 5
        if os.environ.get("VERCEL"):
            # Each concurrent serverless instance builds its own pool, so the
            # per-process numbers multiply by the number of live instances. A
            # 5+5 pool exhausts a hosted Postgres connection limit under modest
            # traffic; one connection per instance plus a little headroom keeps
            # the total bounded while the platform scales instances out.
            args["pool_size"] = 1
            args["max_overflow"] = 2
        else:
            args["pool_size"] = 5
            args["max_overflow"] = 5
    return args


engine = create_engine(
    settings.DATABASE_URL,
    **_build_engine_args(settings.DATABASE_URL),
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables from the SQLAlchemy 2.0 models."""
    from backend.models import Base

    Base.metadata.create_all(bind=engine)
