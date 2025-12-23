"""E2E tests for /start command workflow."""
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from telegram import Chat
from telegram import Message
from telegram import Update
from telegram import User
from telegram.ext import ContextTypes

from src.bot.handlers.auth import start_command


class TestStartWorkflowE2E:
    """End-to-end tests for complete /start command workflow."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update for /start command."""
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.message.chat = MagicMock(spec=Chat)
        update.message.chat.id = 12345
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.effective_user.first_name = "Test User"
        update.effective_user.username = "testuser"
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        context.bot = MagicMock()
        context.bot.send_message = AsyncMock()
        return context

    @pytest.mark.asyncio
    async def test_start_command_sends_welcome_message(self, mock_update, mock_context):
        """Start command should send welcome message with main menu."""
        await start_command(mock_update, mock_context)

        # Should send welcome message
        mock_update.message.reply_text.assert_called_once()

        # Message should include greeting
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "welcome" in message_text.lower() or "hello" in message_text.lower()

    @pytest.mark.asyncio
    async def test_start_command_includes_main_menu_keyboard(self, mock_update, mock_context):
        """Start command should include main menu inline keyboard."""
        await start_command(mock_update, mock_context)

        # Should include reply_markup with keyboard
        call_args = mock_update.message.reply_text.call_args
        assert "reply_markup" in call_args[1]

        # Keyboard should have buttons
        keyboard = call_args[1]["reply_markup"]
        assert len(keyboard.inline_keyboard) > 0

    @pytest.mark.asyncio
    async def test_start_command_personalizes_greeting(self, mock_update, mock_context):
        """Start command should use user's first name in greeting."""
        mock_update.effective_user.first_name = "Alice"

        await start_command(mock_update, mock_context)

        # Should include user's name
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "alice" in message_text.lower()

    @pytest.mark.asyncio
    async def test_start_command_menu_has_five_options(self, mock_update, mock_context):
        """Start command menu should have all 5 primary options."""
        await start_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        keyboard = call_args[1]["reply_markup"]

        # Count total buttons
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 5

    @pytest.mark.asyncio
    async def test_start_command_uses_html_formatting(self, mock_update, mock_context):
        """Start command should use HTML parse mode for formatting."""
        await start_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert call_args[1].get("parse_mode") == "HTML"

    @pytest.mark.asyncio
    async def test_start_command_includes_bot_description(self, mock_update, mock_context):
        """Start message should explain bot's purpose."""
        await start_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0].lower()

        # Should mention cash flow or transactions
        assert (
            "cash flow" in message_text
            or "transaction" in message_text
            or "income" in message_text
            or "expense" in message_text
        )

    @pytest.mark.asyncio
    async def test_start_command_handles_new_user(self, mock_update, mock_context):
        """Start command should handle new users gracefully."""
        # Simulate new user with no context
        mock_context.user_data = {}

        await start_command(mock_update, mock_context)

        # Should still send welcome
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_command_handles_returning_user(self, mock_update, mock_context):
        """Start command should handle returning users."""
        # Simulate returning user with existing context
        mock_context.user_data = {"last_command": "/summary", "transaction_count": 10}

        await start_command(mock_update, mock_context)

        # Should still send welcome (can be same or different message)
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_workflow_complete_navigation_path(self, mock_update, mock_context):
        """Complete workflow: start -> view menu -> can navigate all options."""
        # Step 1: Send /start
        await start_command(mock_update, mock_context)

        # Get keyboard from response
        call_args = mock_update.message.reply_text.call_args
        keyboard = call_args[1]["reply_markup"]

        # Step 2: Verify all expected buttons are present
        expected_callbacks = [
            "record_income",
            "record_expense",
            "daily_summary",
            "transaction_history",
            "settings",
        ]

        actual_callbacks = []
        for row in keyboard.inline_keyboard:
            for button in row:
                actual_callbacks.append(button.callback_data)

        for expected in expected_callbacks:
            assert expected in actual_callbacks, f"Expected callback '{expected}' not found in menu"

    @pytest.mark.asyncio
    async def test_start_command_emoji_consistency(self, mock_update, mock_context):
        """Start command menu should use consistent emoji."""
        await start_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        keyboard = call_args[1]["reply_markup"]

        # Collect button texts
        button_texts = []
        for row in keyboard.inline_keyboard:
            for button in row:
                button_texts.append(button.text)

        # Verify expected emoji
        all_text = " ".join(button_texts)
        assert "💰" in all_text  # Income
        assert "💸" in all_text  # Expense
        assert "📊" in all_text  # Summary
        assert "📋" in all_text  # History
        assert "⚙️" in all_text  # Settings

    @pytest.mark.asyncio
    async def test_start_command_error_handling(self, mock_update, mock_context):
        """Start command should handle errors gracefully."""
        mock_update.message.reply_text.side_effect = Exception("Telegram API error")

        # Should not crash
        try:
            await start_command(mock_update, mock_context)
        except Exception:
            pytest.fail("Start command should handle errors gracefully")

    @pytest.mark.asyncio
    async def test_start_command_response_time(self, mock_update, mock_context):
        """Start command should respond quickly."""
        import time

        start_time = time.time()
        await start_command(mock_update, mock_context)
        end_time = time.time()

        # Should respond in under 1 second (generous for mock)
        response_time = end_time - start_time
        assert response_time < 1.0, f"Start command took {response_time}s"
