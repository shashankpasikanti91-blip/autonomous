"""
SQLAlchemy database connection for SRP Autonomous OS.

Reads DATABASE_URL from the environment (set in .env).
Provides:
  - engine        — SQLAlchemy Engine
  - SessionLocal  — session factory
  - Base          — declarative base class
  - get_db()      — FastAPI dependency that yields a session
"""
from __future__ import annotations

import os
import logging
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection string
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/srp_os",
)

# ---------------------------------------------------------------------------
# Engine
#  - pool_pre_ping keeps connections healthy after idle periods
#  - echo=False in production; set DATABASE_ECHO=true to debug SQL
# ---------------------------------------------------------------------------
_echo_sql = os.getenv("DATABASE_ECHO", "false").lower() == "true"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=_echo_sql,
    # psycopg2 default pool is fine for local dev; tune for production
    pool_size=5,
    max_overflow=10,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Declarative base  (all ORM models inherit from Base)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator:
    """
    Yield a SQLAlchemy session and guarantee it is closed afterwards.

    Usage in a FastAPI route::

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Startup helper — create all tables that don't yet exist
# ---------------------------------------------------------------------------
def init_db() -> None:
    """
    Create all tables defined on Base.metadata (if they don't exist yet).
    Call this once from the FastAPI lifespan / startup event.
    """
    from db import models as _models  # noqa: F401 — ensures models are registered
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified / created.")
