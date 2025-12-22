"""Transaction command handlers for income and expense recording.

Handles /income and /expense commands with both command-based and interactive modes.
"""
import structlog
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler

from bot.repositories.category_repository import CategoryRepository
from bot.repositories.user_repository import UserRepository
from bot.services.notification_service import NotificationService
from bot.services.transaction_service import TransactionService
from bot.utils.validators import AmountValidationError
from bot.utils.validators import parse_amount


logger = structlog.get_logger(__name__)


# Conversation states
AMOUNT, DESCRIPTION, CATEGORY, CONFIRM_DUPLICATE = range(4)


# Service instances (initialized in main)
transaction_service: TransactionService = None
notification_service: NotificationService = None
user_repository: UserRepository = None
category_repository: CategoryRepository = None


def init_services(
    trans_service: TransactionService,
    notif_service: NotificationService,
    user_repo: UserRepository,
    category_repo: CategoryRepository,
):
    """Initialize service instances for handlers.

    Args:
        trans_service: Transaction service instance
        notif_service: Notification service instance
        user_repo: User repository instance
        category_repo: Category repository instance
    """
    global transaction_service, notification_service, user_repository, category_repository
    transaction_service = trans_service
    notification_service = notif_service
    user_repository = user_repo
    category_repository = category_repo


async def get_user_by_telegram_id(telegram_id: int):
    """Get user by Telegram ID.

    Args:
        telegram_id: Telegram user ID

    Returns:
        User object or None if not found
    """
    return await user_repository.find_by_telegram_id(telegram_id)


async def income_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /income command for recording income transactions.

    Supports two modes:
    1. Command mode: /income 500000 Client payment
    2. Interactive mode: /income (then prompts for amount and description)

    Args:
        update: Telegram update object
        context: Bot context

    Returns:
        ConversationHandler state or END
    """
    user_telegram_id = update.effective_user.id
    message_text = update.message.text

    logger.info(
        "Income command received",
        telegram_id=user_telegram_id,
        username=update.effective_user.username,
        message=message_text,
    )

    # Get user from database
    user = await get_user_by_telegram_id(user_telegram_id)

    if not user:
        logger.warning("Unauthorized income command attempt", telegram_id=user_telegram_id)
        await update.message.reply_text(
            "❌ You are not authorized to use this bot.\n\n"
            "Please contact the administrator to register.",
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    # Parse command arguments
    parts = message_text.split(maxsplit=2)  # /income amount description

    # Interactive mode - no arguments provided
    if len(parts) == 1:
        await notification_service.send_prompt(
            chat_id=update.effective_chat.id, prompt_type="amount"
        )
        context.user_data["transaction_type"] = "income"
        context.user_data["user"] = user
        return AMOUNT

    # Command mode - amount provided
    if len(parts) >= 2:
        amount_str = parts[1]
        description = parts[2] if len(parts) > 2 else None

        try:
            # Parse and validate amount
            amount = parse_amount(amount_str)

            # Record transaction
            transaction = await transaction_service.record_income(
                user=user, amount=amount, description=description
            )

            # Send confirmation
            await notification_service.send_confirmation(
                chat_id=update.effective_chat.id, transaction=transaction
            )

            logger.info(
                "Income transaction recorded via command",
                transaction_id=transaction.transaction_id,
                user_id=user.user_id,
                amount=str(amount),
            )

            return ConversationHandler.END

        except AmountValidationError as e:
            logger.warning(
                "Invalid amount in income command",
                telegram_id=user_telegram_id,
                amount_str=amount_str,
                error=str(e),
            )
            await notification_service.send_error_message(
                chat_id=update.effective_chat.id,
                error_message=str(e),
                usage_example="/income 500000 Client payment",
            )
            return ConversationHandler.END

        except Exception as e:
            logger.exception(
                "Error processing income command",
                telegram_id=user_telegram_id,
                error=str(e),
            )
            await update.message.reply_text(
                "❌ An error occurred while processing your transaction. Please try again.",
                parse_mode=ParseMode.HTML,
            )
            return ConversationHandler.END


async def income_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input in interactive income flow.

    Args:
        update: Telegram update object
        context: Bot context

    Returns:
        Next conversation state (DESCRIPTION) or current state (AMOUNT) on error
    """
    amount_str = update.message.text
    user = context.user_data.get("user")

    logger.info(
        "Amount received in interactive flow",
        user_id=user.user_id if user else None,
        amount_str=amount_str,
    )

    try:
        # Parse and validate amount
        amount = parse_amount(amount_str)

        # Store in context
        context.user_data["amount"] = amount

        # Ask for description
        await notification_service.send_prompt(
            chat_id=update.effective_chat.id, prompt_type="description"
        )

        return DESCRIPTION

    except AmountValidationError as e:
        logger.warning(
            "Invalid amount in interactive flow",
            user_id=user.user_id if user else None,
            amount_str=amount_str,
            error=str(e),
        )
        await notification_service.send_error_message(
            chat_id=update.effective_chat.id,
            error_message=str(e),
            usage_example="500000",
        )
        # Stay in AMOUNT state
        return AMOUNT


