"""One-shot database bootstrap.

Run with:

    python -m scripts.init_db

Useful in environments where you want the SQLite file (and any future tables)
created without first starting the API.
"""

from __future__ import annotations

import sys

from app.core.logging import configure_logging, get_logger
from app.database import init_db


def main() -> int:
    """Initialise the database and exit with a status code."""
    configure_logging()
    logger = get_logger("tradingos.scripts.init_db")
    try:
        init_db()
    except Exception as exc:  # pragma: no cover - manual script
        logger.error("init_db.failed", error=str(exc))
        return 1
    logger.info("init_db.completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
