"""TradingOS application package.

Top-level package for the TradingOS Trading Operating System. The release
identity (version, build, codename) lives in :mod:`app.version` — re-exported
here as ``__version__`` for convenience.
"""

from __future__ import annotations

from app.version import BUILD, CODENAME, VERSION

# Re-export the version so ``from app import __version__`` continues to work.
__version__: str = VERSION

__all__ = ["__version__", "VERSION", "BUILD", "CODENAME"]
