"""Unit tests for expense transaction recording (User Story 2).

Following TDD: These tests are written FIRST and should FAIL until implementation.
Tests the record_expense method with category selection logic.
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.bot.models.category import Category
from src.bot.models.transaction import Transaction
from src.bot.models.user import User
from src.bot.repositories.category_repository import CategoryRepository
from src.bot.repositories.transaction_repository import TransactionRepository
from src.bot.services.transaction_service import TransactionService
from src.bot.utils.validators import AmountValidationError


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
def transaction_service(mock_transaction_repository):
    """Create transaction service with mocked repository."""
    return TransactionService(
        repository=mock_transaction_repository,
    )


@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    return User(
        user_id=1,
        telegram_id=123456789,
        telegram_username="testuser",
        display_name="Test User",
        role="staff",
        status="approved",
    )


@pytest.fixture
def expense_categories():
    """Create sample expense categories."""
    return [
        Category(category_id=2, name="Operational", type="expense", emoji="🏢", sort_order=2),
        Category(category_id=3, name="Salaries", type="expense", emoji="👔", sort_order=3),
        Category(category_id=4, name="Supplies", type="expense", emoji="📦", sort_order=4),
        Category(category_id=5, name="Marketing", type="expense", emoji="📢", sort_order=5),
        Category(category_id=6, name="Other", type="expense", emoji="➕", sort_order=6),
    ]


class TestRecordExpense:
    """Test expense transaction recording (ID-based)."""

    @pytest.mark.asyncio
    async def test_record_expense_with_valid_category(
        self,
        transaction_service,
        mock_transaction_repository,
        sample_user,
        expense_categories,
    ):
        """Should successfully record expense with valid category ID."""
        # Arrange
        amount = Decimal("250000")
        description = "Office supplies purchase"
        # Use existing category object from fixture
        supplies_category = expense_categories[2]  # Supplies (ID 4)
        category_id = supplies_category.category_id

        expected_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="expense",
            amount=amount,
            category_id=category_id,
            description=description,
            timestamp=datetime.now(),
            status="recorded",
        )
        mock_transaction_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_expense(
            user=sample_user,
            amount=amount,
            category_id=category_id,
            description=description,
        )

        # Assert
        assert result.type == "expense"
        assert result.amount == amount
        assert result.description == description
        assert result.category_id == category_id
        assert result.user_id == sample_user.user_id
        mock_transaction_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_expense_default_description(
        self,
        transaction_service,
        mock_transaction_repository,
        sample_user,
        expense_categories,
    ):
        """Should use 'Uncategorized expense' as default description per US2 AS5."""
        # Arrange
        amount = Decimal("100000")
        other_category = expense_categories[4]  # Other (ID 6)
        category_id = other_category.category_id

        expected_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="expense",
            amount=amount,
            category_id=category_id,
            description="Uncategorized expense",
            timestamp=datetime.now(),
            status="recorded",
        )
        mock_transaction_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_expense(
            user=sample_user,
            amount=amount,
            category_id=category_id,
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
        sample_user,
        expense_categories,
    ):
        """Should successfully record expenses for all category types."""
        # Test all expense categories: Operational, Salaries, Supplies, Marketing, Other
        category_tests = [
            (expense_categories[0], "Office rent"),
            (expense_categories[1], "Monthly salaries"),
            (expense_categories[2], "Office supplies"),
            (expense_categories[3], "Facebook ads"),
            (expense_categories[4], "Miscellaneous"),
        ]

        for category_obj, description in category_tests:
            # Arrange
            amount = Decimal("500000")

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
                category_id=category_obj.category_id,
                description=description,
            )

            # Assert
            assert result.type == "expense"
            assert result.category_id == category_obj.category_id
            assert result.description == description

    @pytest.mark.asyncio
    async def test_record_expense_invalid_amount_zero(self, transaction_service, sample_user):
        """Should raise AmountValidationError for zero amount."""
        # Arrange
        amount = Decimal("0")
        category_id = 4  # Valid ID

        # Act & Assert
        with pytest.raises(AmountValidationError, match="Amount must be greater than 0"):
            await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_id=category_id,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_record_expense_invalid_amount_negative(self, transaction_service, sample_user):
        """Should raise AmountValidationError for negative amount."""
        # Arrange
        amount = Decimal("-100000")
        category_id = 4

        # Act & Assert
        with pytest.raises(AmountValidationError, match="Amount must be greater than 0"):
            await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_id=category_id,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_record_expense_amount_exceeds_maximum(self, transaction_service, sample_user):
        """Should raise AmountValidationError when amount exceeds Rp 10 billion per FR-022."""
        # Arrange
        amount = Decimal("10000000001")  # 10 billion + 1
        category_id = 4

        # Act & Assert
        with pytest.raises(AmountValidationError, match="Amount exceeds maximum.*"):
            await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_id=category_id,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_record_expense_income_category_id(self, transaction_service, sample_user):
        """Should raise ValueError if income category ID is used for expense."""
        # Arrange
        amount = Decimal("100000")
        income_category_id = 1  # Known income ID

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot use income category"):
            await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_id=income_category_id,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_record_expense_duplicate_detection(
        self,
        transaction_service,
        mock_transaction_repository,
        sample_user,
        expense_categories,
    ):
        """Should detect duplicate expense within 60-second window per FR-023."""
        # Arrange
        amount = Decimal("150000")
        description = "Paper and ink"
        supplies_category = expense_categories[2]

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
        mock_transaction_repository.find_duplicates.return_value = [duplicate_transaction]

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
        sample_user,
        expense_categories,
    ):
        """Should record expense with is_duplicate_confirmed=True when user confirms duplicate."""
        # Arrange
        amount = Decimal("150000")
        description = "Paper and ink"
        supplies_category = expense_categories[2]

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
            category_id=supplies_category.category_id,
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
        sample_user,
        expense_categories,
    ):
        """Should generate transaction ID in TX20251218001 format per FR-004."""
        # Arrange
        amount = Decimal("100000")
        other_category = expense_categories[4]

        mock_transaction_repository.get_daily_sequence.return_value = 5

        # Mock WITA datetime function
        mock_path = "src.bot.services.transaction_service.get_current_wita_datetime"
        with patch(mock_path) as mock_time:
            # We mock the UTILS function, not datetime directly
            from datetime import datetime
            import pytz

            wita = pytz.timezone("Asia/Makassar")
            mock_date = wita.localize(datetime(2025, 12, 18, 10, 30, 0))
            mock_time.return_value = mock_date

            expected_transaction = Transaction(
                transaction_id="TX20251218005",  # Sequence 5
                user_id=sample_user.user_id,
                type="expense",
                amount=amount,
                category_id=other_category.category_id,
                description="Test",
                timestamp=mock_date,
                status="recorded",
            )
            mock_transaction_repository.create.return_value = expected_transaction

            # Act
            result = await transaction_service.record_expense(
                user=sample_user,
                amount=amount,
                category_id=other_category.category_id,
                description="Test",
            )

            # Assert
            assert result.transaction_id == "TX20251218005"
            assert result.transaction_id.startswith("TX20251218")
