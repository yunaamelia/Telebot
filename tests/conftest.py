"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer

from src.bot.models.category import Base as CategoryBase
from src.bot.models.category import Category
from src.bot.models.transaction import Base as TransactionBase
from src.bot.models.user import Base as UserBase
from src.bot.models.user import User


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:15.5") as postgres:
        yield postgres


@pytest.fixture(scope="session")
async def async_engine(postgres_container):
    """Create async database engine connected to test container."""
    connection_url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
    engine = create_async_engine(connection_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(TransactionBase.metadata.create_all)
        await conn.run_sync(CategoryBase.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    """Create database session for each test."""
    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="session")
async def test_user(async_engine):
    """Create test user in database."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if user exists
        result = await session.execute(select(User).where(User.telegram_id == 123456789))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=123456789,
                telegram_username="testuser",
                display_name="Test User",
                role="staff",
                status="approved",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user


@pytest.fixture(scope="session")
async def income_category(async_engine):
    """Create income category in database."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if category exists
        result = await session.execute(select(Category).where(Category.name == "Income"))
        category = result.scalar_one_or_none()

        if not category:
            category = Category(
                category_id=1,
                name="Income",
                type="income",
                emoji="💰",
                sort_order=1,
            )
            session.add(category)
            await session.commit()
            await session.refresh(category)

        return category


@pytest.fixture(autouse=True)
async def cleanup_transactions(db_session):
    """Clean up transactions before and after each test to prevent IntegrityError."""
    from src.bot.models.transaction import Transaction
    from sqlalchemy import delete
    from sqlalchemy.exc import PendingRollbackError

    async def _clean():
        try:
            # Delete transactions using TRUNCATE for speed and certainty
            from sqlalchemy import text

            await db_session.execute(text("TRUNCATE TABLE transactions RESTART IDENTITY CASCADE"))
            await db_session.commit()

            # Verify empty
            from sqlalchemy import select, func

            count = await db_session.execute(select(func.count(Transaction.transaction_id)))
            if count.scalar_one() > 0:
                print("WARNING: Cleanup failed, transactions still exist")
        except PendingRollbackError:
            await db_session.rollback()
            await db_session.execute(delete(Transaction))
            await db_session.commit()
        except Exception as e:
            print(f"Cleanup failed: {e}")
            await db_session.rollback()
            raise

    # Clean before test
    await _clean()

    # Yield control to the test
    yield

    # Clean after test
    await _clean()
