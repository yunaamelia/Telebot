"""End-to-end tests for /history command flow with mock Telegram API.

Tests T109: Complete user workflow for transaction history with pagination and filtering.
"""
from datetime import date
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from telegram import CallbackQuery
from telegram import Chat
from telegram import Message
from telegram import Update
from telegram import User as TelegramUser
from telegram.ext import ContextTypes

from src.bot.models.transaction import Transaction
from src.bot.models.user import User


@pytest.fixture
def mock_telegram_update():
    """Create mock Telegram Update object for /history command."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=TelegramUser)
    update.effective_user.id = 123456789
    update.effective_user.username = "testuser"
    update.effective_user.full_name = "Test User"

    update.message = Mock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.text = "/history"
    update.message.chat = Mock(spec=Chat)
    update.message.chat.id = 123456789

    return update


@pytest.fixture
def mock_callback_query_update():
    """Create mock Telegram Update with callback query for pagination."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=TelegramUser)
    update.effective_user.id = 123456789

    update.callback_query = Mock(spec=CallbackQuery)
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = "history_page_1"
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
def sample_user():
    """Create sample approved user."""
    return User(
        user_id=1,
        telegram_id=123456789,
        telegram_username="testuser",
        display_name="Test User",
        role="staff",
        status="approved",
    )


@pytest.fixture
def sample_transactions():
    """Create list of sample transactions for history."""
    transactions = []
    for i in range(15):
        tx = Transaction(
            transaction_id=f"TX2025121800{i + 1:02d}",
            user_id=1,
            type="income" if i % 2 == 0 else "expense",
            amount=Decimal(str(100000 + i * 10000)),
            category_id=1 if i % 2 == 0 else 3,
            description=f"Transaction {i + 1}",
            timestamp=datetime(2025, 12, 18, 10 + i, 0, 0),
            transaction_date=date(2025, 12, 18),
            status="recorded",
        )
        transactions.append(tx)
    return transactions


class TestHistoryCommandE2E:
    """End-to-end tests for /history command."""

    @pytest.mark.asyncio
    async def test_history_command_displays_recent_transactions(
        self, mock_telegram_update, mock_context, sample_user, sample_transactions
    ):
        """Should display last 10 transactions with pagination buttons."""
        # Arrange
        from src.bot.handlers.history import history_command_handler

        with patch("src.bot.handlers.history.UserRepository") as MockUserRepo, patch(
            "src.bot.handlers.history.TransactionRepository"
        ) as MockTxRepo:
            # Mock user repository
            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)

            # Mock transaction repository - return first page
            mock_tx_repo = MockTxRepo.return_value
            mock_tx_repo.get_history = AsyncMock(return_value=(sample_transactions[:10], 15))

            # Act
            await history_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args

            # Verify message contains transaction info
            message_text = call_args.kwargs.get("text", "")
            assert "📋 Transaction History" in message_text
            assert "TX20251218001" in message_text  # First transaction ID
            assert "Page 1 of 2" in message_text or "1/2" in message_text

            # Verify pagination keyboard is present
            reply_markup = call_args.kwargs.get("reply_markup")
            assert reply_markup is not None

    @pytest.mark.asyncio
    async def test_history_command_with_date_filter(
        self, mock_telegram_update, mock_context, sample_user, sample_transactions
    ):
        """Should filter transactions by specific date."""
        # Arrange
        mock_telegram_update.message.text = "/history 2025-12-18"

        from src.bot.handlers.history import history_command_handler

        with patch("src.bot.handlers.history.UserRepository") as MockUserRepo, patch(
            "src.bot.handlers.history.TransactionRepository"
        ) as MockTxRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)

            mock_tx_repo = MockTxRepo.return_value
            # Return filtered transactions
            filtered_txs = [
                tx for tx in sample_transactions if tx.transaction_date == date(2025, 12, 18)
            ]
            mock_tx_repo.get_by_date_range = AsyncMock(return_value=filtered_txs[:10])

            # Act
            await history_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            message_text = call_args.kwargs.get("text", "")

            # Should indicate date filter
            assert "2025-12-18" in message_text or "18 Dec 2025" in message_text

    @pytest.mark.asyncio
    async def test_history_pagination_next_page(
        self, mock_callback_query_update, mock_context, sample_user, sample_transactions
    ):
        """Should navigate to next page when Next button clicked."""
        # Arrange
        mock_callback_query_update.callback_query.data = "history_page_1"

        from src.bot.handlers.keyboard import history_pagination_callback

        with patch("src.bot.handlers.keyboard.UserRepository") as MockUserRepo, patch(
            "src.bot.handlers.keyboard.TransactionRepository"
        ) as MockTxRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)

            mock_tx_repo = MockTxRepo.return_value
            # Return second page (items 10-15)
            mock_tx_repo.get_history = AsyncMock(return_value=(sample_transactions[10:15], 15))

            # Act
            await history_pagination_callback(mock_callback_query_update, mock_context)

            # Assert
            mock_callback_query_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_callback_query_update.callback_query.edit_message_text.call_args
            message_text = call_args.kwargs.get("text", "")

            # Should show page 2
            assert "Page 2 of 2" in message_text or "2/2" in message_text
            # Should show transactions from second page
            assert "TX20251218011" in message_text

    @pytest.mark.asyncio
    async def test_history_empty_results(self, mock_telegram_update, mock_context, sample_user):
        """Should display friendly message when no transactions found."""
        # Arrange
        from src.bot.handlers.history import history_command_handler

        with patch("src.bot.handlers.history.UserRepository") as MockUserRepo, patch(
            "src.bot.handlers.history.TransactionRepository"
        ) as MockTxRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)

            mock_tx_repo = MockTxRepo.return_value
            mock_tx_repo.get_history = AsyncMock(return_value=([], 0))

            # Act
            await history_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            message_text = call_args.kwargs.get("text", "")

            # Should show "no transactions" message
            assert (
                "No transactions found" in message_text or "no transactions" in message_text.lower()
            )

    @pytest.mark.asyncio
    async def test_history_filter_by_category(
        self, mock_callback_query_update, mock_context, sample_user, sample_transactions
    ):
        """Should filter transactions by selected category."""
        # Arrange
        mock_callback_query_update.callback_query.data = "history_filter_category_3"

        from src.bot.handlers.keyboard import history_filter_callback

        with patch("src.bot.handlers.keyboard.UserRepository") as MockUserRepo, patch(
            "src.bot.handlers.keyboard.TransactionRepository"
        ) as MockTxRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)

            mock_tx_repo = MockTxRepo.return_value
            # Return only expense transactions (category 3)
            filtered = [tx for tx in sample_transactions if tx.category_id == 3]
            mock_tx_repo.get_by_date_range = AsyncMock(return_value=filtered[:10])

            # Act
            await history_filter_callback(mock_callback_query_update, mock_context)

            # Assert
            mock_callback_query_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_history_filter_by_today(
        self, mock_callback_query_update, mock_context, sample_user, sample_transactions
    ):
        """Should filter transactions to show only today's entries."""
        # Arrange
        mock_callback_query_update.callback_query.data = "history_filter_today"

        from src.bot.handlers.keyboard import history_filter_callback

        with patch("src.bot.handlers.keyboard.UserRepository") as MockUserRepo, patch(
            "src.bot.handlers.keyboard.TransactionRepository"
        ) as MockTxRepo, patch("src.bot.handlers.keyboard.date") as mock_date:
            # Mock today's date
            mock_date.today.return_value = date(2025, 12, 18)

            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)

            mock_tx_repo = MockTxRepo.return_value
            today_txs = [
                tx for tx in sample_transactions if tx.transaction_date == date(2025, 12, 18)
            ]
            mock_tx_repo.get_by_date_range = AsyncMock(return_value=today_txs[:10])

            # Act
            await history_filter_callback(mock_callback_query_update, mock_context)

            # Assert
            mock_callback_query_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_callback_query_update.callback_query.edit_message_text.call_args
            message_text = call_args.kwargs.get("text", "")

            # Should indicate "Today" filter
            assert "Today" in message_text or "today" in message_text.lower()

    @pytest.mark.asyncio
    async def test_history_unauthorized_user(self, mock_telegram_update, mock_context):
        """Should reject history request from unauthorized user."""
        # Arrange
        from src.bot.handlers.history import history_command_handler

        with patch("src.bot.handlers.history.UserRepository") as MockUserRepo:
            mock_user_repo = MockUserRepo.return_value
            # User not found or not approved
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=None)

            # Act
            await history_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            message_text = call_args.kwargs.get("text", "")

            # Should show unauthorized message
            assert (
                "not authorized" in message_text.lower() or "access denied" in message_text.lower()
            )

    @pytest.mark.asyncio
    async def test_history_invalid_date_format(
        self, mock_telegram_update, mock_context, sample_user
    ):
        """Should show error for invalid date format."""
        # Arrange
        mock_telegram_update.message.text = "/history 2025/12/18"  # Wrong format

        from src.bot.handlers.history import history_command_handler

        with patch("src.bot.handlers.history.UserRepository") as MockUserRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)

            # Act
            await history_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            message_text = call_args.kwargs.get("text", "")

            # Should show format error
            assert "invalid" in message_text.lower() or "format" in message_text.lower()
            # Should show correct format example
            assert "YYYY-MM-DD" in message_text


