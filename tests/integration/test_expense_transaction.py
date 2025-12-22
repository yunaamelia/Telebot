"""Integration tests for expense transaction recording with real database (User Story 2).

Following TDD: These tests are written FIRST and should FAIL until implementation.
Uses Testcontainers to spin up real PostgreSQL for integration testing.
Tests complete expense workflow: amount validation → category selection → database persistence.
"""
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer

from src.bot.models.category import Base as CategoryBase
from src.bot.models.category import Category
from src.bot.models.transaction import Base as TransactionBase
from src.bot.models.transaction import Transaction
from src.bot.models.user import Base as UserBase
from src.bot.models.user import User
from src.bot.repositories.category_repository import CategoryRepository
from src.bot.repositories.transaction_repository import TransactionRepository
from src.bot.services.transaction_service import TransactionService


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
async def expense_categories(db_session):
    """Create all expense categories in database per data-model.md seed data."""
    categories = [
        Category(category_id=2, name="Operational", type="expense", emoji="🏢", sort_order=2),
        Category(category_id=3, name="Salaries", type="expense", emoji="👔", sort_order=3),
        Category(category_id=4, name="Supplies", type="expense", emoji="📦", sort_order=4),
        Category(category_id=5, name="Marketing", type="expense", emoji="📢", sort_order=5),
        Category(category_id=6, name="Other", type="expense", emoji="➕", sort_order=6),
    ]

    for category in categories:
        db_session.add(category)

    await db_session.commit()

    for category in categories:
        await db_session.refresh(category)

    return categories


@pytest.fixture
def transaction_repository(db_session):
    """Create transaction repository with database session."""
    return TransactionRepository(session=db_session)


@pytest.fixture
def category_repository(db_session):
    """Create category repository with database session."""
    return CategoryRepository(session=db_session)


@pytest.fixture
def transaction_service(transaction_repository, category_repository):
    """Create transaction service with real repositories."""
    return TransactionService(
        repository=transaction_repository, category_repository=category_repository
    )


