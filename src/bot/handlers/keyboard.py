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


async def handle_transaction_history_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle Transaction History button callback.

    Shows placeholder message (US6 not yet implemented).

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
            "📋 <b>Transaction History</b>\n\n"
            "Transaction history feature coming soon!\n\n"
            "For now, use <code>/summary</code> to view today's transactions."
        )

        keyboard = create_main_menu_keyboard()

        await query.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

        logger.info(
            "Transaction history placeholder shown",
            extra={"user_id": query.from_user.id},
        )

    except Exception as e:
        logger.exception("Error in history callback", extra={"error": str(e)})
        with contextlib.suppress(Exception):
            await query.answer("Error", show_alert=True)


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
