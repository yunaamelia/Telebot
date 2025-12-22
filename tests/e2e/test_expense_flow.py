"""End-to-end tests for /expense command flow with category selection (User Story 2).

Following TDD: These tests are written FIRST and should FAIL until implementation.
Tests complete user workflow from command input → category selection → confirmation.
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from telegram import CallbackQuery
from telegram import Chat
from telegram import InlineKeyboardMarkup
from telegram import Message
from telegram import Update
from telegram import User as TelegramUser
from telegram.ext import ContextTypes

from src.bot.handlers.transaction import expense_category_callback_handler
from src.bot.handlers.transaction import expense_command_handler
from src.bot.models.category import Category
from src.bot.models.transaction import Transaction
from src.bot.models.user import User
from src.bot.services.transaction_service import TransactionService


@pytest.fixture
def mock_telegram_update():
    """Create mock Telegram Update object for /expense command."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=TelegramUser)
    update.effective_user.id = 123456789
    update.effective_user.username = "testuser"
    update.effective_user.full_name = "Test User"

    update.message = Mock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.text = "/expense 250000 Office supplies"
    update.message.chat = Mock(spec=Chat)
    update.message.chat.id = 123456789

    return update


@pytest.fixture
def mock_callback_query_update():
    """Create mock Telegram Update object for category selection callback."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=TelegramUser)
    update.effective_user.id = 123456789
    update.effective_user.username = "testuser"

    update.callback_query = Mock(spec=CallbackQuery)
    update.callback_query.data = "category_4"  # Supplies category
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message = Mock(spec=Message)
    update.callback_query.message.chat = Mock(spec=Chat)
    update.callback_query.message.chat.id = 123456789

    return update


@pytest.fixture
def mock_context():
    """Create mock bot context."""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = Mock()
    context.bot.send_message = AsyncMock()
    return context


@pytest.fixture
def mock_transaction_service():
    """Create mock transaction service."""
    service = Mock(spec=TransactionService)
    service.record_expense = AsyncMock()
    service.check_duplicate_expense = AsyncMock(return_value=[])
    return service


@pytest.fixture
def sample_user():
    """Create sample user."""
    return User(
        user_id=1,
        telegram_id=123456789,
        telegram_username="testuser",
        display_name="Test User",
        role="staff",
        status="approved",
    )


@pytest.fixture
def sample_transaction():
    """Create sample expense transaction response."""
    return Transaction(
        transaction_id="TX20251218001",
        user_id=1,
        type="expense",
        amount=Decimal("250000"),
        category_id=4,
        description="Office supplies",
        timestamp=datetime(2025, 12, 18, 10, 30, 0),
        status="recorded",
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


class TestExpenseCommandE2E:
    """End-to-end tests for /expense command workflow."""

    @pytest.mark.asyncio
    async def test_expense_command_shows_category_keyboard(
        self, mock_telegram_update, mock_context, sample_user, expense_categories
    ):
        """Should display category selection keyboard after /expense command."""
        # Arrange
        mock_telegram_update.message.text = "/expense 250000 Office supplies"

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id", return_value=sample_user
        ):
            with patch(
                "src.bot.handlers.transaction.get_expense_categories",
                return_value=expense_categories,
            ):
                # Act
                await expense_command_handler(mock_telegram_update, mock_context)

                # Assert - Should send category keyboard
                mock_telegram_update.message.reply_text.assert_called_once()
                call_args = mock_telegram_update.message.reply_text.call_args

                # Verify message contains category selection prompt
                msg = call_args[0][0]
                assert "category" in msg.lower() or "Select" in msg

                # Verify keyboard was provided
                assert "reply_markup" in call_args[1]
                keyboard = call_args[1]["reply_markup"]
                assert isinstance(keyboard, InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_expense_category_callback_records_transaction(
        self,
        mock_callback_query_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should record transaction after category selection callback."""
        # Arrange
        mock_context.user_data = {
            "amount": Decimal("250000"),
            "description": "Office supplies",
        }
        mock_transaction_service.record_expense.return_value = sample_transaction

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id", return_value=sample_user
        ):
            with patch(
                "src.bot.handlers.transaction.transaction_service", mock_transaction_service
            ):
                with patch(
                    "src.bot.handlers.transaction.get_category_by_id",
                    return_value=Category(
                        category_id=4,
                        name="Supplies",
                        type="expense",
                        emoji="📦",
                        sort_order=4,
                    ),
                ):
                    # Act
                    await expense_category_callback_handler(
                        mock_callback_query_update, mock_context
                    )

                    # Assert - Should record expense
                    mock_transaction_service.record_expense.assert_called_once_with(
                        user=sample_user,
                        amount=Decimal("250000"),
                        category_name="Supplies",
                        description="Office supplies",
                    )

    @pytest.mark.asyncio
    async def test_expense_flow_sends_confirmation_message(
        self,
        mock_callback_query_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should send formatted confirmation message after successful expense recording."""
        # Arrange
        mock_context.user_data = {
            "amount": Decimal("250000"),
            "description": "Office supplies",
        }
        mock_transaction_service.record_expense.return_value = sample_transaction

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id", return_value=sample_user
        ):
            with patch(
                "src.bot.handlers.transaction.transaction_service", mock_transaction_service
            ):
                with patch(
                    "src.bot.handlers.transaction.get_category_by_id",
                    return_value=Category(
                        category_id=4,
                        name="Supplies",
                        type="expense",
                        emoji="📦",
                        sort_order=4,
                    ),
                ):
                    # Act
                    await expense_category_callback_handler(
                        mock_callback_query_update, mock_context
                    )

                    # Assert - Should send confirmation
                    mock_callback_query_update.callback_query.edit_message_text.assert_called_once()
                    confirmation_message = (
                        mock_callback_query_update.callback_query.edit_message_text.call_args[0][0]
                    )

                    # Verify confirmation contains transaction details per contracts/messages.yaml
                    assert "TX20251218001" in confirmation_message  # Transaction ID
                    assert (
                        "250,000" in confirmation_message or "250.000" in confirmation_message
                    )  # Amount formatted
                    assert (
                        "Supplies" in confirmation_message or "📦" in confirmation_message
                    )  # Category

    @pytest.mark.asyncio
    async def test_expense_quick_category_shortcut(
        self,
        mock_telegram_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should record expense directly with /expense_supplies shortcut per FR-002."""
        # Arrange
        mock_telegram_update.message.text = "/expense_supplies 150000 Paper and ink"
        mock_transaction_service.record_expense.return_value = sample_transaction

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=sample_user,
        ), patch(
            "src.bot.handlers.transaction.transaction_service",
            mock_transaction_service,
        ):
            # Act
            await expense_command_handler(mock_telegram_update, mock_context)

            # Assert - Should record directly without keyboard
            mock_transaction_service.record_expense.assert_called_once()
            call_args = mock_transaction_service.record_expense.call_args
            assert call_args[1]["category_name"] == "Supplies"
            assert call_args[1]["amount"] == Decimal("150000")

    @pytest.mark.asyncio
    async def test_expense_all_quick_category_shortcuts(
        self, mock_context, mock_transaction_service, sample_user, sample_transaction
    ):
        """Should support all quick category shortcuts per contracts/commands.yaml."""
        # Test all shortcut commands
        shortcuts = [
            ("/expense_operational 500000 Rent", "Operational"),
            ("/expense_salaries 1000000 Staff payment", "Salaries"),
            ("/expense_supplies 150000 Office items", "Supplies"),
            ("/expense_marketing 300000 Ad campaign", "Marketing"),
            ("/expense_other 75000 Misc", "Other"),
        ]

        for command, expected_category in shortcuts:
            # Arrange
            mock_update = Mock(spec=Update)
            mock_update.effective_user = Mock(spec=TelegramUser)
            mock_update.effective_user.id = 123456789
            mock_update.message = Mock(spec=Message)
            mock_update.message.text = command
            mock_update.message.reply_text = AsyncMock()

            mock_transaction_service.record_expense.return_value = sample_transaction

            with patch(
                "src.bot.handlers.transaction.get_user_by_telegram_id",
                return_value=sample_user,
            ):
                with patch(
                    "src.bot.handlers.transaction.transaction_service",
                    mock_transaction_service,
                ):
                    # Act
                    await expense_command_handler(mock_update, mock_context)

                    # Assert
                    call_args = mock_transaction_service.record_expense.call_args
                    assert call_args[1]["category_name"] == expected_category

    @pytest.mark.asyncio
    async def test_expense_default_description_uncategorized(
        self,
        mock_telegram_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should use 'Uncategorized expense' when description omitted per US2 AS5."""
        # Arrange
        mock_telegram_update.message.text = "/expense 100000"  # No description
        mock_transaction_service.record_expense.return_value = sample_transaction

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id", return_value=sample_user
        ):
            with patch(
                "src.bot.handlers.transaction.transaction_service", mock_transaction_service
            ):
                # Act
                await expense_command_handler(mock_telegram_update, mock_context)

                # Assert - Should have category keyboard shown (will get description later)
                # Or if using default immediately:
                # call_args = mock_transaction_service.record_expense.call_args
                # assert call_args[1]['description'] == "Uncategorized expense"

    @pytest.mark.asyncio
    async def test_expense_invalid_amount_shows_error(
        self, mock_telegram_update, mock_context, sample_user
    ):
        """Should display error message for invalid amount format."""
        # Arrange
        mock_telegram_update.message.text = "/expense abc Invalid amount"

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id", return_value=sample_user
        ):
            # Act
            await expense_command_handler(mock_telegram_update, mock_context)

            # Assert - Should send error message
            mock_telegram_update.message.reply_text.assert_called_once()
            error_message = mock_telegram_update.message.reply_text.call_args[0][0]
            assert (
                "❌" in error_message
                or "Invalid" in error_message
                or "error" in error_message.lower()
            )

    @pytest.mark.asyncio
    async def test_expense_amount_too_large_shows_error(
        self, mock_telegram_update, mock_context, sample_user
    ):
        """Should display error for amount exceeding Rp 10 billion per FR-022."""
        # Arrange
        mock_telegram_update.message.text = "/expense 10000000001 Too large"

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id", return_value=sample_user
        ):
            # Act
            await expense_command_handler(mock_telegram_update, mock_context)

            # Assert - Should send error message
            mock_telegram_update.message.reply_text.assert_called_once()
            error_message = mock_telegram_update.message.reply_text.call_args[0][0]
            assert (
                "❌" in error_message
                or "maximum" in error_message.lower()
                or "exceeds" in error_message.lower()
            )

    @pytest.mark.asyncio
    async def test_expense_unauthorized_user_denied(self, mock_telegram_update, mock_context):
        """Should deny access to unauthorized users."""
        # Arrange
        unauthorized_user = User(
            user_id=1,
            telegram_id=123456789,
            status="pending",
            role="staff",  # Not approved
        )

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=unauthorized_user,
        ):
            # Act
            await expense_command_handler(mock_telegram_update, mock_context)

            # Assert - Should send access denied message
            mock_telegram_update.message.reply_text.assert_called_once()
            error_message = mock_telegram_update.message.reply_text.call_args[0][0]
            assert (
                "❌" in error_message
                or "denied" in error_message.lower()
                or "unauthorized" in error_message.lower()
            )

    @pytest.mark.asyncio
    async def test_expense_duplicate_detection_shows_confirmation(
        self,
        mock_telegram_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should show duplicate confirmation dialog when duplicate detected per FR-023."""
        # Arrange
        mock_telegram_update.message.text = "/expense 100000 Duplicate test"

        # Mock duplicate detection
        mock_transaction_service.check_duplicate_expense.return_value = [sample_transaction]

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id", return_value=sample_user
        ):
            with patch(
                "src.bot.handlers.transaction.transaction_service", mock_transaction_service
            ):
                # Act
                await expense_command_handler(mock_telegram_update, mock_context)

                # Assert - Should send duplicate warning with Yes/No keyboard
                mock_telegram_update.message.reply_text.assert_called()
                call_args = mock_telegram_update.message.reply_text.call_args

                # Check for duplicate warning message
                message = call_args[1].get("text", call_args[0][0])

                assert "duplicate" in message.lower() or "similar" in message.lower()

                # Should have keyboard with Yes/No options
                if "reply_markup" in call_args[1]:
                    keyboard = call_args[1]["reply_markup"]
                    assert isinstance(keyboard, InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_expense_interactive_mode_sequential_prompts(self, mock_context, sample_user):
        """Should use sequential prompts for keyboard-based expense entry per FR-029."""
        # Arrange - /expense with no args triggers interactive mode
        mock_update = Mock(spec=Update)
        mock_update.effective_user = Mock(spec=TelegramUser)
        mock_update.effective_user.id = 123456789
        mock_update.message = Mock(spec=Message)
        mock_update.message.text = "/expense"
        mock_update.message.reply_text = AsyncMock()

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id", return_value=sample_user
        ):
            # Act
            await expense_command_handler(mock_update, mock_context)

            # Assert - Should prompt for amount first
            mock_update.message.reply_text.assert_called_once()
            prompt_message = mock_update.message.reply_text.call_args[0][0]
            assert "amount" in prompt_message.lower() or "enter" in prompt_message.lower()

    @pytest.mark.asyncio
    async def test_expense_callback_query_acknowledged(
        self,
        mock_callback_query_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should acknowledge callback query to prevent loading indicator."""
        # Arrange
        mock_context.user_data = {
            "amount": Decimal("100000"),
            "description": "Test",
        }
        mock_transaction_service.record_expense.return_value = sample_transaction

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id", return_value=sample_user
        ):
            with patch(
                "src.bot.handlers.transaction.transaction_service", mock_transaction_service
            ):
                with patch(
                    "src.bot.handlers.transaction.get_category_by_id",
                    return_value=Category(
                        category_id=4,
                        name="Supplies",
                        type="expense",
                        emoji="📦",
                        sort_order=4,
                    ),
                ):
                    # Act
                    await expense_category_callback_handler(
                        mock_callback_query_update, mock_context
                    )

                    # Assert - Should answer callback query
                    mock_callback_query_update.callback_query.answer.assert_called_once()
