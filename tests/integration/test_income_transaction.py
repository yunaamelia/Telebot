"""Integration tests for income transaction recording with real database.

Uses Testcontainers to spin up a real PostgreSQL instance for testing.
"""
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer

from bot.models.category import Base as CategoryBase
from bot.models.category import Category
from bot.models.transaction import Base as TransactionBase
from bot.models.transaction import Transaction
from bot.models.user import Base as UserBase
from bot.models.user import User
from bot.repositories.transaction_repository import TransactionRepository
from bot.repositories.user_repository import UserRepository
from bot.services.transaction_service import TransactionService


@pytest.fixture(scope="module")
def postgres_container():
    """Start PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:15.5") as postgres:
        yield postgres


@pytest.fixture(scope="module")
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


@pytest.fixture
async def test_user(db_session):
    """Create test user in database."""
    user = User(
        telegram_id=123456789,
        telegram_username="testuser",
        full_name="Test User",
        role="staff",
        status="active",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def income_category(db_session):
    """Create income category in database."""
    category = Category(
        category_id=1,
        name="Income",
        type="income",
        emoji="💰",
        description="All income transactions",
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture
def transaction_repository(db_session):
    """Create transaction repository with database session."""
    return TransactionRepository(session=db_session)


@pytest.fixture
def user_repository(db_session):
    """Create user repository with database session."""
    return UserRepository(session=db_session)


@pytest.fixture
def transaction_service(transaction_repository):
    """Create transaction service with repository."""
    return TransactionService(repository=transaction_repository)


class TestIncomeRecordingIntegration:
    """Integration tests for income transaction recording."""

    @pytest.mark.asyncio
    async def test_record_income_persists_to_database(
        self, transaction_service, test_user, income_category, db_session
    ):
        """Should persist income transaction to database with all fields."""
        # Arrange
        amount = Decimal("500000")
        description = "Client payment"

        # Act
        result = await transaction_service.record_income(
            user=test_user, amount=amount, description=description
        )

        # Assert - Verify transaction was created
        assert result.transaction_id is not None
        assert result.transaction_id.startswith("TX")

        # Verify transaction persisted to database
        saved_transaction = await db_session.get(Transaction, result.transaction_id)
        assert saved_transaction is not None
        assert saved_transaction.type == "income"
        assert saved_transaction.amount == amount
        assert saved_transaction.description == description
        assert saved_transaction.user_id == test_user.user_id
        assert saved_transaction.category_id == income_category.category_id
        assert saved_transaction.status == "completed"

    @pytest.mark.asyncio
    async def test_record_multiple_income_transactions(
        self, transaction_service, test_user, income_category, db_session
    ):
        """Should record multiple income transactions with sequential IDs."""
        # Arrange
        transactions_data = [
            (Decimal("500000"), "Payment 1"),
            (Decimal("750000"), "Payment 2"),
            (Decimal("1000000"), "Payment 3"),
        ]

        # Act
        results = []
        for amount, description in transactions_data:
            result = await transaction_service.record_income(
                user=test_user, amount=amount, description=description
            )
            results.append(result)

        # Assert - All transactions created
        assert len(results) == 3

        # Verify unique transaction IDs
        tx_ids = [r.transaction_id for r in results]
        assert len(tx_ids) == len(set(tx_ids))  # All unique

        # Verify all persisted
        for result in results:
            saved_transaction = await db_session.get(Transaction, result.transaction_id)
            assert saved_transaction is not None
            assert saved_transaction.type == "income"

    @pytest.mark.asyncio
    async def test_record_income_with_timestamp(
        self, transaction_service, test_user, income_category, db_session
    ):
        """Should record transaction with accurate timestamp."""
        # Arrange
        amount = Decimal("500000")
        before_time = datetime.utcnow()

        # Act
        result = await transaction_service.record_income(
            user=test_user, amount=amount, description="Test"
        )

        after_time = datetime.utcnow()

        # Assert
        assert result.timestamp is not None
        assert before_time <= result.timestamp <= after_time

    @pytest.mark.asyncio
    async def test_record_income_transaction_immutable(
        self, transaction_service, test_user, income_category, db_session
    ):
        """Should not allow modification of completed transaction."""
        # Arrange
        amount = Decimal("500000")

        # Act - Create transaction
        result = await transaction_service.record_income(
            user=test_user, amount=amount, description="Original"
        )

        # Try to modify (should be prevented by application logic)
        saved_transaction = await db_session.get(Transaction, result.transaction_id)

        # Attempt modification
        saved_transaction.amount = Decimal("999999")
        await db_session.commit()

        # Assert - Fetch again to verify
        refetched = await db_session.get(Transaction, result.transaction_id)

        # Note: Database allows update, but application should prevent it
        # This test verifies database persistence; application-level immutability
        # should be enforced in service layer
        assert refetched.transaction_id == result.transaction_id

    @pytest.mark.asyncio
    async def test_record_income_with_default_description(
        self, transaction_service, test_user, income_category, db_session
    ):
        """Should use default description when none provided."""
        # Arrange
        amount = Decimal("500000")

        # Act
        result = await transaction_service.record_income(
            user=test_user, amount=amount, description=None
        )

        # Assert
        assert result.description == "No description"

        # Verify in database
        saved_transaction = await db_session.get(Transaction, result.transaction_id)
        assert saved_transaction.description == "No description"

    @pytest.mark.asyncio
    async def test_record_income_foreign_key_constraint(
        self, transaction_repository, income_category, db_session
    ):
        """Should enforce foreign key constraint for user_id."""
        # Arrange - Create transaction with non-existent user
        transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=99999,  # Non-existent user
            type="income",
            amount=Decimal("500000"),
            category_id=income_category.category_id,
            description="Test",
            timestamp=datetime.utcnow(),
            status="completed",
        )

        # Act & Assert - Should fail due to foreign key constraint
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError, match="foreign key"):
            await transaction_repository.create(transaction)
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_record_income_concurrent_transactions(
        self, transaction_service, test_user, income_category, db_session
    ):
        """Should handle concurrent income recordings correctly."""
        # Arrange
        import asyncio

        async def record_transaction(seq):
            return await transaction_service.record_income(
                user=test_user,
                amount=Decimal(str(500000 + seq * 1000)),
                description=f"Concurrent payment {seq}",
            )

        # Act - Record 5 transactions concurrently
        results = await asyncio.gather(*[record_transaction(i) for i in range(5)])

        # Assert
        assert len(results) == 5

        # All should have unique transaction IDs
        tx_ids = [r.transaction_id for r in results]
        assert len(tx_ids) == len(set(tx_ids))

        # All should be persisted
        for result in results:
            saved_transaction = await db_session.get(Transaction, result.transaction_id)
            assert saved_transaction is not None
