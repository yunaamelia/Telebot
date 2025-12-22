"""Notification service for sending messages to users.

Handles transaction confirmations, reports, and system notifications.
"""
from typing import Optional

import structlog
from telegram import Bot
from telegram.constants import ParseMode

from bot.models.category import Category
from bot.models.transaction import Transaction
from bot.utils.formatters import format_currency
from bot.utils.timezone import format_datetime_wita


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
        self, chat_id: int, transaction: Transaction, category: Optional[Category] = None
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
        timestamp = format_datetime_wita(transaction.timestamp)

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
        timestamp = format_datetime_wita(transaction.timestamp)

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
