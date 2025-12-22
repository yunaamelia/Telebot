"""Unit tests for transaction service business logic."""
from datetime import date
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.bot.models.transaction import Transaction
from src.bot.models.user import User
from src.bot.repositories.transaction_repository import TransactionRepository
from src.bot.services.transaction_service import TransactionService
from src.bot.utils.validators import AmountValidationError


@pytest.fixture
def mock_repository():
    """Create mock transaction repository."""
    repository = Mock(spec=TransactionRepository)
    repository.create = AsyncMock()
    repository.find_duplicates = AsyncMock(return_value=[])
    repository.get_daily_sequence = AsyncMock(return_value=1)
    return repository


@pytest.fixture
def transaction_service(mock_repository):
    """Create transaction service with mocked repository."""
    return TransactionService(repository=mock_repository)


@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    user = User(
        user_id=1,
        telegram_id=123456789,
        telegram_username="testuser",
        full_name="Test User",
        role="staff",
        status="active",
    )
    return user


class TestRecordIncome:
    """Test income transaction recording."""

    @pytest.mark.asyncio
    async def test_record_income_valid_amount(
        self, transaction_service, mock_repository, sample_user
    ):
        """Should successfully record income with valid amount."""
        # Arrange
        amount = Decimal("500000")
        description = "Client payment"

        expected_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="income",
            amount=amount,
            category_id=1,  # Income category
            description=description,
            timestamp=datetime.now(),
            status="completed",
        )
        mock_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_income(
            user=sample_user, amount=amount, description=description
        )

        # Assert
        assert result.type == "income"
        assert result.amount == amount
        assert result.description == description
        assert result.user_id == sample_user.user_id
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_income_default_description(
        self, transaction_service, mock_repository, sample_user
    ):
        """Should use default description when not provided."""
        # Arrange
        amount = Decimal("500000")

        expected_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="income",
            amount=amount,
            category_id=1,
            description="No description",
            timestamp=datetime.now(),
            status="completed",
        )
        mock_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_income(
            user=sample_user, amount=amount, description=None
        )

        # Assert
        assert result.description == "No description"

    @pytest.mark.asyncio
    async def test_record_income_zero_amount_rejected(self, transaction_service, sample_user):
        """Should reject zero amount."""
        with pytest.raises(AmountValidationError) as exc_info:
            await transaction_service.record_income(
                user=sample_user, amount=Decimal("0"), description="Test"
            )
        assert "greater than 0" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_record_income_negative_amount_rejected(self, transaction_service, sample_user):
        """Should reject negative amount."""
        with pytest.raises(AmountValidationError) as exc_info:
            await transaction_service.record_income(
                user=sample_user, amount=Decimal("-500000"), description="Test"
            )
        assert "greater than 0" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_record_income_exceeds_max_limit(self, transaction_service, sample_user):
        """Should reject amount exceeding Rp 10 billion limit."""
        with pytest.raises(AmountValidationError) as exc_info:
            await transaction_service.record_income(
                user=sample_user,
                amount=Decimal("10000000001"),  # 10 billion + 1
                description="Test",
            )
        assert "maximum limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_record_income_at_max_limit(
        self, transaction_service, mock_repository, sample_user
    ):
        """Should accept amount exactly at Rp 10 billion limit."""
        # Arrange
        amount = Decimal("10000000000")  # Exactly 10 billion

        expected_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="income",
            amount=amount,
            category_id=1,
            description="Large payment",
            timestamp=datetime.now(),
            status="completed",
        )
        mock_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_income(
            user=sample_user, amount=amount, description="Large payment"
        )

        # Assert
        assert result.amount == amount

    @pytest.mark.asyncio
    async def test_record_income_generates_transaction_id(
        self, transaction_service, mock_repository, sample_user
    ):
        """Should generate transaction ID with correct format."""
        # Arrange
        amount = Decimal("500000")
        mock_repository.get_daily_sequence.return_value = 42

        with patch("bot.services.transaction_service.date") as mock_date:
            mock_date.today.return_value = date(2025, 12, 18)

            expected_transaction = Transaction(
                transaction_id="TX20251218042",
                user_id=sample_user.user_id,
                type="income",
                amount=amount,
                category_id=1,
                description="Test",
                timestamp=datetime.now(),
                status="completed",
            )
            mock_repository.create.return_value = expected_transaction

            # Act
            result = await transaction_service.record_income(
                user=sample_user, amount=amount, description="Test"
            )

            # Assert
            assert result.transaction_id == "TX20251218042"
            mock_repository.get_daily_sequence.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_income_category_always_income(
        self, transaction_service, mock_repository, sample_user
    ):
        """Should always assign income category (ID=1) for income transactions."""
        # Arrange
        amount = Decimal("500000")

        expected_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="income",
            amount=amount,
            category_id=1,  # Income category
            description="Test",
            timestamp=datetime.now(),
            status="completed",
        )
        mock_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_income(
            user=sample_user, amount=amount, description="Test"
        )

        # Assert
        assert result.category_id == 1  # Income category

    @pytest.mark.asyncio
    async def test_record_income_description_max_length(self, transaction_service, sample_user):
        """Should enforce maximum description length of 500 characters."""
        # Arrange
        amount = Decimal("500000")
        long_description = "a" * 501  # 501 characters

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await transaction_service.record_income(
                user=sample_user, amount=amount, description=long_description
            )
        assert "max 500 characters" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_record_income_description_exactly_500_chars(
        self, transaction_service, mock_repository, sample_user
    ):
        """Should accept description with exactly 500 characters."""
        # Arrange
        amount = Decimal("500000")
        description_500 = "a" * 500

        expected_transaction = Transaction(
            transaction_id="TX20251218001",
            user_id=sample_user.user_id,
            type="income",
            amount=amount,
            category_id=1,
            description=description_500,
            timestamp=datetime.now(),
            status="completed",
        )
        mock_repository.create.return_value = expected_transaction

        # Act
        result = await transaction_service.record_income(
            user=sample_user, amount=amount, description=description_500
        )

        # Assert
        assert len(result.description) == 500

    @pytest.mark.asyncio
    def test_record_expense_with_valid_category():
        """Test expense recording with valid category (not implemented)."""
        pytest.skip("Expense functionality not implemented yet - Phase 5")

    @pytest.mark.asyncio
    def test_record_expense_with_invalid_category():
        """Test expense recording with invalid category (not implemented)."""
        pytest.skip("Expense functionality not implemented yet - Phase 5")
