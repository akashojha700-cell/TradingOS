"""Repository layer package.

Repositories are the *only* layer that talks to the database directly. They
hide SQLAlchemy specifics from services and keep the persistence concern in
one place per aggregate.

Sprint 0 ships no repositories; they arrive in Sprint 1 alongside the market
event model.
"""
