"""Database connection management with PostgreSQL connection pooling.

This module provides async database connection functionality with connection pooling,
following SQLAlchemy 2.0+ async patterns.
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.pool import QueuePool

from src.config.settings import get_settings


class DatabaseConnection:
    """Manages database connection and connection pooling."""

    def __init__(self) -> None:
        """Initialize database connection manager."""
        self._engine: Optional[AsyncEngine] = None
        self._settings = get_settings()

    def get_engine(self) -> AsyncEngine:
        """Get or create the async database engine with connection pooling.

        Returns:
            AsyncEngine: SQLAlchemy async engine instance

        Note:
            Connection pooling configuration:
            - pool_size: 10 (max connections in pool)
            - max_overflow: 20 (max additional connections beyond pool_size)
            - pool_timeout: 30 seconds (wait time for connection)
            - pool_recycle: 3600 seconds (recycle connections after 1 hour)
        """
        if self._engine is None:
            # Use asyncpg driver for PostgreSQL (fastest async driver)
            database_url = self._settings.database_url

            # Convert postgresql:// to postgresql+asyncpg:// if needed
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            # Determine pooling strategy based on environment
            if self._settings.environment == "test":
                # Disable pooling for tests to avoid connection issues
                poolclass = NullPool
                pool_kwargs = {}
            else:
                # Production pooling configuration
                poolclass = QueuePool
                pool_kwargs = {
                    "pool_size": 10,  # Base connections always open
                    "max_overflow": 20,  # Additional connections when needed (20 concurrent users)
                    "pool_timeout": 30,  # Seconds to wait for connection
                    "pool_recycle": 3600,  # Recycle connections after 1 hour
                    "pool_pre_ping": True,  # Verify connection health before use
                }

            self._engine = create_async_engine(
                database_url,
                poolclass=poolclass,
                echo=self._settings.debug,  # Log SQL queries in debug mode
                future=True,  # Use SQLAlchemy 2.0 style
                **pool_kwargs
            )

        return self._engine

    async def close(self) -> None:
        """Close database engine and all connections.

        Should be called during application shutdown.
        """
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None


# Singleton instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """Get the singleton database connection instance.

    Returns:
        DatabaseConnection: Singleton database connection manager
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


async def close_db_connection() -> None:
    """Close the database connection singleton.

    Call this during application shutdown.
    """
    global _db_connection
    if _db_connection is not None:
        await _db_connection.close()
        _db_connection = None
