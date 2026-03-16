"""
PostgreSQL service shim — SRP Autonomous OS.

Supabase has been removed. All database operations now go through the
PostgreSQL-backed service in app.db.service.

This file is kept so legacy imports don't break:
    from app.integrations.supabase_client import pg_service

All new code should import directly from app.db:
    from app.db.service import db_service
    from app.db.database import get_db, SessionLocal
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Supabase SDK no longer used — import guard kept for safety
_SUPABASE_AVAILABLE = False
SupabaseClient = Any  # type: ignore

# Re-export PostgreSQL service so legacy imports resolve without breaking:
#   from app.integrations.supabase_client import pg_service
try:
    from app.db.service import db_service as pg_service   # noqa: F401
    from app.db.database import get_db, SessionLocal       # noqa: F401
    logger.info("PostgreSQL db_service loaded (via supabase_client shim).")
except Exception as _exc:  # pragma: no cover
    logger.warning("Could not load PostgreSQL service: %s", _exc)
    pg_service = None  # type: ignore


def _get_admin_client() -> None:  # kept as no-op stub
    """No-op stub — Supabase removed."""
    return None


# Supabase removed — no singleton needed.
# All DB access goes through app.db.service.db_service.