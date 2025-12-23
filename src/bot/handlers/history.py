"""Transaction history command handler.

Handles /history command for viewing past transactions with pagination and filtering.
Per US6: Transaction History and Search (Priority P3).
"""
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.bot.keyboards.main_menu import create_history_pagination_keyboard
from src.bot.repositories.transaction_repository import TransactionRepository
from src.bot.repositories.user_repository import UserRepository
from src.bot.utils.formatters import format_currency
from src.bot.utils.timezone import to_wita
from src.config.logging import get_logger
from src.database.session import get_session

logger = get_logger(__name__)

# Pagination settings
ITEMS_PER_PAGE = 10


def format_history_message(
    transactions: list,
    current_page: int,
    total_pages: int,
    total_count: int,
    filter_description: str = "All transactions",
) -> str:
    """Format transaction history into a message.

    Args:
        transactions: List of Transaction objects
        current_page: Current page number (1-indexed)
        total_pages: Total number of pages
        total_count: Total transaction count
        filter_description: Description of applied filters

    Returns:
        Formatted HTML message string
    """
    if not transactions:
        return (
            "📋 <b>Transaction History</b>\n\n"
            "ℹ️ No transactions found for the selected period\n\n"
            "Try a different filter or date range"
        )

    # Header
    message = (
        "📋 <b>Transaction History</b>\n"
        f"<b>Filter:</b> {filter_description}\n"
        f"<b>Page:</b> {current_page} of {total_pages}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # Transaction items
    for tx in transactions:
        # Get emoji based on type
        emoji = "💰" if tx.type == "income" else "💸"

        # Get category name (will fetch from relationship)
        category_name = tx.category.name if hasattr(tx, "category") and tx.category else "Unknown"

        # Format amount
        amount = format_currency(tx.amount)

        # Format date
        wita_time = to_wita(tx.timestamp)
        date_str = wita_time.strftime("%d %b %Y %H:%M")

        # Format description
        description = tx.description if tx.description else "No description"

        # Build transaction item
        message += (
            f"{emoji} <b>{tx.type.capitalize()}</b> - {category_name}\n"
            f"<code>{amount}</code>\n"
            f"{description}\n"
            f"<i>{date_str} · {tx.transaction_id}</i>\n\n"
        )

    # Footer
    start_idx = (current_page - 1) * ITEMS_PER_PAGE + 1
    end_idx = min(current_page * ITEMS_PER_PAGE, total_count)

    message += (
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n" f"Showing {start_idx}-{end_idx} of {total_count} transactions"
    )

    return message


async def history_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /history command - show transaction history with pagination.

    Usage:
        /history - Show recent transactions (default)
        /history [YYYY-MM-DD] - Filter by specific date

    Args:
        update: Telegram update object
        context: Telegram context

    Returns:
        ConversationHandler state (not used, returns -1)
    """
    user = update.effective_user
    message_text = update.message.text.strip()

    logger.info(
        "History command received",
        extra={
            "user_id": user.id,
            "username": user.username,
            "command": message_text,
        },
    )

    async with get_session() as session:
        # Check authorization
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_telegram_id(user.id)

        if not db_user or db_user.status != "approved":
            await update.message.reply_text(
                "🔒 <b>Access Denied</b>\n\n"
                "You are not authorized to view transaction history.\n\n"
                "Please use /register to request access.",
                parse_mode=ParseMode.HTML,
            )
            logger.warning(
                "Unauthorized history access attempt",
                extra={
                    "telegram_id": user.id,
                    "status": db_user.status if db_user else "not_found",
                },
            )
            return -1

        # Parse command arguments
        parts = message_text.split()
        target_date = None
        filter_description = "All transactions"

        if len(parts) > 1:
            # User provided a date filter
            date_str = parts[1]
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                filter_description = f"Date: {target_date.strftime('%d %b %Y')}"
            except ValueError:
                await update.message.reply_text(
                    "❌ <b>Invalid Date Format</b>\n\n"
                    "Please use format: <code>YYYY-MM-DD</code>\n\n"
                    "<b>Example:</b> /history 2025-12-18",
                    parse_mode=ParseMode.HTML,
                )
                return -1

        # Retrieve transactions
        tx_repo = TransactionRepository(session)

        if target_date:
            # Filter by specific date
            transactions = await tx_repo.get_by_date_range(
                start_date=target_date, end_date=target_date, user_id=db_user.user_id
            )
            total_count = len(transactions)
            transactions = transactions[:ITEMS_PER_PAGE]  # First page
            current_page = 1
        else:
            # Get paginated history
            transactions, total_count = await tx_repo.get_history(
                user_id=db_user.user_id, limit=ITEMS_PER_PAGE, offset=0
            )
            current_page = 1

        # Calculate pagination
        total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

        # Format message
        message = format_history_message(
            transactions=transactions,
            current_page=current_page,
            total_pages=total_pages,
            total_count=total_count,
            filter_description=filter_description,
        )

        # Create keyboard
        keyboard = create_history_pagination_keyboard(
            current_page=current_page,
            total_pages=total_pages,
            user_id=db_user.user_id,
            date_filter=target_date,
        )

        # Send response
        await update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

        logger.info(
            "History displayed",
            extra={
                "user_id": db_user.user_id,
                "page": current_page,
                "total_pages": total_pages,
                "total_count": total_count,
                "filter": filter_description,
            },
        )

    return -1
