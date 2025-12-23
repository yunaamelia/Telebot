"""Keyboard callback handlers for inline button navigation.

Routes callback queries from inline keyboards to appropriate handlers.
Implements US5 - Interactive Inline Keyboard Navigation.
"""
import contextlib
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler

from src.bot.handlers.transaction import AMOUNT
from src.bot.keyboards.main_menu import create_main_menu_keyboard
from src.bot.services.report_service import ReportService
from src.bot.utils.formatters import format_currency

logger = logging.getLogger(__name__)


async def handle_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu callback to redisplay menu.

    Used for "Back" button navigation and manual menu display.

    Args:
        update: Telegram update with callback query
        context: Bot context

    Returns:
        None
    """
    try:
        query = update.callback_query
        await query.answer()

        keyboard = create_main_menu_keyboard()

        # Edit message to show main menu
        await query.edit_message_reply_markup(reply_markup=keyboard)

        logger.info("Main menu displayed", extra={"user_id": query.from_user.id})

    except Exception as e:
        logger.exception("Error displaying main menu", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error displaying menu. Try /start", show_alert=True)


async def handle_record_income_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Record Income button callback.

    Initiates income recording conversation flow.

    Args:
        update: Telegram update with callback query
        context: Bot context

    Returns:
        int: AMOUNT conversation state
    """
    try:
        query = update.callback_query
        await query.answer()

        message = (
            "💰 <b>Record Income</b>\n\n"
            "Enter the income amount in Rupiah:\n"
            "<i>Example: 500000 or 500,000</i>"
        )

        await query.message.reply_text(message, parse_mode=ParseMode.HTML)

        logger.info(
            "Income recording initiated via keyboard",
            extra={"user_id": query.from_user.id},
        )

        return AMOUNT

    except Exception as e:
        logger.exception("Error in income callback", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error starting income recording", show_alert=True)
        return ConversationHandler.END


async def handle_record_expense_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Record Expense button callback.

    Initiates expense recording conversation flow.

    Args:
        update: Telegram update with callback query
        context: Bot context

    Returns:
        int: AMOUNT conversation state
    """
    try:
        query = update.callback_query
        await query.answer()

        message = (
            "💸 <b>Record Expense</b>\n\n"
            "Enter the expense amount in Rupiah:\n"
            "<i>Example: 250000 or 250,000</i>"
        )

        await query.message.reply_text(message, parse_mode=ParseMode.HTML)

        # Store that this is an expense transaction
        context.user_data["transaction_type"] = "expense"

        logger.info(
            "Expense recording initiated via keyboard",
            extra={"user_id": query.from_user.id},
        )

        return AMOUNT

    except Exception as e:
        logger.exception("Error in expense callback", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error starting expense recording", show_alert=True)
        return ConversationHandler.END


async def handle_daily_summary_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Daily Summary button callback.

    Displays current day's financial summary.

    Args:
        update: Telegram update with callback query
        context: Bot context

    Returns:
        None
    """
    try:
        query = update.callback_query
        await query.answer()

        # Get user_id from callback
        user_id = query.from_user.id

        # Generate daily summary
        report_service = ReportService()
        summary = await report_service.generate_daily_summary(user_id)

        # Format summary message
        total_income = summary.get("total_income", 0)
        total_expenses = summary.get("total_expenses", 0)
        net_cash_flow = summary.get("net_cash_flow", 0)
        transaction_count = summary.get("transaction_count", 0)

        # Determine net cash flow indicator
        if net_cash_flow > 0:
            net_indicator = "📈 Positive"
        elif net_cash_flow < 0:
            net_indicator = "📉 Negative"
        else:
            net_indicator = "➡️ Break Even"

        message = (
            "📊 <b>Daily Summary</b>\n\n"
            f"💰 Total Income: {format_currency(total_income)}\n"
            f"💸 Total Expenses: {format_currency(total_expenses)}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💵 Net Cash Flow: {format_currency(net_cash_flow)}\n"
            f"   {net_indicator}\n\n"
            f"📝 Transactions: {transaction_count}"
        )

        # Add category breakdown if available
        if "category_breakdown" in summary and summary["category_breakdown"]:
            message += "\n\n<b>Expense Breakdown:</b>"
            for category in summary["category_breakdown"]:
                cat_name = category.get("name", "Unknown")
                cat_emoji = category.get("emoji", "")
                cat_amount = category.get("total", 0)
                message += f"\n{cat_emoji} {cat_name}: {format_currency(cat_amount)}"

        # Add main menu keyboard
        keyboard = create_main_menu_keyboard()

        await query.edit_message_text(message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

        logger.info("Daily summary displayed via keyboard", extra={"user_id": user_id})

    except Exception as e:
        logger.exception("Error in daily summary callback", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error loading summary", show_alert=True)


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Settings button callback.

    Shows "Coming soon" message per US5 AS4.

    Args:
        update: Telegram update with callback query
        context: Bot context

    Returns:
        None
    """
    try:
        query = update.callback_query
        await query.answer()

        message = (
            "⚙️ <b>Settings</b>\n\n"
            "Settings feature coming soon!\n\n"
            "Future settings will include:\n"
            "• Notification preferences\n"
            "• Report schedule customization\n"
            "• Category management\n"
            "• Language selection"
        )

        keyboard = create_main_menu_keyboard()

        await query.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

        logger.info("Settings placeholder shown", extra={"user_id": query.from_user.id})

    except Exception as e:
        logger.exception("Error in settings callback", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error", show_alert=True)


async def handle_back_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Back button callback.

    Returns user to main menu per US5 AS3.

    Args:
        update: Telegram update with callback query
        context: Bot context

    Returns:
        None
    """
    try:
        query = update.callback_query
        await query.answer()

        # Show main menu
        await handle_main_menu_callback(update, context)

        logger.info("Back button navigation", extra={"user_id": query.from_user.id})

    except Exception as e:
        logger.exception("Error in back button callback", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error navigating back", show_alert=True)


async def history_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle history pagination button clicks.

    Parses callback data format: history_page_{page}_{filter_params}

    Args:
        update: Telegram update with callback query
        context: Bot context
    """
    from datetime import timedelta
    from src.bot.handlers.history import format_history_message, ITEMS_PER_PAGE
    from src.bot.keyboards.main_menu import create_history_pagination_keyboard
    from src.bot.repositories.transaction_repository import TransactionRepository
    from src.bot.repositories.user_repository import UserRepository
    from src.database.session import get_session

    try:
        query = update.callback_query
        await query.answer()

        # Parse callback data: history_page_{page}_{filters}
        callback_parts = query.data.split("_")
        page = int(callback_parts[2])
        filter_str = "_".join(callback_parts[3:]) if len(callback_parts) > 3 else "all"

        logger.info(
            "History pagination",
            extra={"user_id": query.from_user.id, "page": page, "filters": filter_str},
        )

        async with get_session() as session:
            # Get user
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(query.from_user.id)

            if not db_user:
                await query.answer("User not found", show_alert=True)
                return

            # Retrieve transactions
            tx_repo = TransactionRepository(session)
            offset = (page - 1) * ITEMS_PER_PAGE

            # Parse filters from filter_str
            date_filter = None
            category_filter = None
            type_filter = None

            if filter_str != "all":
                # Parse filter parameters
                for param in filter_str.split("_"):
                    if param.startswith("date_"):
                        from datetime import datetime

                        date_filter = datetime.strptime(param[5:], "%Y-%m-%d").date()
                    elif param.startswith("cat_"):
                        category_filter = int(param[4:])
                    elif param.startswith("type_"):
                        type_filter = param[5:]

            # Get transactions based on filters
            if date_filter or category_filter or type_filter:
                # Use filtered query
                start_date = (
                    date_filter if date_filter else (datetime.now().date() - timedelta(days=365))
                )
                end_date = date_filter if date_filter else datetime.now().date()

                all_txs = await tx_repo.get_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    user_id=db_user.user_id,
                    category_id=category_filter,
                    transaction_type=type_filter,
                )
                total_count = len(all_txs)
                transactions = all_txs[offset : offset + ITEMS_PER_PAGE]
            else:
                # Get paginated history
                transactions, total_count = await tx_repo.get_history(
                    user_id=db_user.user_id, limit=ITEMS_PER_PAGE, offset=offset
                )

            # Calculate pagination
            total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

            # Format message
            filter_description = "All transactions"
            if date_filter:
                filter_description = f"Date: {date_filter.strftime('%d %b %Y')}"
            elif type_filter:
                filter_description = f"Type: {type_filter.capitalize()}"

            message = format_history_message(
                transactions=transactions,
                current_page=page,
                total_pages=total_pages,
                total_count=total_count,
                filter_description=filter_description,
            )

            # Create keyboard
            keyboard = create_history_pagination_keyboard(
                current_page=page,
                total_pages=total_pages,
                user_id=db_user.user_id,
                date_filter=date_filter,
                category_filter=category_filter,
                type_filter=type_filter,
            )

            # Update message
            await query.edit_message_text(message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    except Exception as e:
        logger.exception("Error in history pagination", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error loading page", show_alert=True)


async def history_filter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle history filter button clicks.

    Parses callback data format: history_filter_{filter_type}_{page}

    Args:
        update: Telegram update with callback query
        context: Bot context
    """
    from datetime import datetime, timedelta
    from src.bot.handlers.history import format_history_message, ITEMS_PER_PAGE
    from src.bot.keyboards.main_menu import (
        create_history_pagination_keyboard,
        create_history_filter_keyboard,
    )
    from src.bot.repositories.transaction_repository import TransactionRepository
    from src.bot.repositories.user_repository import UserRepository
    from src.database.session import get_session

    try:
        query = update.callback_query
        await query.answer()

        # Parse callback data: history_filter_{type}_{page} or history_show_filters_{page}
        callback_parts = query.data.split("_")

        # Check if showing filter menu
        if "show" in callback_parts:
            page = int(callback_parts[3])
            keyboard = create_history_filter_keyboard(current_page=page)
            await query.edit_message_reply_markup(reply_markup=keyboard)
            return

        filter_type = callback_parts[2]
        page = int(callback_parts[3])

        logger.info(
            "History filter applied",
            extra={"user_id": query.from_user.id, "filter": filter_type, "page": page},
        )

        async with get_session() as session:
            # Get user
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(query.from_user.id)

            if not db_user:
                await query.answer("User not found", show_alert=True)
                return

            # Determine filter parameters
            tx_repo = TransactionRepository(session)
            today = datetime.now().date()

            date_filter = None
            type_filter = None
            filter_description = "All transactions"

            if filter_type == "today":
                date_filter = today
                filter_description = f"Today ({today.strftime('%d %b %Y')})"
            elif filter_type == "week":
                start_date = today - timedelta(days=7)
                transactions = await tx_repo.get_by_date_range(
                    start_date=start_date, end_date=today, user_id=db_user.user_id
                )
                total_count = len(transactions)
                transactions = transactions[:ITEMS_PER_PAGE]
                filter_description = "Last 7 days"
            elif filter_type == "month":
                start_date = today - timedelta(days=30)
                transactions = await tx_repo.get_by_date_range(
                    start_date=start_date, end_date=today, user_id=db_user.user_id
                )
                total_count = len(transactions)
                transactions = transactions[:ITEMS_PER_PAGE]
                filter_description = "Last 30 days"
            elif filter_type == "income":
                type_filter = "income"
                filter_description = "Income Only"
            elif filter_type == "expense":
                type_filter = "expense"
                filter_description = "Expense Only"
            else:  # "all"
                pass

            # Get transactions if not already retrieved
            if filter_type in ["today", "income", "expense", "all"]:
                if date_filter or type_filter:
                    start_date = date_filter if date_filter else (today - timedelta(days=365))
                    end_date = date_filter if date_filter else today

                    transactions = await tx_repo.get_by_date_range(
                        start_date=start_date,
                        end_date=end_date,
                        user_id=db_user.user_id,
                        transaction_type=type_filter,
                    )
                    total_count = len(transactions)
                    transactions = transactions[:ITEMS_PER_PAGE]
                else:
                    transactions, total_count = await tx_repo.get_history(
                        user_id=db_user.user_id, limit=ITEMS_PER_PAGE, offset=0
                    )

            # Calculate pagination
            total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

            # Format message
            message = format_history_message(
                transactions=transactions,
                current_page=1,  # Reset to page 1 when filter changes
                total_pages=total_pages,
                total_count=total_count,
                filter_description=filter_description,
            )

            # Create keyboard
            keyboard = create_history_pagination_keyboard(
                current_page=1,
                total_pages=total_pages,
                user_id=db_user.user_id,
                date_filter=date_filter,
                type_filter=type_filter,
            )

            # Update message
            await query.edit_message_text(message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    except Exception as e:
        logger.exception("Error in history filter", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error applying filter", show_alert=True)


async def handle_transaction_history_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle Transaction History button callback from main menu.

    Displays transaction history with pagination.

    Args:
        update: Telegram update with callback query
        context: Bot context
    """
    from src.bot.handlers.history import format_history_message, ITEMS_PER_PAGE
    from src.bot.keyboards.main_menu import create_history_pagination_keyboard
    from src.bot.repositories.transaction_repository import TransactionRepository
    from src.bot.repositories.user_repository import UserRepository
    from src.database.session import get_session

    try:
        query = update.callback_query
        await query.answer()

        logger.info("Transaction history callback", extra={"user_id": query.from_user.id})

        async with get_session() as session:
            # Get user
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(query.from_user.id)

            if not db_user or db_user.status != "approved":
                await query.answer("Not authorized", show_alert=True)
                return

            # Get transactions
            tx_repo = TransactionRepository(session)
            transactions, total_count = await tx_repo.get_history(
                user_id=db_user.user_id, limit=ITEMS_PER_PAGE, offset=0
            )

            # Calculate pagination
            total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

            # Format message
            message = format_history_message(
                transactions=transactions,
                current_page=1,
                total_pages=total_pages,
                total_count=total_count,
                filter_description="All transactions",
            )

            # Create keyboard
            keyboard = create_history_pagination_keyboard(
                current_page=1, total_pages=total_pages, user_id=db_user.user_id
            )

            # Send or edit message
            await query.message.reply_text(
                message, parse_mode=ParseMode.HTML, reply_markup=keyboard
            )

    except Exception as e:
        logger.exception("Error in transaction history callback", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error loading history", show_alert=True)
