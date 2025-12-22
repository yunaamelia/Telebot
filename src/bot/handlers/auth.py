"""Authentication and user management handlers.

Handles /start, /register, and user approval workflows.
"""
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.bot.keyboards.main_menu import create_main_menu_keyboard

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with welcome message and main menu.

    Displays personalized welcome message with inline keyboard showing all
    primary bot actions. Per FR-013 and US5 AS1.

    Args:
        update: Telegram update object
        context: Bot context with user data

    Returns:
        None
    """
    try:
        user = update.effective_user
        user_name = user.first_name if user else "there"

        welcome_message = (
            f"👋 <b>Welcome, {user_name}!</b>\n\n"
            "I'm your Cash Flow Management Bot. I help you track income and expenses "
            "for your business.\n\n"
            "<b>What I can do:</b>\n"
            "💰 Record income transactions\n"
            "💸 Record expense transactions\n"
            "📊 View daily financial summary\n"
            "📋 Browse transaction history\n\n"
            "Choose an option below to get started:"
        )

        keyboard = create_main_menu_keyboard()

        await update.message.reply_text(
            welcome_message, reply_markup=keyboard, parse_mode=ParseMode.HTML
        )

        logger.info(
            "Start command executed",
            extra={
                "user_id": user.id if user else None,
                "username": user.username if user else None,
            },
        )

    except Exception as e:
        logger.exception("Error in start command", extra={"error": str(e)})

        # Fallback message without formatting
        try:
            await update.message.reply_text(
                "Welcome! Something went wrong, but I'm here to help you track "
                "your cash flow. Try using /income or /expense to get started."
            )
        except Exception:
            # If even fallback fails, just log it
            logger.exception("Failed to send fallback start message")
