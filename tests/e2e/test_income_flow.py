"""End-to-end tests for /income command flow with mock Telegram API.

Tests complete user workflow from command input through confirmation message.
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from telegram import Chat
from telegram import Message
from telegram import Update
from telegram import User as TelegramUser
from telegram.ext import ContextTypes

from src.bot.handlers.transaction import income_amount_handler
from src.bot.handlers.transaction import income_command_handler
from src.bot.handlers.transaction import income_description_handler
from src.bot.models.transaction import Transaction
from src.bot.models.user import User
from src.bot.services.notification_service import NotificationService
from src.bot.services.transaction_service import TransactionService


@pytest.fixture
def mock_telegram_update():
    """Create mock Telegram Update object."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=TelegramUser)
    update.effective_user.id = 123456789
    update.effective_user.username = "testuser"
    update.effective_user.full_name = "Test User"

    update.message = Mock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.text = "/income 500000 Client payment"
    update.message.chat = Mock(spec=Chat)
    update.message.chat.id = 123456789

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
    service.record_income = AsyncMock()
    return service


@pytest.fixture
def mock_notification_service_obj():
    """Create mock notification service with AsyncMock methods."""
    service = Mock(spec=NotificationService)
    service.send_error_message = AsyncMock()
    service.send_prompt = AsyncMock()
    service.send_confirmation = AsyncMock()
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
    """Create sample transaction response."""
    return Transaction(
        transaction_id="TX20251218001",
        user_id=1,
        type="income",
        amount=Decimal("500000"),
        category_id=1,
        description="Client payment",
        timestamp=datetime(2025, 12, 18, 10, 30, 0),
        status="completed",
    )


