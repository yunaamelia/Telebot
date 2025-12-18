"""Structured logging configuration with JSON formatting and correlation IDs.

Provides consistent logging across the application with request tracing support.
"""
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Optional

import structlog
from pythonjsonlogger import jsonlogger

from src.config.settings import get_settings


# Context variable for correlation ID (persists across async calls)
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    """Get or generate correlation ID for request tracing.

    Returns:
        str: Correlation ID (UUID4 format)
    """
    corr_id = correlation_id_var.get()
    if corr_id is None:
        corr_id = str(uuid.uuid4())
        correlation_id_var.set(corr_id)
    return corr_id


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context.

    Args:
        correlation_id: Correlation ID to set
    """
    correlation_id_var.set(correlation_id)


def reset_correlation_id() -> None:
    """Reset correlation ID (generates new ID on next get_correlation_id call)."""
    correlation_id_var.set(None)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with correlation ID and timestamp."""

    def add_fields(
        self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]
    ) -> None:
        """Add custom fields to log record.

        Args:
            log_record: Log record dictionary to modify
            record: Original logging record
            message_dict: Message dictionary
        """
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add correlation ID for request tracing
        log_record["correlation_id"] = get_correlation_id()

        # Add log level
        log_record["level"] = record.levelname

        # Add logger name
        log_record["logger"] = record.name

        # Add module and function info
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno


def configure_logging() -> None:
    """Configure application logging with structured format.

    Sets up:
    - JSON logging for production (machine-readable)
    - Human-readable logging for development
    - Correlation IDs for request tracing
    - Log level from settings

    Example JSON output:
        {
            "timestamp": "2025-12-18T10:30:00.123456Z",
            "level": "INFO",
            "logger": "src.bot.handlers.transaction",
            "message": "Transaction recorded",
            "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": 12345,
            "transaction_id": "TX20251218001",
            "amount": 500000.00
        }
    """
    settings = get_settings()

    # Clear existing handlers
    logging.root.handlers = []

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    if settings.log_format == "json":
        # JSON format for production (structured, machine-readable)
        formatter = CustomJsonFormatter(
            fmt="%(timestamp)s %(level)s %(logger)s %(message)s",
            json_ensure_ascii=False,
        )
    else:
        # Text format for development (human-readable)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(correlation_id)s): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Inject correlation ID into text format
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.correlation_id = get_correlation_id()[:8]  # Short ID for readability
            return record

        logging.setLogRecordFactory(record_factory)

    handler.setFormatter(formatter)

    # Set log level
    log_level = getattr(logging, settings.log_level)
    logging.root.setLevel(log_level)
    logging.root.addHandler(handler)

    # Suppress noisy third-party logs
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance

    Example:
        ```python
        logger = get_logger(__name__)
        logger.info("Transaction recorded", extra={
            "user_id": 12345,
            "transaction_id": "TX20251218001",
            "amount": 500000.00
        })
        ```
    """
    return logging.getLogger(name)