async def income_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle description input in interactive income flow.

    Args:
        update: Telegram update object
        context: Bot context

    Returns:
        ConversationHandler.END after recording transaction
    """
    description_text = update.message.text
    user = context.user_data.get("user")
    amount = context.user_data.get("amount")

    logger.info(
        "Description received in interactive flow",
        user_id=user.user_id if user else None,
        has_description=description_text != "/skip",
    )

    # Handle skip
    if description_text == "/skip":
        description = None
    else:
        description = description_text

    try:
        # Record transaction
        transaction = await transaction_service.record_income(
            user=user, amount=amount, description=description
        )

        # Send confirmation
        await notification_service.send_confirmation(
            chat_id=update.effective_chat.id, transaction=transaction
        )

        logger.info(
            "Income transaction recorded via interactive flow",
            transaction_id=transaction.transaction_id,
            user_id=user.user_id,
            amount=str(amount),
        )

        # Clear context
        context.user_data.clear()

        return ConversationHandler.END

    except Exception as e:
        logger.exception(
            "Error recording income transaction",
            user_id=user.user_id if user else None,
            error=str(e),
        )
        await update.message.reply_text(
            "❌ An error occurred while processing your transaction. Please try again.",
            parse_mode=ParseMode.HTML,
        )
        context.user_data.clear()
        return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command to abort interactive flow.

    Args:
        update: Telegram update object
        context: Bot context

    Returns:
        ConversationHandler.END
    """
    logger.info("Transaction cancelled by user", telegram_id=update.effective_user.id)

    await update.message.reply_text("❌ Transaction cancelled.", parse_mode=ParseMode.HTML)

    context.user_data.clear()
    return ConversationHandler.END


# =============================================================================
# Expense Handlers
# =============================================================================


async def expense_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /expense command for recording expense transactions.

    Supports three modes:
    1. Command mode: /expense 250000 Office supplies
    2. Interactive mode: /expense (prompts for amount → description → category)
    3. Quick category shortcuts: /expense_supplies 250000 Paper

    Args:
        update: Telegram update object
        context: Bot context

    Returns:
        ConversationHandler state or END
    """
    user_telegram_id = update.effective_user.id
    message_text = update.message.text

    logger.info(
        "Expense command received",
        telegram_id=user_telegram_id,
        username=update.effective_user.username,
        message=message_text,
    )

    # Get user from database
    user = await get_user_by_telegram_id(user_telegram_id)

    if not user:
        logger.warning("Unauthorized expense command attempt", telegram_id=user_telegram_id)
        await update.message.reply_text(
            "❌ You are not authorized to use this bot.\n\n"
            "Please contact the administrator to register.",
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    # Check for quick category shortcuts (e.g., /expense_supplies)
    command = message_text.split()[0].lower()
    category_shortcuts = {
        "/expense_operational": 2,
        "/expense_salaries": 3,
        "/expense_supplies": 4,
        "/expense_marketing": 5,
        "/expense_other": 6,
    }

    quick_category_id = category_shortcuts.get(command)

    # Parse command arguments
    parts = message_text.split(maxsplit=2)

    # Interactive mode - no arguments
    if len(parts) == 1 and not quick_category_id:
        await notification_service.send_prompt(
            chat_id=update.effective_chat.id, prompt_type="amount"
        )
        context.user_data["transaction_type"] = "expense"
        context.user_data["user"] = user
        return AMOUNT

    # Command mode with amount
    if len(parts) >= 2:
        amount_str = parts[1]
        description = parts[2] if len(parts) > 2 else "Uncategorized expense"

        try:
            # Parse and validate amount
            amount = parse_amount(amount_str)

            # If quick category shortcut, record immediately
            if quick_category_id:
                transaction = await transaction_service.record_expense(
                    user=user,
                    amount=amount,
                    category_id=quick_category_id,
                    description=description,
                )

                await notification_service.send_confirmation(
                    chat_id=update.effective_chat.id, transaction=transaction
                )

                logger.info(
                    "Expense transaction recorded via quick shortcut",
                    transaction_id=transaction.transaction_id,
                    user_id=user.user_id,
                    category_id=quick_category_id,
                )

                return ConversationHandler.END

            # Otherwise, show category selection
            context.user_data["amount"] = amount
            context.user_data["description"] = description
            context.user_data["user"] = user

            # Get expense categories
            categories = await category_repository.find_by_type("expense")

            # Import here to avoid circular dependency
            from bot.keyboards.categories import create_expense_category_keyboard

            keyboard = create_expense_category_keyboard(categories)

            await update.message.reply_text(
                "📂 <b>Select Category</b>\n\n" "Choose the expense category:",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

            return CATEGORY

        except AmountValidationError as e:
            logger.warning(
                "Invalid amount in expense command",
                telegram_id=user_telegram_id,
                amount_str=amount_str,
                error=str(e),
            )
            await notification_service.send_error_message(
                chat_id=update.effective_chat.id,
                error_message=str(e),
                usage_example="/expense 250000 Office supplies",
            )
            return ConversationHandler.END

        except Exception as e:
            logger.exception(
                "Error processing expense command",
                telegram_id=user_telegram_id,
                error=str(e),
            )
            await update.message.reply_text(
                "❌ An error occurred while processing your transaction. Please try again.",
                parse_mode=ParseMode.HTML,
            )
            return ConversationHandler.END


async def expense_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input in interactive expense flow.

    Args:
        update: Telegram update object
        context: Bot context

    Returns:
        Next conversation state (DESCRIPTION)
    """
    amount_str = update.message.text
    user = context.user_data.get("user")

    logger.info(
        "Expense amount received in interactive flow",
        user_id=user.user_id if user else None,
        amount_str=amount_str,
    )

    try:
        amount = parse_amount(amount_str)
        context.user_data["amount"] = amount

        await notification_service.send_prompt(
            chat_id=update.effective_chat.id, prompt_type="description"
        )

        return DESCRIPTION

    except AmountValidationError as e:
        logger.warning(
            "Invalid amount in interactive expense flow",
            user_id=user.user_id if user else None,
            error=str(e),
        )
        await notification_service.send_error_message(
            chat_id=update.effective_chat.id,
            error_message=str(e),
            usage_example="250000",
        )
        return AMOUNT


