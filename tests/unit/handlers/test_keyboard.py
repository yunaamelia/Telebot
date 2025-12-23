"""Unit tests for keyboard callback navigation handlers."""
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from telegram import CallbackQuery
from telegram import Chat
from telegram import InlineKeyboardMarkup
from telegram import Message
from telegram import Update
from telegram import User
from telegram.ext import ContextTypes

from src.bot.handlers.keyboard import handle_daily_summary_callback
from src.bot.handlers.keyboard import handle_main_menu_callback
from src.bot.handlers.keyboard import handle_record_expense_callback
from src.bot.handlers.keyboard import handle_record_income_callback
from src.bot.handlers.keyboard import handle_settings_callback
from src.bot.handlers.keyboard import handle_transaction_history_callback


class TestKeyboardNavigation:
    """Test suite for keyboard callback navigation."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object with callback query."""
        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.edit_message_reply_markup = AsyncMock()
        update.callback_query.message = MagicMock(spec=Message)
        update.callback_query.message.reply_text = AsyncMock()
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = 12345
        update.callback_query.from_user.first_name = "Test User"
        update.callback_query.message.chat = MagicMock(spec=Chat)
        update.callback_query.message.chat.id = 12345
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_handle_record_income_callback_initiates_conversation(
        self, mock_update, mock_context
    ):
        """Record Income callback should initiate income recording conversation."""
        result = await handle_record_income_callback(mock_update, mock_context)

        # Should answer callback query
        mock_update.callback_query.answer.assert_called_once()

        # Should send prompt message for amount
        mock_update.callback_query.message.reply_text.assert_called_once()
        call_args = mock_update.callback_query.message.reply_text.call_args
        assert "amount" in call_args[0][0].lower() or "income" in call_args[0][0].lower()

        # Should return conversation state
        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_record_expense_callback_initiates_conversation(
        self, mock_update, mock_context
    ):
        """Record Expense callback should initiate expense recording conversation."""
        result = await handle_record_expense_callback(mock_update, mock_context)

        # Should answer callback query
        mock_update.callback_query.answer.assert_called_once()

        # Should send prompt message for amount
        mock_update.callback_query.message.reply_text.assert_called_once()
        call_args = mock_update.callback_query.message.reply_text.call_args
        assert "amount" in call_args[0][0].lower() or "expense" in call_args[0][0].lower()

        # Should return conversation state
        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_daily_summary_callback_shows_summary(self, mock_update, mock_context):
        """Daily Summary callback should display current day summary."""
        with patch("src.bot.handlers.keyboard.ReportService") as mock_service:
            mock_service_instance = AsyncMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.generate_daily_summary.return_value = {
                "total_income": 1000000,
                "total_expenses": 500000,
                "net_cash_flow": 500000,
                "transaction_count": 5,
            }

            await handle_daily_summary_callback(mock_update, mock_context)

            # Should answer callback query
            mock_update.callback_query.answer.assert_called_once()

            # Should edit message with summary
            mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_transaction_history_callback_placeholder(self, mock_update, mock_context):
        """Transaction History callback should show placeholder message (US6 not implemented)."""
        await handle_transaction_history_callback(mock_update, mock_context)

        # Should answer callback query
        mock_update.callback_query.answer.assert_called_once()

        # Should show placeholder message
        mock_update.callback_query.message.reply_text.assert_called_once()
        call_args = mock_update.callback_query.message.reply_text.call_args
        assert "history" in call_args[0][0].lower() or "coming soon" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_handle_settings_callback_placeholder(self, mock_update, mock_context):
        """Settings callback should show 'Coming soon' message per US5 AS4."""
        await handle_settings_callback(mock_update, mock_context)

        # Should answer callback query
        mock_update.callback_query.answer.assert_called_once()

        # Should show coming soon message
        mock_update.callback_query.message.reply_text.assert_called_once()
        call_args = mock_update.callback_query.message.reply_text.call_args
        assert "coming soon" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_callback_returns_to_main_menu(self, mock_update, mock_context):
        """Callbacks should provide way to return to main menu."""
        with patch("src.bot.handlers.keyboard.create_main_menu_keyboard") as mock_keyboard:
            mock_keyboard.return_value = MagicMock(spec=InlineKeyboardMarkup)

            await handle_settings_callback(mock_update, mock_context)

            # Should include main menu keyboard
            call_args = mock_update.callback_query.message.reply_text.call_args
            if "reply_markup" in call_args[1]:
                mock_keyboard.assert_called()

    @pytest.mark.asyncio
    async def test_callback_query_answered_first(self, mock_update, mock_context):
        """All callbacks should answer callback query to remove loading state."""
        await handle_settings_callback(mock_update, mock_context)

        # answer() should be called before any message operations
        mock_update.callback_query.answer.assert_called()

        # Verify answer was called first
        call_order = [call[0] for call in mock_update.callback_query.method_calls]
        answer_index = next(i for i, name in enumerate(call_order) if name == "answer")
        assert answer_index == 0, "answer() should be called first"

    @pytest.mark.asyncio
    async def test_main_menu_callback_shows_menu(self, mock_update, mock_context):
        """Main menu callback should display/redisplay main menu."""
        with patch("src.bot.handlers.keyboard.create_main_menu_keyboard") as mock_keyboard:
            mock_keyboard_markup = MagicMock(spec=InlineKeyboardMarkup)
            mock_keyboard.return_value = mock_keyboard_markup

            await handle_main_menu_callback(mock_update, mock_context)

            # Should answer callback query
            mock_update.callback_query.answer.assert_called_once()

            # Should create and display main menu keyboard
            mock_keyboard.assert_called_once()
            mock_update.callback_query.edit_message_reply_markup.assert_called_once_with(
                reply_markup=mock_keyboard_markup
            )

    @pytest.mark.asyncio
    async def test_callback_handles_errors_gracefully(self, mock_update, mock_context):
        """Callbacks should handle errors without crashing."""
        mock_update.callback_query.answer.side_effect = Exception("API Error")

        # Should not raise exception
        try:
            await handle_settings_callback(mock_update, mock_context)
        except Exception as e:
            pytest.fail(f"Callback should handle errors gracefully, but raised: {e}")
