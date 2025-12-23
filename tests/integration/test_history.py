"""Integration tests for transaction history retrieval.

Tests T108: Integration test for history retrieval with real database.
Uses Testcontainers for real PostgreSQL instance.
"""
from datetime import date
from datetime import datetime
from decimal import Decimal

import pytest

from src.bot.repositories.transaction_repository import TransactionRepository
from src.bot.services.transaction_service import TransactionService


@pytest.fixture
def transaction_repository(db_session):
    """Create transaction repository with database session."""
    return TransactionRepository(session=db_session)


@pytest.fixture
def transaction_service(transaction_repository):
    """Create transaction service with repository."""
    return TransactionService(repository=transaction_repository)


class TestHistoryRetrievalIntegration:
    """Integration tests for transaction history with pagination and filtering."""

    @pytest.mark.asyncio
    async def test_get_history_with_pagination(
        self,
        transaction_service,
        test_user,
        income_category,
        expense_category,
        db_session,
    ):
        """Should retrieve transaction history with correct pagination."""
        # Arrange - Create 15 transactions
        for i in range(15):
            if i % 2 == 0:
                await transaction_service.record_income(
                    user=test_user,
                    amount=Decimal(str(100000 + i * 10000)),
                    description=f"Income transaction {i + 1}",
                )
            else:
                await transaction_service.record_expense(
                    user=test_user,
                    amount=Decimal(str(50000 + i * 5000)),
                    description=f"Expense transaction {i + 1}",
                    category_id=expense_category.category_id,
                )
        await db_session.commit()

        # Create repository
        repo = TransactionRepository(db_session)

        # Act - Get first page (10 items)
        page1_transactions, total_count = await repo.get_history(
            user_id=test_user.user_id, limit=10, offset=0
        )

        # Assert page 1
        assert len(page1_transactions) == 10
        assert total_count == 15

        # Act - Get second page (5 items)
        page2_transactions, _ = await repo.get_history(
            user_id=test_user.user_id, limit=10, offset=10
        )

        # Assert page 2
        assert len(page2_transactions) == 5
        assert total_count == 15

        # Verify no overlap between pages
        page1_ids = {t.transaction_id for t in page1_transactions}
        page2_ids = {t.transaction_id for t in page2_transactions}
        assert len(page1_ids & page2_ids) == 0

    @pytest.mark.asyncio
    async def test_history_sorted_by_timestamp_desc(
        self, transaction_service, test_user, income_category, db_session
    ):
        """Should return history sorted by timestamp descending (most recent first)."""
        # Arrange - Create transactions with specific timestamps
        timestamps = [
            datetime(2025, 12, 18, 10, 0, 0),
            datetime(2025, 12, 18, 14, 30, 0),
            datetime(2025, 12, 18, 12, 15, 0),
        ]

        for _i, ts in enumerate(timestamps):
            # Manually set timestamp for testing
            tx = await transaction_service.record_income(
                user=test_user,
                amount=Decimal("100000"),
                description=f"Transaction at {ts.strftime('%H:%M')}",
            )
            tx.timestamp = ts
        await db_session.commit()

        # Create repository
        repo = TransactionRepository(db_session)

        # Act
        transactions, _ = await repo.get_history(user_id=test_user.user_id, limit=10, offset=0)

        # Assert - Should be in DESC order (14:30, 12:15, 10:00)
        assert len(transactions) == 3
        assert transactions[0].timestamp.hour == 14
        assert transactions[1].timestamp.hour == 12
        assert transactions[2].timestamp.hour == 10

    @pytest.mark.asyncio
    async def test_get_by_date_range_single_date(
        self, transaction_service, test_user, income_category, db_session
    ):
        """Should filter transactions by specific date."""
        # Arrange - Create transactions on different dates
        target_date = date(2025, 12, 18)
        other_date = date(2025, 12, 17)

        # Transactions on target date
        for i in range(3):
            tx = await transaction_service.record_income(
                user=test_user,
                amount=Decimal("100000"),
                description=f"Target date transaction {i + 1}",
            )
            tx.transaction_date = target_date

        # Transactions on other date
        for i in range(2):
            tx = await transaction_service.record_income(
                user=test_user,
                amount=Decimal("50000"),
                description=f"Other date transaction {i + 1}",
            )
            tx.transaction_date = other_date

        await db_session.commit()

        # Create repository
        repo = TransactionRepository(db_session)

        # Act
        transactions = await repo.get_by_date_range(
            start_date=target_date, end_date=target_date, user_id=test_user.user_id
        )

        # Assert
        assert len(transactions) == 3
        assert all(t.transaction_date == target_date for t in transactions)

    @pytest.mark.asyncio
    async def test_get_by_date_range_multiple_days(
        self, transaction_service, test_user, income_category, db_session
    ):
        """Should filter transactions by date range."""
        # Arrange - Create transactions across multiple dates
        dates = [
            date(2025, 12, 15),
            date(2025, 12, 16),
            date(2025, 12, 17),
            date(2025, 12, 18),
        ]

        for target_date in dates:
            tx = await transaction_service.record_income(
                user=test_user,
                amount=Decimal("100000"),
                description=f"Transaction on {target_date.isoformat()}",
            )
            tx.transaction_date = target_date

        await db_session.commit()

        # Create repository
        repo = TransactionRepository(db_session)

        # Act - Get transactions from 12/16 to 12/17
        transactions = await repo.get_by_date_range(
            start_date=date(2025, 12, 16),
            end_date=date(2025, 12, 17),
            user_id=test_user.user_id,
        )

        # Assert
        assert len(transactions) == 2
        assert all(
            date(2025, 12, 16) <= t.transaction_date <= date(2025, 12, 17) for t in transactions
        )

    @pytest.mark.asyncio
    async def test_filter_by_category(
        self, transaction_service, test_user, expense_category, db_session
    ):
        """Should filter transactions by category."""
        # Arrange - Create transactions in different categories
        # Get Operational category (should be seeded)
        from src.bot.repositories.category_repository import CategoryRepository

        cat_repo = CategoryRepository(db_session)
        operational_cat = await cat_repo.get_by_name("Operational")
        supplies_cat = await cat_repo.get_by_name("Supplies")

        # Create expenses in different categories
        for i in range(3):
            await transaction_service.record_expense(
                user=test_user,
                amount=Decimal("100000"),
                description=f"Operational expense {i + 1}",
                category_id=operational_cat.category_id,
            )

        for i in range(2):
            await transaction_service.record_expense(
                user=test_user,
                amount=Decimal("50000"),
                description=f"Supplies expense {i + 1}",
                category_id=supplies_cat.category_id,
            )

        await db_session.commit()

        # Create repository
        repo = TransactionRepository(db_session)

        # Act - Filter by Operational category
        today = date.today()
        transactions = await repo.get_by_date_range(
            start_date=today,
            end_date=today,
            user_id=test_user.user_id,
            category_id=operational_cat.category_id,
        )

        # Assert
        assert len(transactions) == 3
        assert all(t.category_id == operational_cat.category_id for t in transactions)

    @pytest.mark.asyncio
    async def test_filter_by_transaction_type(
        self,
        transaction_service,
        test_user,
        income_category,
        expense_category,
        db_session,
    ):
        """Should filter transactions by type (income/expense)."""
        # Arrange - Create both income and expense transactions
        for i in range(3):
            await transaction_service.record_income(
                user=test_user,
                amount=Decimal("200000"),
                description=f"Income {i + 1}",
            )

        for i in range(4):
            await transaction_service.record_expense(
                user=test_user,
                amount=Decimal("100000"),
                description=f"Expense {i + 1}",
                category_id=expense_category.category_id,
            )

        await db_session.commit()

        # Create repository
        repo = TransactionRepository(db_session)

        # Act - Filter by income type
        today = date.today()
        income_txs = await repo.get_by_date_range(
            start_date=today,
            end_date=today,
            user_id=test_user.user_id,
            transaction_type="income",
        )

        expense_txs = await repo.get_by_date_range(
            start_date=today,
            end_date=today,
            user_id=test_user.user_id,
            transaction_type="expense",
        )

        # Assert
        assert len(income_txs) == 3
        assert all(t.type == "income" for t in income_txs)

        assert len(expense_txs) == 4
        assert all(t.type == "expense" for t in expense_txs)

    @pytest.mark.asyncio
    async def test_empty_history(self, test_user, db_session):
        """Should return empty list when no transactions exist."""
        # Arrange
        repo = TransactionRepository(db_session)

        # Act
        transactions, total = await repo.get_history(user_id=test_user.user_id, limit=10, offset=0)

        # Assert
        assert len(transactions) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_combined_filters(
        self, transaction_service, test_user, expense_category, db_session
    ):
        """Should apply multiple filters simultaneously."""
        # Arrange
        from src.bot.repositories.category_repository import CategoryRepository

        cat_repo = CategoryRepository(db_session)
        supplies_cat = await cat_repo.get_by_name("Supplies")

        target_date = date(2025, 12, 18)

        # Create various transactions
        # 1. Supplies expense on target date (MATCH)
        tx1 = await transaction_service.record_expense(
            user=test_user,
            amount=Decimal("100000"),
            description="Target supplies",
            category_id=supplies_cat.category_id,
        )
        tx1.transaction_date = target_date

        # 2. Other category expense on target date (NO MATCH - wrong category)
        tx2 = await transaction_service.record_expense(
            user=test_user,
            amount=Decimal("50000"),
            description="Other expense",
            category_id=expense_category.category_id,
        )
        tx2.transaction_date = target_date

        # 3. Supplies expense on different date (NO MATCH - wrong date)
        tx3 = await transaction_service.record_expense(
            user=test_user,
            amount=Decimal("75000"),
            description="Different date supplies",
            category_id=supplies_cat.category_id,
        )
        tx3.transaction_date = date(2025, 12, 17)

        await db_session.commit()

        # Create repository
        repo = TransactionRepository(db_session)

        # Act - Filter by date, category, and type
        transactions = await repo.get_by_date_range(
            start_date=target_date,
            end_date=target_date,
            user_id=test_user.user_id,
            category_id=supplies_cat.category_id,
            transaction_type="expense",
        )

        # Assert - Should only get tx1
        assert len(transactions) == 1
        assert transactions[0].transaction_id == tx1.transaction_id
