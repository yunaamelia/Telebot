"""Daily report scheduler configuration and execution.

Configures APScheduler to trigger daily financial reports at midnight WITA.
Handles report generation, delivery, and error recovery per FR-009, FR-018.
"""
from datetime import datetime
from datetime import timedelta
from typing import Callable

import pytz
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from telegram.constants import ParseMode

from src.bot.services.notification_service import NotificationService
from src.bot.services.report_service import ReportService
from src.config.settings import settings


logger = structlog.get_logger(__name__)

# WITA timezone (Asia/Makassar, UTC+8, no DST)
WITA = pytz.timezone("Asia/Makassar")


def configure_daily_report_scheduler(scheduler: AsyncIOScheduler, report_job: Callable) -> None:
    """Configure scheduler to run daily report at midnight WITA.

    Args:
        scheduler: AsyncIOScheduler instance
        report_job: Async function to execute for daily report

    Example:
        >>> scheduler = AsyncIOScheduler(timezone=WITA)
        >>> configure_daily_report_scheduler(scheduler, execute_daily_report_job)
        >>> scheduler.start()
    """
    logger.info("Configuring daily report scheduler", timezone="Asia/Makassar")

    # Set scheduler timezone to WITA
    scheduler.timezone = WITA

    # Schedule job for midnight WITA (00:00)
    scheduler.add_job(
        report_job,
        trigger=CronTrigger(hour=0, minute=0, timezone=WITA),
        id="daily_report_midnight_wita",
        name="Daily Financial Report Generation",
        replace_existing=True,
        misfire_grace_time=300,  # 5 minutes grace period
    )

    logger.info(
        "Daily report scheduler configured",
        job_id="daily_report_midnight_wita",
        trigger_time="00:00 WITA",
    )


async def execute_daily_report_job(management_chat_id: int) -> None:
    """Execute daily report generation and delivery job.

    Called by scheduler at midnight WITA. Generates report for previous day,
    delivers to management chat with retry logic.

    Args:
        management_chat_id: Telegram chat ID to send report to

    Raises:
        Exception: If report delivery fails after all retries
    """
    logger.info("Starting daily report job execution", chat_id=management_chat_id)

    try:
        # Get previous day's date in WITA
        now_wita = datetime.now(WITA)
        report_date = (now_wita - timedelta(days=1)).date()

        logger.info("Generating daily report", report_date=str(report_date))

        # Initialize services
        bot = Bot(token=settings.telegram_bot_token)

        # Initialize repository and service
        from src.bot.repositories.transaction_repository import (
            TransactionRepository,
        )
        from src.database.session import get_db_session

        async with get_db_session() as session:
            transaction_repo = TransactionRepository(session)
            report_service = ReportService(transaction_repo)
            notification_service = NotificationService(bot)

            # Generate report data
            report_data = await report_service.generate_daily_report(report_date)

            # Format report message
            report_text = _format_daily_report_message(report_data)

            # Send with retry logic
            await notification_service.send_daily_report_with_retry(
                chat_id=management_chat_id, report_text=report_text
            )
    except Exception as e:
        logger.exception(
            "Daily report job failed",
            error=str(e),
            chat_id=management_chat_id,
        )

        # Send critical alert per FR-030
        await _send_critical_alert(management_chat_id, str(e))
        raise


def _format_daily_report_message(report_data: dict) -> str:
    """Format daily report data into message text.

    Args:
        report_data: Dictionary with report metrics

    Returns:
        Formatted HTML message string
    """
    generated_at = datetime.now(WITA).strftime("%d %b %Y %H:%M WITA")

    message = (
        f"🌙 <b>Daily Financial Report</b>\n"
        f"<b>Report Date:</b> {report_data['date']}\n"
        f"<b>Generated:</b> {generated_at}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Total Income:</b> <code>{report_data['total_income']}</code>\n"
        f"💸 <b>Total Expenses:</b> <code>{report_data['total_expenses']}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{report_data['net_cash_flow_indicator']} <b>Net Cash Flow:</b> "
        f"<code>{report_data['net_cash_flow']}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Expense Details:</b>\n"
        f"{report_data['category_breakdown']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 <b>Transaction Summary:</b>\n"
        f"• Total: {report_data['transaction_count']} transactions\n"
        f"• Income: {report_data['income_count']} transactions\n"
        f"• Expenses: {report_data['expense_count']} transactions"
    )

    return message


async def _send_critical_alert(chat_id: int, error_message: str) -> None:
    """Send critical alert for report delivery failure per FR-030.

    Args:
        chat_id: Management chat ID
        error_message: Error description
    """
    try:
        bot = Bot(token=settings.telegram_bot_token)
        alert_text = (
            f"🚨 <b>CRITICAL: Daily Report Delivery Failed</b>\n\n"
            f"<b>Time:</b> "
            f"{datetime.now(WITA).strftime('%d %b %Y %H:%M WITA')}\n"
            f"<b>Error:</b> <code>{error_message}</code>\n\n"
            f"Please check system logs and retry with /report command."
        )
        await bot.send_message(chat_id=chat_id, text=alert_text, parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("Failed to send critical alert")


async def reset_daily_counter() -> None:
    """Reset daily transaction counter at 00:01 WITA per FR-019.

    Called by scheduler one minute after midnight to reset the daily
    transaction sequence number.
    """
    logger.info("Resetting daily transaction counter")

    # TODO(#1): Implement counter reset in transaction service
    # This will be handled when implementing transaction ID generation

    logger.info("Daily transaction counter reset complete")
