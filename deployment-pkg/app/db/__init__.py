"""
SRP Autonomous OS — Database layer.

Exports:
    get_db          — FastAPI dependency for a SQLAlchemy session
    engine          — SQLAlchemy engine (used for table creation)
    Base            — declarative base (all ORM models inherit from this)
    db_service      — high-level service layer for CRUD operations
"""
from .database import engine, Base, get_db  # noqa: F401
from .service import db_service              # noqa: F401
