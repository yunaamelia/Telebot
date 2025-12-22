"""Notification service for sending messages to users.

Handles transaction confirmations, reports, and system notifications.
"""
from typing import Optional

import structlog
from telegram import Bot
from telegram.constants import ParseMode

from src.bot.models.category import Category
from src.bot.models.transaction import Transaction
from src.bot.utils.formatters import format_currency
from src.bot.utils.timezone import format_wita_datetime


logger = structlog.get_logger(__name__)


class NotificationService:
    """Service for sending notifications via Telegram."""

    def __init__(self, bot: Bot):
        """Initialize notification service.

        Args:
            bot: Telegram Bot instance for sending messages
        """
        self.bot = bot

    async def send_confirmation(
        self,
        chat_id: int,
        transaction: Transaction,
        category: Optional[Category] = None,
    ) -> None:
        """Send transaction confirmation message to user.

        Formats and sends a confirmation message with transaction details
        using HTML formatting and appropriate emoji.

        Args:
            chat_id: Telegram chat ID to send message to
            transaction: Transaction object to confirm
            category: Optional category object for expense transactions

        Raises:
            TelegramError: If message sending fails

        Example:
            >>> await service.send_confirmation(
            ...     chat_id=123456789,
            ...     transaction=income_tx,
            ...     category=None
            ... )
        """
        logger.info(
            "Sending transaction confirmation",
            chat_id=chat_id,
            transaction_id=transaction.transaction_id,
            transaction_type=transaction.type,
        )

        try:
            if transaction.type == "income":
                message = self._format_income_confirmation(transaction)
            else:
                message = self._format_expense_confirmation(transaction, category)

            await self.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)

            logger.info(
                "Transaction confirmation sent successfully",
                chat_id=chat_id,
                transaction_id=transaction.transaction_id,
            )

        except Exception as e:
            logger.exception(
                "Failed to send transaction confirmation",
                chat_id=chat_id,
                transaction_id=transaction.transaction_id,
                error=str(e),
            )
            raise

    def _format_income_confirmation(self, transaction: Transaction) -> str:
        """Format income transaction confirmation message.

        Args:
            transaction: Income transaction to format

        Returns:
            Formatted message string with HTML markup
        """
        amount = format_currency(transaction.amount)
        timestamp = format_wita_datetime(transaction.timestamp)

        return (
            f"💰 <b>Income Recorded</b>\n\n"
            f"<b>Amount:</b> <code>{amount}</code>\n"
            f"<b>Category:</b> Income\n"
            f"<b>Description:</b> {transaction.description}\n"
            f"<b>Date:</b> {timestamp}\n"
            f"<b>ID:</b> <code>{transaction.transaction_id}</code>\n\n"
            f"✅ Transaction saved successfully"
        )

    def _format_expense_confirmation(
        self, transaction: Transaction, category: Optional[Category]
    ) -> str:
        """Format expense transaction confirmation message.

        Args:
            transaction: Expense transaction to format
            category: Category object with emoji and name

        Returns:
            Formatted message string with HTML markup
        """
        amount = format_currency(transaction.amount)
        timestamp = format_wita_datetime(transaction.timestamp)

        # Get category info
        if category:
            category_display = f"{category.emoji} {category.name}"
        else:
            category_display = "Other"

        return (
            f"💸 <b>Expense Recorded</b>\n\n"
            f"<b>Amount:</b> <code>{amount}</code>\n"
            f"<b>Category:</b> {category_display}\n"
            f"<b>Description:</b> {transaction.description}\n"
            f"<b>Date:</b> {timestamp}\n"
            f"<b>ID:</b> <code>{transaction.transaction_id}</code>\n\n"
            f"✅ Transaction saved successfully"
        )

    async def send_error_message(
        self, chat_id: int, error_message: str, usage_example: Optional[str] = None
    ) -> None:
        """Send error message with optional usage example.

        Args:
            chat_id: Telegram chat ID
            error_message: Error description
            usage_example: Optional usage example to show
        """
        logger.info("Sending error message", chat_id=chat_id, error=error_message)

        message = f"❌ <b>Error</b>\n\n{error_message}"

        if usage_example:
            message += f"\n\n<b>Example:</b>\n<code>{usage_example}</code>"

        try:
            await self.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.exception("Failed to send error message", chat_id=chat_id, error=str(e))

    async def send_prompt(
        self, chat_id: int, prompt_type: str, examples: Optional[list[str]] = None
    ) -> None:
        """Send prompt message for interactive input flow.

        Args:
            chat_id: Telegram chat ID
            prompt_type: Type of prompt ('amount', 'description', 'category')
            examples: Optional list of example inputs
        """
        logger.info("Sending prompt message", chat_id=chat_id, prompt_type=prompt_type)

        if prompt_type == "amount":
            message = (
                "💰 <b>Enter Transaction Amount</b>\n\n"
                "Please enter the amount in Rupiah (numbers only):\n\n"
                "<b>Examples:</b>\n"
                "• 500000\n"
                "• 1500000\n"
                "• 2500000\n\n"
                "Or send /cancel to abort"
            )
        elif prompt_type == "description":
            message = (
                "📝 <b>Enter Description</b>\n\n"
                "Please enter a description for this transaction:\n\n"
                "<b>Examples:</b>\n"
                "• Client payment for Project A\n"
                "• Office supplies purchase\n"
                "• Monthly salary payment\n\n"
                "Or send /skip to use default description"
            )
        elif prompt_type == "category":
            message = "📂 <b>Select Category</b>\n\n" "Please select a category for this expense:"
        else:
            message = f"Please provide {prompt_type}"

        try:
            await self.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.exception(
                "Failed to send prompt message",
                chat_id=chat_id,
                prompt_type=prompt_type,
                error=str(e),
            )
            raise

    async def send_daily_report_with_retry(
        self,
        chat_id: int,
        report_text: str,
        max_retries: int = 6,
        retry_interval: int = 300,
    ) -> None:
        """Send daily report with retry logic per FR-018.

        Retries delivery on network failures with 5-minute intervals.
        Maximum retry window is 30 minutes (6 attempts total).

        Args:
            chat_id: Telegram chat ID to send report to
            report_text: Formatted report message
            max_retries: Maximum retry attempts (default 6 = 30 min window)
            retry_interval: Seconds between retries (default 300 = 5 min)

        Raises:
            TelegramError: If delivery fails after all retries

        Example:
            >>> await service.send_daily_report_with_retry(
            ...     chat_id=123456789,
            ...     report_text="Daily Report..."
            ... )
        """
        from telegram.error import NetworkError, TimedOut
        import asyncio

        logger.info(
            "Sending daily report with retry",
            chat_id=chat_id,
            max_retries=max_retries,
            retry_interval=retry_interval,
        )

        for attempt in range(max_retries):
            try:
                await self.bot.send_message(
                    chat_id=chat_id, text=report_text, parse_mode=ParseMode.HTML
                )

                logger.info(
                    "Daily report sent successfully",
                    chat_id=chat_id,
                    attempt=attempt + 1,
                )
                return

            except (NetworkError, TimedOut) as e:
                logger.warning(
                    "Daily report delivery failed, will retry",
                    chat_id=chat_id,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                )

                if attempt < max_retries - 1:
                    # Wait before retry (except on last attempt)
                    await asyncio.sleep(retry_interval)
                else:
                    # Final attempt failed
                    logger.error(
                        "Daily report delivery failed after all retries",
                        chat_id=chat_id,
                        total_attempts=max_retries,
                    )
                    raise

            except Exception as e:
                # Non-retryable error
                logger.exception(
                    "Daily report delivery failed with non-retryable error",
                    chat_id=chat_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
                raise
