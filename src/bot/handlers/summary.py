"""Summary command handler for daily financial reports.

Handles /summary command to display current day's financial snapshot.
"""
import structlog
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.repositories.user_repository import UserRepository
from bot.services.report_service import ReportService
from bot.utils.formatters import format_daily_summary


logger = structlog.get_logger(__name__)


# Service instances (initialized in main)
report_service: ReportService = None
user_repository: UserRepository = None


def init_services(
    rpt_service: ReportService,
    user_repo: UserRepository,
):
    """Initialize service instances for handlers.

    Args:
        rpt_service: Report service instance
        user_repo: User repository instance
    """
    global report_service, user_repository
    report_service = rpt_service
    user_repository = user_repo


async def get_user_by_telegram_id(telegram_id: int):
    """Get user by Telegram ID.

    Args:
        telegram_id: Telegram user ID

    Returns:
        User object or None if not found
    """
    return await user_repository.find_by_telegram_id(telegram_id)


async def summary_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /summary command for daily financial summary.

    Displays current day's financial snapshot with:
    - Total income and expenses
    - Net cash flow (with positive/negative indicator)
    - Category breakdown
    - Transaction count

    Per US3: Staff and management can request current day's financial snapshot anytime.

    Args:
        update: Telegram update object
        context: Bot context

    Example output:
        📊 Daily Financial Summary
        Date: 18 Dec 2025

        ━━━━━━━━━━━━━━━━━━━━━━━

        💰 Total Income: Rp 2,500,000
        💸 Total Expenses: Rp 1,900,000

        ━━━━━━━━━━━━━━━━━━━━━━━

        📈 Net Cash Flow: Rp 600,000

        ━━━━━━━━━━━━━━━━━━━━━━━

        Expense Breakdown:
        🏢 Operational: Rp 500,000
        👔 Salaries: Rp 1,000,000
        📦 Supplies: Rp 150,000

        ━━━━━━━━━━━━━━━━━━━━━━━

        📈 Transactions: 12 total (5 income, 7 expenses)
    """
    user_telegram_id = update.effective_user.id

    logger.info(
        "Summary command received",
        telegram_id=user_telegram_id,
        username=update.effective_user.username,
    )

    # Get user from database
    user = await get_user_by_telegram_id(user_telegram_id)

    if not user:
        logger.warning("Unauthorized summary command attempt", telegram_id=user_telegram_id)
        await update.message.reply_text(
            "❌ You are not authorized to use this bot.\n\n"
            "Please contact the administrator to register.",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        # Generate daily summary for current date
        summary = await report_service.generate_daily_summary()

        # Format summary message
        summary_message = format_daily_summary(summary)

        # Send formatted summary
        await update.message.reply_text(
            summary_message,
            parse_mode=ParseMode.HTML,
        )

        logger.info(
            "Daily summary sent",
            user_id=user.user_id,
            summary_date=summary.summary_date.isoformat(),
            transaction_count=summary.transaction_count,
        )

    except Exception as e:
        logger.exception(
            "Error generating daily summary",
            user_id=user.user_id if user else None,
            error=str(e),
        )
        await update.message.reply_text(
            "❌ An error occurred while generating the summary. Please try again.",
            parse_mode=ParseMode.HTML,
        )
