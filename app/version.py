"""Single source of truth for the TradingOS release identity.

Bumped exactly once per release, alongside the CHANGELOG entry and the git tag.
Everything else in the codebase reads from here — never duplicate these
constants elsewhere.

Versioning policy lives in ``governance/RELEASE_PROCESS.md``.
"""

from __future__ import annotations

#: Semantic version. Follows MAJOR.MINOR.PATCH.
VERSION: str = "0.2.0"

#: Build label. Used in logs and the ``/version`` endpoint to identify which
#: sprint cut this build.
BUILD: str = "Sprint-1"

#: Human-readable release name. One-or-two words.
CODENAME: str = "Terminal"

__all__ = ["VERSION", "BUILD", "CODENAME"]
