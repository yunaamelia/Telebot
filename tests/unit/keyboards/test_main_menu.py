"""Unit tests for main menu keyboard builder."""
from telegram import InlineKeyboardButton

from src.bot.keyboards.main_menu import create_main_menu_keyboard


class TestMainMenuKeyboard:
    """Test suite for main menu keyboard functionality."""

    def test_main_menu_has_five_buttons(self):
        """Main menu should have all 5 primary action buttons."""
        keyboard = create_main_menu_keyboard()

        # Count total buttons
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 5, "Main menu should have exactly 5 buttons"

    def test_main_menu_record_income_button(self):
        """Main menu should have Record Income button in first row."""
        keyboard = create_main_menu_keyboard()

        first_row = keyboard.inline_keyboard[0]
        assert len(first_row) >= 1

        income_button = first_row[0]
        assert income_button.text == "💰 Record Income"
        assert income_button.callback_data == "record_income"

    def test_main_menu_record_expense_button(self):
        """Main menu should have Record Expense button in first row."""
        keyboard = create_main_menu_keyboard()

        first_row = keyboard.inline_keyboard[0]
        assert len(first_row) >= 2

        expense_button = first_row[1]
        assert expense_button.text == "💸 Record Expense"
        assert expense_button.callback_data == "record_expense"

    def test_main_menu_daily_summary_button(self):
        """Main menu should have Daily Summary button in second row."""
        keyboard = create_main_menu_keyboard()

        second_row = keyboard.inline_keyboard[1]
        assert len(second_row) >= 1

        summary_button = second_row[0]
        assert summary_button.text == "📊 Daily Summary"
        assert summary_button.callback_data == "daily_summary"

    def test_main_menu_transaction_history_button(self):
        """Main menu should have Transaction History button in second row."""
        keyboard = create_main_menu_keyboard()

        second_row = keyboard.inline_keyboard[1]
        assert len(second_row) >= 2

        history_button = second_row[1]
        assert history_button.text == "📋 Transaction History"
        assert history_button.callback_data == "transaction_history"

    def test_main_menu_settings_button(self):
        """Main menu should have Settings button in third row."""
        keyboard = create_main_menu_keyboard()

        third_row = keyboard.inline_keyboard[2]
        assert len(third_row) >= 1

        settings_button = third_row[0]
        assert settings_button.text == "⚙️ Settings"
        assert settings_button.callback_data == "settings"

    def test_main_menu_button_layout(self):
        """Main menu should have 3 rows with 2-2-1 button layout."""
        keyboard = create_main_menu_keyboard()

        assert len(keyboard.inline_keyboard) == 3, "Should have 3 rows"
        assert len(keyboard.inline_keyboard[0]) == 2, "First row should have 2 buttons"
        assert len(keyboard.inline_keyboard[1]) == 2, "Second row should have 2 buttons"
        assert len(keyboard.inline_keyboard[2]) == 1, "Third row should have 1 button"

    def test_main_menu_buttons_are_inline_keyboard_buttons(self):
        """All buttons should be InlineKeyboardButton instances."""
        keyboard = create_main_menu_keyboard()

        for row in keyboard.inline_keyboard:
            for button in row:
                assert isinstance(button, InlineKeyboardButton)

    def test_main_menu_callback_data_format(self):
        """All callback data should follow snake_case format."""
        keyboard = create_main_menu_keyboard()

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

        assert sorted(actual_callbacks) == sorted(expected_callbacks)

    def test_main_menu_uses_emoji_consistently(self):
        """All buttons should have emoji for visual consistency."""
        keyboard = create_main_menu_keyboard()

        emoji_map = {
            "💰": "Record Income",
            "💸": "Record Expense",
            "📊": "Daily Summary",
            "📋": "Transaction History",
            "⚙️": "Settings",
        }

        found_emojis = set()
        for row in keyboard.inline_keyboard:
            for button in row:
                for emoji in emoji_map.keys():
                    if emoji in button.text:
                        found_emojis.add(emoji)

        assert len(found_emojis) == 5, "All 5 emoji should be present"