class TestHistoryKeyboardNavigation:
    """Test keyboard interactions for history filtering and pagination."""

    @pytest.mark.asyncio
    async def test_pagination_keyboard_structure(
        self, mock_telegram_update, mock_context, sample_user, sample_transactions
    ):
        """Should generate correct pagination keyboard structure."""
        # Arrange
        from src.bot.handlers.history import history_command_handler

        with patch("src.bot.handlers.history.UserRepository") as MockUserRepo, patch(
            "src.bot.handlers.history.TransactionRepository"
        ) as MockTxRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)

            mock_tx_repo = MockTxRepo.return_value
            mock_tx_repo.get_history = AsyncMock(return_value=(sample_transactions[:10], 15))

            # Act
            await history_command_handler(mock_telegram_update, mock_context)

            # Assert
            call_args = mock_telegram_update.message.reply_text.call_args
            reply_markup = call_args.kwargs.get("reply_markup")
            assert reply_markup is not None

            # Should have pagination buttons
            # Structure: [Previous] [Next] | [Filters] | [Back to Menu]
            keyboard = reply_markup.inline_keyboard
            assert len(keyboard) >= 1  # At least one row

    @pytest.mark.asyncio
    async def test_filter_keyboard_options(
        self, mock_telegram_update, mock_context, sample_user, sample_transactions
    ):
        """Should provide filter options for date ranges and categories."""
        # Arrange
        from src.bot.handlers.history import history_command_handler

        with patch("src.bot.handlers.history.UserRepository") as MockUserRepo, patch(
            "src.bot.handlers.history.TransactionRepository"
        ) as MockTxRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)

            mock_tx_repo = MockTxRepo.return_value
            mock_tx_repo.get_history = AsyncMock(return_value=(sample_transactions[:10], 15))

            # Act
            await history_command_handler(mock_telegram_update, mock_context)

            # Assert
            call_args = mock_telegram_update.message.reply_text.call_args
            reply_markup = call_args.kwargs.get("reply_markup")

            # Keyboard should exist
            assert reply_markup is not None