class TestIncomeCommandE2E:
    """End-to-end tests for /income command."""

    @pytest.mark.asyncio
    async def test_income_command_with_args_success(
        self,
        mock_telegram_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should successfully process /income command with amount and description."""
        # Arrange
        mock_telegram_update.message.text = "/income 500000 Client payment"
        mock_transaction_service.record_income.return_value = sample_transaction

        # Use real notification service
        real_notification_service = NotificationService(bot=mock_context.bot)

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=sample_user,
        ), patch(
            "src.bot.handlers.transaction.transaction_service", mock_transaction_service
        ), patch(
            "src.bot.handlers.transaction.notification_service",
            real_notification_service,
        ):
            # Act
            await income_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_transaction_service.record_income.assert_called_once_with(
                user=sample_user,
                amount=Decimal("500000"),
                description="Client payment",
            )

            # Verify confirmation message sent via bot.send_message
            mock_context.bot.send_message.assert_called_once()
            call_kwargs = mock_context.bot.send_message.call_args[1]
            sent_message = call_kwargs["text"]

            # Verify message contains transaction details
            assert "TX20251218001" in sent_message
            assert "500,000" in sent_message or "500.000" in sent_message

    @pytest.mark.asyncio
    async def test_income_command_without_args_enters_interactive_mode(
        self,
        mock_telegram_update,
        mock_context,
        sample_user,
        mock_notification_service_obj,
    ):
        """Should enter interactive mode when /income called without arguments."""
        # Arrange
        mock_telegram_update.message.text = "/income"

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=sample_user,
        ):
            with patch(
                "src.bot.handlers.transaction.notification_service",
                mock_notification_service_obj,
            ):
                # Act
                result = await income_command_handler(mock_telegram_update, mock_context)

        # Assert
        # Should ask for amount via send_prompt
        mock_notification_service_obj.send_prompt.assert_called_once()
        call_args = mock_notification_service_obj.send_prompt.call_args
        prompt_type = call_args[1]["prompt_type"]
        assert prompt_type == "amount"

        # Should return state for conversation handler
        assert result is not None  # Should return AMOUNT state

    @pytest.mark.asyncio
    async def test_income_command_invalid_amount_shows_error(
        self,
        mock_telegram_update,
        mock_context,
        sample_user,
        mock_notification_service_obj,
    ):
        """Should show error message for invalid amount format."""
        # Arrange
        mock_telegram_update.message.text = "/income abc123 Test"

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=sample_user,
        ):
            with patch(
                "src.bot.handlers.transaction.notification_service",
                mock_notification_service_obj,
            ):
                # Act
                await income_command_handler(mock_telegram_update, mock_context)

                # Assert
                mock_notification_service_obj.send_error_message.assert_called_once()
                call_args = mock_notification_service_obj.send_error_message.call_args
                error_message = call_args[1]["error_message"]
                assert "invalid" in error_message.lower() or "error" in error_message.lower()

    @pytest.mark.asyncio
    async def test_income_command_unauthorized_user_rejected(
        self, mock_telegram_update, mock_context
    ):
        """Should reject command from unauthorized user."""
        # Arrange
        mock_telegram_update.message.text = "/income 500000 Test"

        with patch("src.bot.handlers.transaction.get_user_by_telegram_id", return_value=None):
            # Act
            await income_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_telegram_update.message.reply_text.assert_called_once()
            sent_message = mock_telegram_update.message.reply_text.call_args[0][0]
            assert "not authorized" in sent_message.lower() or "register" in sent_message.lower()

    @pytest.mark.asyncio
    async def test_income_interactive_flow_complete(
        self,
        mock_telegram_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
        mock_notification_service_obj,
    ):
        """Should complete full interactive flow: command → amount → description → confirm."""
        mock_transaction_service.record_income.return_value = sample_transaction

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=sample_user,
        ), patch(
            "src.bot.handlers.transaction.transaction_service", mock_transaction_service
        ), patch(
            "src.bot.handlers.transaction.notification_service",
            mock_notification_service_obj,
        ):
            # Step 1: Start command
            mock_telegram_update.message.text = "/income"
            state = await income_command_handler(mock_telegram_update, mock_context)
            assert state is not None  # Should return AMOUNT state

            # Step 2: Provide amount
            mock_telegram_update.message.text = "500000"
            mock_notification_service_obj.send_prompt.reset_mock()  # Reset mock for next prompt
            state = await income_amount_handler(mock_telegram_update, mock_context)

            # Should ask for description
            mock_notification_service_obj.send_prompt.assert_called_once()
            prompt_text = mock_notification_service_obj.send_prompt.call_args[1]["prompt_type"]
            assert "description" in prompt_text.lower()
            assert state is not None  # Should return DESCRIPTION state

            # Step 3: Provide description
            mock_telegram_update.message.text = "Client payment"
            # Reset mock for confirmation
            mock_notification_service_obj.send_confirmation.reset_mock()
            state = await income_description_handler(mock_telegram_update, mock_context)

            # Should confirm transaction
            mock_notification_service_obj.send_confirmation.assert_called_once()
            mock_transaction_service.record_income.assert_called_once()

    @pytest.mark.asyncio
    async def test_income_command_with_comma_separator(
        self,
        mock_telegram_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should accept amount with comma thousands separator."""
        # Arrange
        mock_telegram_update.message.text = "/income 1,500,000 Large payment"
        mock_transaction_service.record_income.return_value = sample_transaction

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=sample_user,
        ), patch(
            "src.bot.handlers.transaction.transaction_service", mock_transaction_service
        ), patch(
            "src.bot.handlers.transaction.notification_service"
        ):
            # Act
            await income_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_transaction_service.record_income.assert_called_once()
            call_args = mock_transaction_service.record_income.call_args[1]
            assert call_args["amount"] == Decimal("1500000")

    @pytest.mark.asyncio
    async def test_income_command_with_dot_separator(
        self,
        mock_telegram_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should accept amount with dot thousands separator (Indonesian format)."""
        # Arrange
        mock_telegram_update.message.text = "/income 1.500.000 Large payment"
        mock_transaction_service.record_income.return_value = sample_transaction

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=sample_user,
        ), patch(
            "src.bot.handlers.transaction.transaction_service", mock_transaction_service
        ), patch(
            "src.bot.handlers.transaction.notification_service"
        ):
            # Act
            await income_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_transaction_service.record_income.assert_called_once()
            call_args = mock_transaction_service.record_income.call_args[1]
            assert call_args["amount"] == Decimal("1500000")

    @pytest.mark.asyncio
    async def test_income_command_confirmation_message_format(
        self,
        mock_telegram_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
    ):
        """Should send properly formatted confirmation message with HTML."""
        # Arrange
        mock_telegram_update.message.text = "/income 500000 Client payment"
        mock_transaction_service.record_income.return_value = sample_transaction

        # Use real notification service
        real_notification_service = NotificationService(bot=mock_context.bot)

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=sample_user,
        ), patch(
            "src.bot.handlers.transaction.transaction_service", mock_transaction_service
        ), patch(
            "src.bot.handlers.transaction.notification_service",
            real_notification_service,
        ):
            # Act
            await income_command_handler(mock_telegram_update, mock_context)

            # Assert
            mock_context.bot.send_message.assert_called_once()
            call_kwargs = mock_context.bot.send_message.call_args[1]

            # Should use HTML parse mode
            assert "parse_mode" in call_kwargs
            assert call_kwargs["parse_mode"] == "HTML" or call_kwargs["parse_mode"].name == "HTML"

            # Should contain emoji
            sent_text = call_kwargs["text"]
            assert "💰" in sent_text or "income" in sent_text.lower()

    @pytest.mark.asyncio
    async def test_income_command_skip_description(
        self,
        mock_telegram_update,
        mock_context,
        mock_transaction_service,
        sample_user,
        sample_transaction,
        mock_notification_service_obj,
    ):
        """Should use default description when skipped in interactive mode."""
        # Arrange
        mock_transaction_service.record_income.return_value = sample_transaction

        with patch(
            "src.bot.handlers.transaction.get_user_by_telegram_id",
            return_value=sample_user,
        ), patch(
            "src.bot.handlers.transaction.transaction_service", mock_transaction_service
        ), patch(
            "src.bot.handlers.transaction.notification_service",
            mock_notification_service_obj,
        ):
            # Step 1: Start command
            mock_telegram_update.message.text = "/income"
            await income_command_handler(mock_telegram_update, mock_context)

            # Step 2: Provide amount
            mock_telegram_update.message.text = "500000"
            await income_amount_handler(mock_telegram_update, mock_context)

            # Step 3: Skip description (send /skip or empty)
            mock_telegram_update.message.text = "/skip"
            await income_description_handler(mock_telegram_update, mock_context)

            # Assert
            call_args = mock_transaction_service.record_income.call_args[1]
            assert call_args["description"] is None or call_args["description"] == "No description"
