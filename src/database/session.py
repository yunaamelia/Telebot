"""SQLAlchemy async session factory and database base class.

This module provides async session management using SQLAlchemy's async session
factory pattern with proper context management.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.database.connection import get_db_connection


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    All model classes should inherit from this base.
    """

    pass


# Global session factory (initialized once)
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory.

    Returns:
        async_sessionmaker: Factory for creating async database sessions

    Note:
        Session configuration:
        - expire_on_commit=False: Allows accessing objects after commit
        - autoflush=True: Auto-flush before queries
        - autocommit=False: Explicit transaction control
    """
    global _session_factory

    if _session_factory is None:
        engine = get_db_connection().get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Allow object access after commit
            autoflush=True,  # Automatically flush before queries
            autocommit=False,  # Explicit transaction control
        )

    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session with automatic cleanup.

    Yields:
        AsyncSession: SQLAlchemy async session instance

    Example:
        ```python
        async with get_db_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
        ```

    Note:
        - Automatically commits on successful completion
        - Automatically rolls back on exception
        - Ensures session is closed after use
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Initialize database by creating all tables.

    This should only be used in development/testing.
    In production, use Alembic migrations instead.

    Warning:
        This will create tables but won't handle schema changes.
        Use `alembic upgrade head` for production deployments.
    """
    from src.database.connection import get_db_connection

    engine = get_db_connection().get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
