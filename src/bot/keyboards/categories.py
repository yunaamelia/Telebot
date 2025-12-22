"""Category selection keyboards for expense recording.

Provides inline keyboard markup for expense category selection per data-model.md.
"""
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from bot.models.category import Category


def create_expense_category_keyboard(
    categories: list[Category],
) -> InlineKeyboardMarkup:
    """Create inline keyboard for expense category selection.

    Displays expense categories (excluding income) in a 3-column grid layout
    with emoji and category name. Callback data format: 'category_{id}'.

    Args:
        categories: List of Category objects for expenses only (type='expense')

    Returns:
        InlineKeyboardMarkup: Telegram inline keyboard with category buttons

    Example:
        >>> categories = [
        ...     Category(id=2, name="Operational", emoji="🏢", type="expense"),
        ...     Category(id=3, name="Salaries", emoji="👔", type="expense"),
        ... ]
        >>> keyboard = create_expense_category_keyboard(categories)
        >>> # Renders as:
        >>> # [🏢 Operational] [👔 Salaries] [📦 Supplies]
        >>> # [📢 Marketing] [➕ Other]
    """
    # Filter expense categories only and sort by sort_order
    expense_categories = [cat for cat in categories if cat.type == "expense"]
    expense_categories.sort(key=lambda c: c.sort_order)

    # Build keyboard rows (3 buttons per row)
    keyboard = []
    row = []

    for category in expense_categories:
        # Format button text with emoji and name
        button_text = f"{category.emoji} {category.name}"
        callback_data = f"category_{category.category_id}"

        button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
        row.append(button)

        # Create new row after 3 buttons
        if len(row) == 3:
            keyboard.append(row)
            row = []

    # Add remaining buttons in last row
    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)
