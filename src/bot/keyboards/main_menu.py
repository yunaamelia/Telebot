"""Main menu and confirmation keyboards.

Provides inline keyboard layouts for user interactions.
"""
from datetime import date
from typing import Optional

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


def create_history_pagination_keyboard(
    current_page: int,
    total_pages: int,
    user_id: int,
    date_filter: Optional[date] = None,
    category_filter: Optional[int] = None,
    type_filter: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """Create keyboard for history pagination and filtering.

    Args:
        current_page: Current page number (1-indexed)
        total_pages: Total number of pages
        user_id: User ID for callback data
        date_filter: Optional date filter
        category_filter: Optional category ID filter
        type_filter: Optional transaction type filter ('income' or 'expense')

    Returns:
        InlineKeyboardMarkup with pagination and filter buttons
    """
    keyboard = []

    # Build filter parameters string for callback data
    filter_params = []
    if date_filter:
        filter_params.append(f"date_{date_filter.isoformat()}")
    if category_filter:
        filter_params.append(f"cat_{category_filter}")
    if type_filter:
        filter_params.append(f"type_{type_filter}")

    filter_str = "_".join(filter_params) if filter_params else "all"

    # Row 1: Pagination buttons (Previous / Next)
    pagination_row = []

    if current_page > 1:
        prev_page = current_page - 1
        pagination_row.append(
            InlineKeyboardButton(
                "◀️ Previous", callback_data=f"history_page_{prev_page}_{filter_str}"
            )
        )

    if current_page < total_pages:
        next_page = current_page + 1
        pagination_row.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"history_page_{next_page}_{filter_str}")
        )

    if pagination_row:
        keyboard.append(pagination_row)

    # Row 2: Filter buttons
    filter_row = [
        InlineKeyboardButton("🗓️ Filters", callback_data=f"history_show_filters_{current_page}"),
    ]
    keyboard.append(filter_row)

    # Row 3: Back to menu
    keyboard.append([InlineKeyboardButton("◀️ Back to Menu", callback_data="main_menu")])

    return InlineKeyboardMarkup(keyboard)


def create_history_filter_keyboard(current_page: int = 1) -> InlineKeyboardMarkup:
    """Create keyboard for history filter options.

    Args:
        current_page: Current page number to return to after filter

    Returns:
        InlineKeyboardMarkup with filter option buttons
    """
    keyboard = [
        # Row 1: Date filters
        [
            InlineKeyboardButton("📅 Today", callback_data=f"history_filter_today_{current_page}"),
            InlineKeyboardButton("📅 Week", callback_data=f"history_filter_week_{current_page}"),
        ],
        [
            InlineKeyboardButton("📅 Month", callback_data=f"history_filter_month_{current_page}"),
            InlineKeyboardButton("📅 All", callback_data=f"history_filter_all_{current_page}"),
        ],
        # Row 2: Type filters
        [
            InlineKeyboardButton(
                "💰 Income Only", callback_data=f"history_filter_income_{current_page}"
            ),
            InlineKeyboardButton(
                "💸 Expense Only",
                callback_data=f"history_filter_expense_{current_page}",
            ),
        ],
        # Row 3: Back
        [
            InlineKeyboardButton(
                "◀️ Back to History", callback_data=f"history_page_{current_page}_all"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
