"""Unit tests for category keyboard builder (User Story 2).

Following TDD: These tests are written FIRST and should FAIL until implementation.
Tests the inline keyboard layout for expense category selection.
"""
import pytest
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from src.bot.keyboards.categories import create_category_keyboard
from src.bot.models.category import Category


@pytest.fixture
def expense_categories():
    """Create sample expense categories per data-model.md seed data."""
    return [
        Category(category_id=2, name="Operational", type="expense", emoji="🏢", sort_order=2),
        Category(category_id=3, name="Salaries", type="expense", emoji="👔", sort_order=3),
        Category(category_id=4, name="Supplies", type="expense", emoji="📦", sort_order=4),
        Category(category_id=5, name="Marketing", type="expense", emoji="📢", sort_order=5),
        Category(category_id=6, name="Other", type="expense", emoji="➕", sort_order=6),
    ]


class TestCategoryKeyboard:
    """Test category selection inline keyboard generation."""

    def test_create_category_keyboard_returns_markup(self, expense_categories):
        """Should return InlineKeyboardMarkup object."""
        # Act
        keyboard = create_category_keyboard(expense_categories)

        # Assert
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert keyboard is not None

    def test_create_category_keyboard_layout_structure(self, expense_categories):
        """Should create keyboard with correct row layout per contracts/commands.yaml.

        Expected layout:
        Row 1: [🏢 Operational] [👔 Salaries]
        Row 2: [📦 Supplies] [📢 Marketing]
        Row 3: [➕ Other]
        """
        # Act
        keyboard = create_category_keyboard(expense_categories)

        # Assert
        assert len(keyboard.inline_keyboard) == 3  # 3 rows

        # Row 1: Operational and Salaries
        assert len(keyboard.inline_keyboard[0]) == 2
        assert keyboard.inline_keyboard[0][0].text == "🏢 Operational"
        assert keyboard.inline_keyboard[0][1].text == "👔 Salaries"

        # Row 2: Supplies and Marketing
        assert len(keyboard.inline_keyboard[1]) == 2
        assert keyboard.inline_keyboard[1][0].text == "📦 Supplies"
        assert keyboard.inline_keyboard[1][1].text == "📢 Marketing"

        # Row 3: Other
        assert len(keyboard.inline_keyboard[2]) == 1
        assert keyboard.inline_keyboard[2][0].text == "➕ Other"

    def test_create_category_keyboard_button_text_format(self, expense_categories):
        """Should format button text with emoji and category name."""
        # Act
        keyboard = create_category_keyboard(expense_categories)

        # Assert
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]

        expected_texts = ["🏢 Operational", "👔 Salaries", "📦 Supplies", "📢 Marketing", "➕ Other"]

        actual_texts = [btn.text for btn in all_buttons]
        assert actual_texts == expected_texts

    def test_create_category_keyboard_callback_data(self, expense_categories):
        """Should set callback_data with category ID for handler routing."""
        # Act
        keyboard = create_category_keyboard(expense_categories)

        # Assert
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]

        # Callback data format: category_<category_id>
        expected_callbacks = [
            "category_2",  # Operational
            "category_3",  # Salaries
            "category_4",  # Supplies
            "category_5",  # Marketing
            "category_6",  # Other
        ]

        actual_callbacks = [btn.callback_data for btn in all_buttons]
        assert actual_callbacks == expected_callbacks

    def test_create_category_keyboard_respects_sort_order(self):
        """Should display categories in sort_order sequence."""
        # Arrange - Categories with mixed sort orders
        unsorted_categories = [
            Category(category_id=5, name="Marketing", type="expense", emoji="📢", sort_order=5),
            Category(category_id=2, name="Operational", type="expense", emoji="🏢", sort_order=2),
            Category(category_id=6, name="Other", type="expense", emoji="➕", sort_order=6),
            Category(category_id=3, name="Salaries", type="expense", emoji="👔", sort_order=3),
            Category(category_id=4, name="Supplies", type="expense", emoji="📦", sort_order=4),
        ]

        # Act
        keyboard = create_category_keyboard(unsorted_categories)

        # Assert - Should be displayed in sort_order (2, 3, 4, 5, 6)
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        actual_order = [btn.text for btn in all_buttons]

        expected_order = [
            "🏢 Operational",  # sort_order 2
            "👔 Salaries",  # sort_order 3
            "📦 Supplies",  # sort_order 4
            "📢 Marketing",  # sort_order 5
            "➕ Other",  # sort_order 6
        ]

        assert actual_order == expected_order

    def test_create_category_keyboard_empty_list(self):
        """Should handle empty category list gracefully."""
        # Arrange
        empty_categories = []

        # Act
        keyboard = create_category_keyboard(empty_categories)

        # Assert
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 0  # No buttons

    def test_create_category_keyboard_single_category(self):
        """Should handle single category correctly."""
        # Arrange
        single_category = [
            Category(category_id=6, name="Other", type="expense", emoji="➕", sort_order=6)
        ]

        # Act
        keyboard = create_category_keyboard(single_category)

        # Assert
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 1
        assert keyboard.inline_keyboard[0][0].text == "➕ Other"
        assert keyboard.inline_keyboard[0][0].callback_data == "category_6"

    def test_create_category_keyboard_filters_income_categories(self):
        """Should only include expense categories, filter out income categories."""
        # Arrange
        mixed_categories = [
            Category(category_id=1, name="Income", type="income", emoji="💰", sort_order=1),
            Category(category_id=2, name="Operational", type="expense", emoji="🏢", sort_order=2),
            Category(category_id=3, name="Salaries", type="expense", emoji="👔", sort_order=3),
        ]

        # Act
        keyboard = create_category_keyboard(mixed_categories)

        # Assert
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        button_texts = [btn.text for btn in all_buttons]

        # Should NOT include Income category
        assert "💰 Income" not in button_texts
        assert "🏢 Operational" in button_texts
        assert "👔 Salaries" in button_texts

    def test_create_category_keyboard_button_objects(self, expense_categories):
        """Should create proper InlineKeyboardButton objects."""
        # Act
        keyboard = create_category_keyboard(expense_categories)

        # Assert
        for row in keyboard.inline_keyboard:
            for button in row:
                assert isinstance(button, InlineKeyboardButton)
                assert button.text is not None
                assert button.callback_data is not None
                assert button.callback_data.startswith("category_")
