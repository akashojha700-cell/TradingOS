"""Application settings.

Configuration is loaded from environment variables (and optionally a local
``.env`` file). Following the architecture principle of *configuration over
hardcoding*, every tunable value lives here and is injected into the rest of
the application via :func:`get_settings`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import APP_NAME
from app.version import VERSION

Environment = Literal["development", "staging", "production", "test"]


class Settings(BaseSettings):
    """Strongly-typed application settings.

    All fields are sourced from environment variables. The ``.env`` file is
    loaded when present but environment variables always take precedence.
    """

    # --- Application metadata ---------------------------------------------
    # Defaults read from app.version / app.core.constants — never hardcoded.
    app_name: str = Field(default=APP_NAME, alias="APP_NAME")
    app_version: str = Field(default=VERSION, alias="APP_VERSION")
    app_env: Environment = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    # --- Database ---------------------------------------------------------
    database_url: str = Field(
        default="sqlite:///./storage/tradingos.db",
        alias="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    # --- Logging ----------------------------------------------------------
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")

    # --- CORS -------------------------------------------------------------
    cors_allow_origins: str = Field(default="*", alias="CORS_ALLOW_ORIGINS")

    # --- Ingest -----------------------------------------------------------
    # Optional shared secret for the TradingView webhook.
    # When empty the webhook is open (suitable for local development).
    # When set, callers must send ``X-Webhook-Secret: <value>`` to be accepted.
    tradingview_webhook_secret: str | None = Field(
        default=None,
        alias="TRADINGVIEW_WEBHOOK_SECRET",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ helpers
    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list, parsed from the comma-separated env."""
        raw = self.cors_allow_origins.strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        """True when running in a production environment."""
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Using ``lru_cache`` ensures environment variables are parsed exactly once
    per process. Tests can override this via FastAPI's dependency override
    mechanism.
    """
    return Settings()  # type: ignore[call-arg]
