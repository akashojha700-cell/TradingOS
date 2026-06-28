"""Database initialisation.

Creates any tables registered against :class:`app.database.Base`. In Sprint 0
no trading tables exist; this routine still runs to verify the engine and the
storage directory are healthy.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.database.session import Base, engine

logger = get_logger("tradingos.database")


def init_db() -> None:
    """Create database tables if they do not already exist.

    Idempotent — safe to call on every startup. Future sprints will add ORM
    models that get picked up here automatically via ``Base.metadata``.
    """
    # Import models so they register themselves with Base.metadata before
    # create_all is called. Sprint 0 has no models, so the import is a no-op
    # but the hook is kept in place for future sprints.
    import app.models  # noqa: F401  (intentional side-effect import)

    Base.metadata.create_all(bind=engine)
    logger.debug(
        "database.initialised",
        tables=sorted(Base.metadata.tables.keys()),
    )
