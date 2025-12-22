"""Integration tests for keyboard navigation flow."""
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from telegram import CallbackQuery
from telegram import Chat
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
from src.bot.keyboards.main_menu import create_main_menu_keyboard


class TestKeyboardNavigationIntegration:
    """Integration tests for complete keyboard navigation workflows."""

    @pytest.fixture
    def mock_update(self):
        """Create realistic Update mock."""
        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.edit_message_reply_markup = AsyncMock()
        update.callback_query.message = MagicMock(spec=Message)
        update.callback_query.message.reply_text = AsyncMock()
        update.callback_query.message.chat = MagicMock(spec=Chat)
        update.callback_query.message.chat.id = 12345
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = 12345
        update.callback_query.from_user.first_name = "Test"
        return update

    @pytest.fixture
    def mock_context(self):
        """Create realistic Context mock."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        context.bot = MagicMock()
        context.bot.send_message = AsyncMock()
        return context

    @pytest.mark.asyncio
    async def test_main_menu_keyboard_structure(self):
        """Main menu keyboard should have correct button structure."""
        keyboard = create_main_menu_keyboard()

        # Verify structure
        assert len(keyboard.inline_keyboard) == 3
        assert len(keyboard.inline_keyboard[0]) == 2  # Income, Expense
        assert len(keyboard.inline_keyboard[1]) == 2  # Summary, History
        assert len(keyboard.inline_keyboard[2]) == 1  # Settings

        # Verify callback data
        callbacks = []
        for row in keyboard.inline_keyboard:
            for button in row:
                callbacks.append(button.callback_data)

        assert "record_income" in callbacks
        assert "record_expense" in callbacks
        assert "daily_summary" in callbacks
        assert "transaction_history" in callbacks
        assert "settings" in callbacks

    @pytest.mark.asyncio
    async def test_navigation_flow_main_to_income(self, mock_update, mock_context):
        """User should navigate from main menu to income recording."""
        # Step 1: Show main menu
        await handle_main_menu_callback(mock_update, mock_context)
        mock_update.callback_query.answer.assert_called()

        # Step 2: Click Record Income
        mock_update.callback_query.reset_mock()
        await handle_record_income_callback(mock_update, mock_context)

        # Should transition to income conversation
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_navigation_flow_main_to_expense(self, mock_update, mock_context):
        """User should navigate from main menu to expense recording."""
        # Step 1: Show main menu
        await handle_main_menu_callback(mock_update, mock_context)

        # Step 2: Click Record Expense
        mock_update.callback_query.reset_mock()
        await handle_record_expense_callback(mock_update, mock_context)

        # Should transition to expense conversation
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_navigation_flow_main_to_summary(self, mock_update, mock_context):
        """User should navigate from main menu to daily summary."""
        with patch("src.bot.handlers.keyboard.ReportService") as mock_service:
            mock_service_instance = AsyncMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.generate_daily_summary.return_value = {
                "total_income": 0,
                "total_expenses": 0,
                "net_cash_flow": 0,
                "transaction_count": 0,
            }

            # Step 1: Show main menu
            await handle_main_menu_callback(mock_update, mock_context)

            # Step 2: Click Daily Summary
            mock_update.callback_query.reset_mock()
            await handle_daily_summary_callback(mock_update, mock_context)

            # Should show summary
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_navigation_preserves_user_context(self, mock_update, mock_context):
        """Navigation should preserve user context across callbacks."""
        mock_context.user_data["test_key"] = "test_value"

        # Navigate through menu
        await handle_main_menu_callback(mock_update, mock_context)
        mock_update.callback_query.reset_mock()
        await handle_settings_callback(mock_update, mock_context)

        # Context should be preserved
        assert mock_context.user_data["test_key"] == "test_value"

    @pytest.mark.asyncio
    async def test_all_menu_buttons_have_handlers(self):
        """All main menu buttons should have corresponding callback handlers."""
        keyboard = create_main_menu_keyboard()

        handler_map = {
            "record_income": handle_record_income_callback,
            "record_expense": handle_record_expense_callback,
            "daily_summary": handle_daily_summary_callback,
            "transaction_history": handle_transaction_history_callback,
            "settings": handle_settings_callback,
        }

        for row in keyboard.inline_keyboard:
            for button in row:
                assert (
                    button.callback_data in handler_map
                ), f"No handler found for callback: {button.callback_data}"

    @pytest.mark.asyncio
    async def test_keyboard_navigation_error_recovery(self, mock_update, mock_context):
        """Navigation should recover gracefully from errors."""
        # Simulate error in one callback
        mock_update.callback_query.edit_message_text.side_effect = Exception("API Error")

        with patch("src.bot.handlers.keyboard.ReportService") as mock_service:
            mock_service_instance = AsyncMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.generate_daily_summary.return_value = {}

            # Should not crash
            try:
                await handle_daily_summary_callback(mock_update, mock_context)
            except Exception:
                pytest.fail("Keyboard navigation should handle errors gracefully")

            # Should still answer callback query
            mock_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio
    async def test_back_navigation_returns_to_main_menu(self, mock_update, mock_context):
        """Back button should return user to main menu."""
        # Start from submenu (e.g., settings)
        await handle_settings_callback(mock_update, mock_context)

        # Navigate back to main menu
        mock_update.callback_query.reset_mock()
        await handle_main_menu_callback(mock_update, mock_context)

        # Should display main menu
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_reply_markup.assert_called()

    @pytest.mark.asyncio
    async def test_rapid_button_clicks_handled_safely(self, mock_update, mock_context):
        """Rapid button clicks should not cause race conditions."""
        # Simulate rapid clicks
        tasks = []
        for _ in range(5):
            mock_update.callback_query.reset_mock()
            task = handle_settings_callback(mock_update, mock_context)
            tasks.append(task)

        # All should complete without error
        import asyncio

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify no exceptions
        for result in results:
            assert not isinstance(result, Exception)
