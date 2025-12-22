"""Unit tests for expense transaction recording (User Story 2).

Following TDD: These tests are written FIRST and should FAIL until implementation.
Tests the record_expense method with category selection logic.
"""

from datetime import date
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from bot.models.category import Category
from bot.models.transaction import Transaction
from bot.models.user import User
from bot.repositories.category_repository import CategoryRepository
from bot.repositories.transaction_repository import TransactionRepository
from bot.services.transaction_service import TransactionService
from bot.utils.validators import AmountValidationError


@pytest.fixture
def mock_transaction_repository():
    """Create mock transaction repository."""
    repository = Mock(spec=TransactionRepository)
    repository.create = AsyncMock()
    repository.find_duplicates = AsyncMock(return_value=[])
    repository.get_daily_sequence = AsyncMock(return_value=1)
    return repository


@pytest.fixture
def mock_category_repository():
    """Create mock category repository."""
    repository = Mock(spec=CategoryRepository)
    repository.get_by_name = AsyncMock()
    repository.get_expense_categories = AsyncMock()
    return repository


@pytest.fixture
def transaction_service(mock_transaction_repository, mock_category_repository):
    """Create transaction service with mocked repositories."""
    return TransactionService(
        repository=mock_transaction_repository,
        category_repository=mock_category_repository,
    )


@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    return User(
        user_id=1,
        telegram_id=123456789,
        telegram_username="testuser",
        full_name="Test User",
        role="staff",
        status="active",
    )


@pytest.fixture
def expense_categories():
    """Create sample expense categories."""
    return [
        Category(
            category_id=2, name="Operational", type="expense", emoji="🏢", sort_order=2
        ),
        Category(
            category_id=3, name="Salaries", type="expense", emoji="👔", sort_order=3
        ),
        Category(
            category_id=4, name="Supplies", type="expense", emoji="📦", sort_order=4
        ),
        Category(
            category_id=5, name="Marketing", type="expense", emoji="📢", sort_order=5
        ),
        Category(category_id=6, name="Other", type="expense", emoji="➕", sort_order=6),
    ]


