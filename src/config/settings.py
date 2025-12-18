"""Application settings using Pydantic for configuration management.

Settings are loaded from environment variables with validation and type checking.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading.

    All settings can be overridden via environment variables.

    Example:
        DATABASE_URL=postgresql://user:pass@localhost/db  # pragma: allowlist secret
        TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
    """

    # Application Environment
    environment: Literal["development", "production", "test"] = Field(
        default="development", description="Application environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode (verbose logging, SQL echo)")

    # Database Configuration
    database_url: str = Field(
        ...,  # Required field
        description="PostgreSQL database URL (postgresql://user:pass@host:port/dbname)",
    )

    # Telegram Bot Configuration
    telegram_bot_token: str = Field(
        ..., description="Telegram Bot API token from @BotFather"  # Required field
    )
    management_chat_id: int = Field(
        ..., description="Telegram chat ID for management reports and alerts"  # Required field
    )

    # Timezone Configuration
    timezone: str = Field(default="Asia/Makassar", description="WITA timezone (UTC+8)")

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="json", description="Log output format (json for production, text for development)"
    )

    # Rate Limiting & Performance
    max_amount: float = Field(
        default=10_000_000_000.00, description="Maximum transaction amount (10 billion per FR-022)"
    )
    duplicate_detection_window_seconds: int = Field(
        default=60, description="Time window for duplicate transaction detection"
    )

    # Scheduler Configuration
    daily_report_hour: int = Field(
        default=0, description="Hour to send daily report (24-hour format, 0 = midnight)"
    )
    daily_report_minute: int = Field(default=0, description="Minute to send daily report")
    report_retry_interval_minutes: int = Field(
        default=5, description="Retry interval for failed report delivery"
    )
    report_retry_max_minutes: int = Field(
        default=30, description="Maximum retry duration for report delivery"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql://' or 'postgresql+asyncpg://'"
            )
        return v

    @field_validator("telegram_bot_token")
    @classmethod
    def validate_telegram_token(cls, v: str) -> str:
        """Validate Telegram bot token format."""
        if ":" not in v:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN must be in format 'bot_id:token' (e.g., '123456:ABC-DEF...')"
            )
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone string."""
        try:
            import pytz

            pytz.timezone(v)
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {v}. Must be a valid pytz timezone.")
        return v

    @field_validator("max_amount")
    @classmethod
    def validate_max_amount(cls, v: float) -> float:
        """Validate maximum amount is positive."""
        if v <= 0:
            raise ValueError("max_amount must be positive")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Singleton settings instance loaded from environment

    Note:
        Uses LRU cache to ensure settings are loaded only once.
        Cache can be cleared with get_settings.cache_clear() for testing.
    """
    return Settings()