async def expense_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle description input in interactive expense flow.

    Args:
        update: Telegram update object
        context: Bot context

    Returns:
        Next conversation state (CATEGORY)
    """
    description_text = update.message.text
    user = context.user_data.get("user")

    logger.info(
        "Expense description received",
        user_id=user.user_id if user else None,
        has_description=description_text != "/skip",
    )

    # Handle skip or use provided description
    if description_text == "/skip":
        description = "Uncategorized expense"
    else:
        description = description_text

    context.user_data["description"] = description

    # Show category selection
    categories = await category_repository.find_by_type("expense")

    from bot.keyboards.categories import create_expense_category_keyboard

    keyboard = create_expense_category_keyboard(categories)

    await update.message.reply_text(
        "📂 <b>Select Category</b>\n\n" "Choose the expense category:",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )

    return CATEGORY


async def expense_category_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle category selection callback for expense transactions.

    Args:
        update: Telegram update object (callback query)
        context: Bot context

    Returns:
        ConversationHandler.END after recording transaction
    """
    query = update.callback_query
    await query.answer()

    user = context.user_data.get("user")
    amount = context.user_data.get("amount")
    description = context.user_data.get("description")

    # Parse category ID from callback data (format: "category_{id}")
    callback_data = query.data
    category_id = int(callback_data.split("_")[1])

    logger.info(
        "Category selected for expense",
        user_id=user.user_id if user else None,
        category_id=category_id,
    )

    try:
        # Record expense transaction
        transaction = await transaction_service.record_expense(
            user=user,
            amount=amount,
            category_id=category_id,
            description=description,
        )

        # Send confirmation
        await notification_service.send_confirmation(
            chat_id=query.message.chat_id, transaction=transaction
        )

        logger.info(
            "Expense transaction recorded",
            transaction_id=transaction.transaction_id,
            user_id=user.user_id,
            category_id=category_id,
        )

        # Clear context
        context.user_data.clear()

        return ConversationHandler.END

    except Exception as e:
        logger.exception(
            "Error recording expense transaction",
            user_id=user.user_id if user else None,
            error=str(e),
        )
        await query.message.reply_text(
            "❌ An error occurred while processing your transaction. Please try again.",
            parse_mode=ParseMode.HTML,
        )
        context.user_data.clear()
        return ConversationHandler.END