class TestRecordExpense:
    """Test expense transaction recording with category selection."""

    @pytest.mark.asyncio
    async def test_record_expense_with_valid_category(
        self,
        transaction_service,
        mock_transaction_repository,
        mock_category_repository,
        sample_user,
        expense_categories,
    ):
        """Should successfully record expense with valid category name."""
        # Arrange
        amount = Decimal("250000")
        description = "Office supplies purchase"
        category_name = "Supplies"

        supplies_category = expense_categories[2]  # Supplies category
        mock_category_repository.get_by_name.return_value = supplies_category

        expected_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="expense",
            amount=amount,
            category_id=supplies_category.category_id,
            description=description,
            timestamp=datetime.now(),
            status="recorded",
        )
        mock_transaction_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_expense(
            user=sample_user,
            amount=amount,
            category_name=category_name,
            description=description,
        )

        # Assert
        assert result.type == "expense"
        assert result.amount == amount
        assert result.description == description
        assert result.category_id == supplies_category.category_id
        assert result.user_id == sample_user.user_id
        mock_category_repository.get_by_name.assert_called_once_with(category_name)
        mock_transaction_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_expense_default_description(
        self,
        transaction_service,
        mock_transaction_repository,
        mock_category_repository,
        sample_user,
        expense_categories,
    ):
        """Should use 'Uncategorized expense' as default description per US2 AS5."""
        # Arrange
        amount = Decimal("100000")
        category_name = "Other"

        other_category = expense_categories[4]  # Other category
        mock_category_repository.get_by_name.return_value = other_category

        expected_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="expense",
            amount=amount,
            category_id=other_category.category_id,
            description="Uncategorized expense",
            timestamp=datetime.now(),
            status="recorded",
        )
        mock_transaction_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_expense(
            user=sample_user,
            amount=amount,
            category_name=category_name,
            description=None,  # No description provided
        )

        # Assert
        assert result.description == "Uncategorized expense"
        mock_transaction_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_expense_all_expense_categories(
        self,
        transaction_service,
        mock_transaction_repository,
        mock_category_repository,
        sample_user,
        expense_categories,
    ):
        """Should successfully record expenses for all category types."""
        # Test all expense categories: Operational, Salaries, Supplies, Marketing, Other
        category_tests = [
            ("Operational", expense_categories[0], "Office rent"),
            ("Salaries", expense_categories[1], "Monthly salaries"),
            ("Supplies", expense_categories[2], "Office supplies"),
            ("Marketing", expense_categories[3], "Facebook ads"),
            ("Other", expense_categories[4], "Miscellaneous"),
        ]

        for category_name, category_obj, description in category_tests:
            # Arrange
            amount = Decimal("500000")
            mock_category_repository.get_by_name.return_value = category_obj

            expected_transaction = Transaction(
                transaction_id="TX20251218001",
                user_id=sample_user.user_id,
                type="expense",
                amount=amount,
                category_id=category_obj.category_id,
                description=description,
                timestamp=datetime.now(),
                status="recorded",
            )
            mock_transaction_repository.create.return_value = expected_transaction

            # Act
            result = await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_name=category_name,
                description=description,
            )

            # Assert
            assert result.type == "expense"
            assert result.category_id == category_obj.category_id
            assert result.description == description

    @pytest.mark.asyncio
    async def test_record_expense_invalid_amount_zero(
        self, transaction_service, sample_user
    ):
        """Should raise AmountValidationError for zero amount."""
        # Arrange
        amount = Decimal("0")
        category_name = "Supplies"

        # Act & Assert
        with pytest.raises(
            AmountValidationError, match="Amount must be greater than 0"
        ):
            await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_name=category_name,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_record_expense_invalid_amount_negative(
        self, transaction_service, sample_user
    ):
        """Should raise AmountValidationError for negative amount."""
        # Arrange
        amount = Decimal("-100000")
        category_name = "Supplies"

        # Act & Assert
        with pytest.raises(
            AmountValidationError, match="Amount must be greater than 0"
        ):
            await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_name=category_name,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_record_expense_amount_exceeds_maximum(
        self, transaction_service, sample_user
    ):
        """Should raise AmountValidationError when amount exceeds Rp 10 billion per FR-022."""
        # Arrange
        amount = Decimal("10000000001")  # 10 billion + 1
        category_name = "Supplies"

        # Act & Assert
        with pytest.raises(AmountValidationError, match="Amount exceeds maximum limit"):
            await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_name=category_name,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_record_expense_invalid_category(
        self, transaction_service, mock_category_repository, sample_user
    ):
        """Should raise ValueError for invalid/non-existent category."""
        # Arrange
        amount = Decimal("100000")
        invalid_category = "InvalidCategory"
        mock_category_repository.get_by_name.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Category not found"):
            await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_name=invalid_category,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_record_expense_duplicate_detection(
        self,
        transaction_service,
        mock_transaction_repository,
        mock_category_repository,
        sample_user,
        expense_categories,
    ):
        """Should detect duplicate expense within 60-second window per FR-023."""
        # Arrange
        amount = Decimal("150000")
        category_name = "Supplies"
        description = "Paper and ink"

        supplies_category = expense_categories[2]
        mock_category_repository.get_by_name.return_value = supplies_category

        # Mock finding a duplicate transaction
        duplicate_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="expense",
            amount=amount,
            category_id=supplies_category.category_id,
            description=description,
            timestamp=datetime.now(),
            status="recorded",
        )
        mock_transaction_repository.find_duplicates.return_value = [
            duplicate_transaction
        ]

        # Act
        duplicates = await transaction_service.check_duplicate_expense(
            user=sample_user,
            amount=amount,
            category_id=supplies_category.category_id,
            description=description,
        )

        # Assert
        assert len(duplicates) > 0
        assert duplicates[0].amount == amount
        assert duplicates[0].description == description
        mock_transaction_repository.find_duplicates.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_expense_with_duplicate_confirmation(
        self,
        transaction_service,
        mock_transaction_repository,
        mock_category_repository,
        sample_user,
        expense_categories,
    ):
        """Should record expense with is_duplicate_confirmed=True when user confirms duplicate."""
        # Arrange
        amount = Decimal("150000")
        category_name = "Supplies"
        description = "Paper and ink"

        supplies_category = expense_categories[2]
        mock_category_repository.get_by_name.return_value = supplies_category

        expected_transaction = Transaction(
            transaction_id="TX20251218002",
            user_id=sample_user.user_id,
            type="expense",
            amount=amount,
            category_id=supplies_category.category_id,
            description=description,
            timestamp=datetime.now(),
            status="recorded",
            is_duplicate_confirmed=True,
        )
        mock_transaction_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_expense(
            user=sample_user,
            amount=amount,
            category_name=category_name,
            description=description,
            is_duplicate_confirmed=True,
        )

        # Assert
        assert result.is_duplicate_confirmed is True
        mock_transaction_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_expense_generates_correct_transaction_id(
        self,
        transaction_service,
        mock_transaction_repository,
        mock_category_repository,
        sample_user,
        expense_categories,
    ):
        """Should generate transaction ID in TX20251218001 format per FR-004."""
        # Arrange
        amount = Decimal("100000")
        category_name = "Other"

        other_category = expense_categories[4]
        mock_category_repository.get_by_name.return_value = other_category

        mock_transaction_repository.get_daily_sequence.return_value = 5

        with patch("bot.services.transaction_service.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 18, 10, 30, 0)

            expected_transaction = Transaction(
                transaction_id="TX20251218005",  # Sequence 5
                user_id=sample_user.user_id,
                type="expense",
                amount=amount,
                category_id=other_category.category_id,
                description="Test",
                timestamp=datetime(2025, 12, 18, 10, 30, 0),
                status="recorded",
            )
            mock_transaction_repository.create.return_value = expected_transaction

            # Act
            result = await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_name=category_name,
                description="Test",
            )

            # Assert
            assert result.transaction_id == "TX20251218005"
            assert result.transaction_id.startswith("TX20251218")
