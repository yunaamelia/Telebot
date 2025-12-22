"""Main menu and confirmation keyboards.

Provides inline keyboard layouts for user interactions.
"""
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup


def create_duplicate_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for duplicate transaction confirmation.

    Returns:
        InlineKeyboardMarkup with Yes/No buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, record it", callback_data="confirm_duplicate_yes"),
            InlineKeyboardButton("❌ No, cancel", callback_data="confirm_duplicate_no"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard with primary actions.

    Returns:
        InlineKeyboardMarkup with menu options
    """
    keyboard = [
        [
            InlineKeyboardButton("💰 Record Income", callback_data="record_income"),
            InlineKeyboardButton("💸 Record Expense", callback_data="record_expense"),
        ],
        [
            InlineKeyboardButton("📊 Daily Summary", callback_data="daily_summary"),
            InlineKeyboardButton("📋 Transaction History", callback_data="transaction_history"),
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_category_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Create keyboard for expense category selection.

    Args:
        categories: List of Category objects

    Returns:
        InlineKeyboardMarkup with category buttons
    """
    keyboard = []

    # Create buttons in rows of 2
    for i in range(0, len(categories), 2):
        row = []
        for category in categories[i : i + 2]:
            button_text = f"{category.emoji} {category.name}"
            callback_data = f"category_{category.category_id}"
            row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)
