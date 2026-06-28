"""ORM models package.

Importing model modules here registers them with :class:`Base.metadata` so
:func:`app.database.init_db.init_db` discovers them automatically.
"""

from app.models.alert import Alert  # noqa: F401

__all__ = ["Alert"]