class TestExpenseTransactionIntegration:
    """Integration tests for expense recording with database persistence."""

    @pytest.mark.asyncio
    async def test_record_expense_persists_to_database(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should persist expense transaction to database with correct fields."""
        # Arrange
        amount = Decimal("250000")
        category_name = "Supplies"
        description = "Office supplies purchase"

        # Act
        result = await transaction_service.record_expense(
            user=test_user,
            amount=amount,
            category_name=category_name,
            description=description,
        )

        # Assert - Verify transaction was created
        assert result.transaction_id is not None
        assert result.type == "expense"
        assert result.amount == amount
        assert result.description == description

        # Verify in database
        saved_transaction = await db_session.get(Transaction, result.transaction_id)
        assert saved_transaction is not None
        assert saved_transaction.user_id == test_user.user_id
        assert saved_transaction.amount == amount
        assert saved_transaction.type == "expense"
        assert saved_transaction.category_id == 4  # Supplies category

    @pytest.mark.asyncio
    async def test_record_expense_all_categories_persist(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should successfully persist expenses for all category types."""
        # Test data for each category
        test_cases = [
            ("Operational", Decimal("500000"), "Office rent payment"),
            ("Salaries", Decimal("1000000"), "Monthly staff salaries"),
            ("Supplies", Decimal("150000"), "Paper and ink cartridges"),
            ("Marketing", Decimal("300000"), "Facebook advertising campaign"),
            ("Other", Decimal("75000"), "Miscellaneous expenses"),
        ]

        for category_name, amount, description in test_cases:
            # Act
            result = await transaction_service.record_expense(
                user=test_user,
                amount=amount,
                category_name=category_name,
                description=description,
            )

            # Assert
            assert result.transaction_id is not None

            # Verify in database
            saved_transaction = await db_session.get(Transaction, result.transaction_id)
            assert saved_transaction is not None
            assert saved_transaction.description == description
            assert saved_transaction.amount == amount

    @pytest.mark.asyncio
    async def test_record_expense_with_default_description(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should use 'Uncategorized expense' when description is None per US2 AS5."""
        # Arrange
        amount = Decimal("100000")
        category_name = "Other"

        # Act
        result = await transaction_service.record_expense(
            user=test_user, amount=amount, category_name=category_name, description=None
        )

        # Assert
        assert result.description == "Uncategorized expense"

        # Verify in database
        saved_transaction = await db_session.get(Transaction, result.transaction_id)
        assert saved_transaction.description == "Uncategorized expense"

    @pytest.mark.asyncio
    async def test_record_expense_transaction_id_format(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should generate transaction ID in TX20251218001 format per FR-004."""
        # Arrange
        amount = Decimal("200000")
        category_name = "Supplies"

        # Act
        result = await transaction_service.record_expense(
            user=test_user,
            amount=amount,
            category_name=category_name,
            description="Test transaction",
        )

        # Assert - Verify transaction ID format
        assert result.transaction_id.startswith("TX")
        assert len(result.transaction_id) == 13  # TX + 8 digits (date) + 3 digits (sequence)

        # Extract date part (YYYYMMDD)
        date_part = result.transaction_id[2:10]
        assert len(date_part) == 8
        assert date_part.isdigit()

        # Extract sequence part (001)
        sequence_part = result.transaction_id[10:13]
        assert len(sequence_part) == 3
        assert sequence_part.isdigit()

    @pytest.mark.asyncio
    async def test_record_expense_foreign_key_relationships(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should correctly link transaction to user and category via foreign keys."""
        # Arrange
        amount = Decimal("150000")
        category_name = "Marketing"

        # Act
        result = await transaction_service.record_expense(
            user=test_user,
            amount=amount,
            category_name=category_name,
            description="Campaign expenses",
        )

        # Assert - Verify foreign key relationships
        saved_transaction = await db_session.get(Transaction, result.transaction_id)
        assert saved_transaction.user_id == test_user.user_id
        assert saved_transaction.category_id == 5  # Marketing category ID

        # Verify user relationship
        assert saved_transaction.user.telegram_id == test_user.telegram_id

        # Verify category relationship
        assert saved_transaction.category.name == "Marketing"
        assert saved_transaction.category.emoji == "📢"

    @pytest.mark.asyncio
    async def test_record_expense_duplicate_detection_query(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should detect duplicate expense within 60-second window using database query."""
        # Arrange - Create first transaction
        amount = Decimal("100000")
        category_name = "Supplies"
        description = "Duplicate test"

        first_transaction = await transaction_service.record_expense(
            user=test_user,
            amount=amount,
            category_name=category_name,
            description=description,
        )

        # Act - Check for duplicates immediately
        duplicates = await transaction_service.check_duplicate_expense(
            user=test_user,
            amount=amount,
            category_id=4,
            description=description,  # Supplies
        )

        # Assert - Should find the duplicate
        assert len(duplicates) > 0
        assert duplicates[0].transaction_id == first_transaction.transaction_id
        assert duplicates[0].amount == amount

    @pytest.mark.asyncio
    async def test_record_expense_timestamp_in_utc(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should store timestamp in UTC per data-model.md."""
        # Arrange
        amount = Decimal("100000")
        category_name = "Other"

        # Act
        result = await transaction_service.record_expense(
            user=test_user,
            amount=amount,
            category_name=category_name,
            description="Timezone test",
        )

        # Assert - Verify timestamp has timezone info (UTC)
        assert result.timestamp.tzinfo is not None

        # Verify in database
        saved_transaction = await db_session.get(Transaction, result.transaction_id)
        assert saved_transaction.timestamp.tzinfo is not None

    @pytest.mark.asyncio
    async def test_record_expense_transaction_date_computed(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should compute transaction_date from timestamp in WITA timezone."""
        # Arrange
        amount = Decimal("100000")
        category_name = "Supplies"

        # Act
        result = await transaction_service.record_expense(
            user=test_user,
            amount=amount,
            category_name=category_name,
            description="Date test",
        )

        # Assert - transaction_date should be set
        assert result.transaction_date is not None
        assert isinstance(result.transaction_date, datetime.date)

        # Verify in database
        saved_transaction = await db_session.get(Transaction, result.transaction_id)
        assert saved_transaction.transaction_date is not None

    @pytest.mark.asyncio
    async def test_record_expense_status_defaults_to_recorded(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should set transaction status to 'recorded' by default."""
        # Arrange
        amount = Decimal("100000")
        category_name = "Other"

        # Act
        result = await transaction_service.record_expense(
            user=test_user,
            amount=amount,
            category_name=category_name,
            description="Status test",
        )

        # Assert
        assert result.status == "recorded"

        # Verify in database
        saved_transaction = await db_session.get(Transaction, result.transaction_id)
        assert saved_transaction.status == "recorded"

    @pytest.mark.asyncio
    async def test_record_expense_invalid_category_raises_error(
        self, transaction_service, test_user, expense_categories
    ):
        """Should raise ValueError for non-existent category."""
        # Arrange
        amount = Decimal("100000")
        invalid_category = "NonExistentCategory"

        # Act & Assert
        with pytest.raises(ValueError, match="Category not found"):
            await transaction_service.record_expense(
                user=test_user,
                amount=amount,
                category_name=invalid_category,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_record_expense_multiple_users_isolated(
        self, transaction_service, db_session, test_user, expense_categories
    ):
        """Should correctly isolate expense transactions by user."""
        # Arrange - Create second user
        user2 = User(
            telegram_id=987654321,
            telegram_username="testuser2",
            full_name="Test User 2",
            role="staff",
            status="active",
        )
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user2)

        # Act - Record expenses for both users
        expense1 = await transaction_service.record_expense(
            user=test_user,
            amount=Decimal("100000"),
            category_name="Supplies",
            description="User 1 expense",
        )

        expense2 = await transaction_service.record_expense(
            user=user2,
            amount=Decimal("200000"),
            category_name="Supplies",
            description="User 2 expense",
        )

        # Assert - Verify isolation
        assert expense1.user_id == test_user.user_id
        assert expense2.user_id == user2.user_id
        assert expense1.transaction_id != expense2.transaction_id
