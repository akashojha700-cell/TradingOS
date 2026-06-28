"""Database package.

Owns the SQLAlchemy engine, session factory, declarative base, and the
``init_db`` bootstrap routine. Only this package should know which storage
engine is in use; the rest of the application talks to repositories.
"""

from app.database.session import Base, SessionLocal, engine, get_db
from app.database.init_db import init_db

__all__ = ["Base", "SessionLocal", "engine", "get_db", "init_db"]
