"""Unit tests for TransactionRepository pagination and filtering.

Tests for:
- T106: Pagination logic
- T107: Date filtering
"""
from datetime import date
from datetime import datetime
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.models.transaction import Transaction
from src.bot.repositories.transaction_repository import TransactionRepository


class TestTransactionRepositoryPagination:
    """Test pagination logic per T106."""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create repository instance."""
        return TransactionRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_history_returns_correct_limit(self, repository, mock_session):
        """Test that get_history respects limit parameter."""
        # Arrange
        mock_transactions = [
            MagicMock(spec=Transaction, transaction_id=f"TX202512180{i:02d}") for i in range(1, 11)
        ]

        # Mock the count query
        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 25

        # Mock the data query
        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = mock_transactions[:10]

        mock_session.execute.side_effect = [count_mock, data_mock]

        # Act
        transactions, total = await repository.get_history(limit=10, offset=0)

        # Assert
        assert len(transactions) == 10
        assert total == 25
        assert transactions[0].transaction_id == "TX20251218001"

    @pytest.mark.asyncio
    async def test_get_history_pagination_offset(self, repository, mock_session):
        """Test that offset works correctly for pagination."""
        # Arrange
        mock_transactions_page2 = [
            MagicMock(spec=Transaction, transaction_id=f"TX202512180{i:02d}") for i in range(11, 21)
        ]

        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 25

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = mock_transactions_page2

        mock_session.execute.side_effect = [count_mock, data_mock]

        # Act
        transactions, total = await repository.get_history(limit=10, offset=10)

        # Assert
        assert len(transactions) == 10
        assert total == 25
        assert transactions[0].transaction_id == "TX20251218011"

    @pytest.mark.asyncio
    async def test_get_history_empty_results(self, repository, mock_session):
        """Test get_history with no transactions."""
        # Arrange
        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 0

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [count_mock, data_mock]

        # Act
        transactions, total = await repository.get_history(limit=10, offset=0)

        # Assert
        assert len(transactions) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_history_last_page_partial(self, repository, mock_session):
        """Test pagination when last page has fewer items than limit."""
        # Arrange
        mock_transactions = [
            MagicMock(spec=Transaction, transaction_id=f"TX202512180{i:02d}") for i in range(21, 26)
        ]

        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 25

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = mock_transactions

        mock_session.execute.side_effect = [count_mock, data_mock]

        # Act
        transactions, total = await repository.get_history(limit=10, offset=20)

        # Assert
        assert len(transactions) == 5
        assert total == 25

    @pytest.mark.asyncio
    async def test_get_history_with_user_filter(self, repository, mock_session):
        """Test get_history filters by user_id correctly."""
        # Arrange
        user_id = 5
        mock_transactions = [
            MagicMock(spec=Transaction, user_id=user_id, transaction_id=f"TX202512180{i:02d}")
            for i in range(1, 6)
        ]

        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 5

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = mock_transactions

        mock_session.execute.side_effect = [count_mock, data_mock]

        # Act
        transactions, total = await repository.get_history(user_id=user_id, limit=10, offset=0)

        # Assert
        assert len(transactions) == 5
        assert total == 5
        assert all(t.user_id == user_id for t in transactions)


class TestTransactionRepositoryDateFiltering:
    """Test date filtering logic per T107."""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def repository(self, mock_session):
        """Create repository instance."""
        return TransactionRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_date_range_single_day(self, repository, mock_session):
        """Test filtering by single date."""
        # Arrange
        target_date = date(2025, 12, 18)
        mock_transactions = [
            MagicMock(
                spec=Transaction,
                transaction_date=target_date,
                transaction_id=f"TX202512180{i:02d}",
            )
            for i in range(1, 6)
        ]

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = mock_transactions
        mock_session.execute.return_value = data_mock

        # Act
        transactions = await repository.get_by_date_range(
            start_date=target_date, end_date=target_date
        )

        # Assert
        assert len(transactions) == 5
        assert all(t.transaction_date == target_date for t in transactions)

    @pytest.mark.asyncio
    async def test_get_by_date_range_multiple_days(self, repository, mock_session):
        """Test filtering by date range."""
        # Arrange
        start_date = date(2025, 12, 15)
        end_date = date(2025, 12, 18)
        mock_transactions = [
            MagicMock(
                spec=Transaction,
                transaction_date=date(2025, 12, 15 + i),
                transaction_id=f"TX2025121{15 + i}001",
            )
            for i in range(4)
        ]

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = mock_transactions
        mock_session.execute.return_value = data_mock

        # Act
        transactions = await repository.get_by_date_range(start_date=start_date, end_date=end_date)

        # Assert
        assert len(transactions) == 4
        assert transactions[0].transaction_date >= start_date
        assert transactions[-1].transaction_date <= end_date

    @pytest.mark.asyncio
    async def test_get_by_date_range_with_category_filter(self, repository, mock_session):
        """Test date range with category filter."""
        # Arrange
        target_date = date(2025, 12, 18)
        category_id = 3  # Supplies
        mock_transactions = [
            MagicMock(
                spec=Transaction,
                transaction_date=target_date,
                category_id=category_id,
                transaction_id=f"TX202512180{i:02d}",
            )
            for i in range(1, 4)
        ]

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = mock_transactions
        mock_session.execute.return_value = data_mock

        # Act
        transactions = await repository.get_by_date_range(
            start_date=target_date, end_date=target_date, category_id=category_id
        )

        # Assert
        assert len(transactions) == 3
        assert all(t.category_id == category_id for t in transactions)

    @pytest.mark.asyncio
    async def test_get_by_date_range_with_type_filter(self, repository, mock_session):
        """Test date range with transaction type filter."""
        # Arrange
        target_date = date(2025, 12, 18)
        transaction_type = "expense"
        mock_transactions = [
            MagicMock(
                spec=Transaction,
                transaction_date=target_date,
                type=transaction_type,
                transaction_id=f"TX202512180{i:02d}",
            )
            for i in range(1, 6)
        ]

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = mock_transactions
        mock_session.execute.return_value = data_mock

        # Act
        transactions = await repository.get_by_date_range(
            start_date=target_date,
            end_date=target_date,
            transaction_type=transaction_type,
        )

        # Assert
        assert len(transactions) == 5
        assert all(t.type == transaction_type for t in transactions)

    @pytest.mark.asyncio
    async def test_get_by_date_range_no_results(self, repository, mock_session):
        """Test date range with no matching transactions."""
        # Arrange
        target_date = date(2025, 12, 18)

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = data_mock

        # Act
        transactions = await repository.get_by_date_range(
            start_date=target_date, end_date=target_date
        )

        # Assert
        assert len(transactions) == 0

    @pytest.mark.asyncio
    async def test_get_by_date_range_sorted_desc(self, repository, mock_session):
        """Test that results are sorted by timestamp DESC (most recent first)."""
        # Arrange
        target_date = date(2025, 12, 18)
        mock_transactions = [
            MagicMock(
                spec=Transaction,
                transaction_date=target_date,
                timestamp=datetime(2025, 12, 18, 15, 0, 0),
                transaction_id="TX20251218003",
            ),
            MagicMock(
                spec=Transaction,
                transaction_date=target_date,
                timestamp=datetime(2025, 12, 18, 14, 0, 0),
                transaction_id="TX20251218002",
            ),
            MagicMock(
                spec=Transaction,
                transaction_date=target_date,
                timestamp=datetime(2025, 12, 18, 13, 0, 0),
                transaction_id="TX20251218001",
            ),
        ]

        data_mock = MagicMock()
        data_mock.scalars.return_value.all.return_value = mock_transactions
        mock_session.execute.return_value = data_mock

        # Act
        transactions = await repository.get_by_date_range(
            start_date=target_date, end_date=target_date
        )

        # Assert
        assert len(transactions) == 3
        # Most recent first (15:00 > 14:00 > 13:00)
        assert transactions[0].transaction_id == "TX20251218003"
        assert transactions[1].transaction_id == "TX20251218002"
        assert transactions[2].transaction_id == "TX20251218001"
