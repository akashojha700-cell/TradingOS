"""Configuration package.

Exposes a cached :func:`get_settings` accessor so the rest of the application
imports configuration from a single location.
"""

from app.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
