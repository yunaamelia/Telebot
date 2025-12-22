"""Transaction service business logic.

Handles income and expense transaction recording with validation.
"""
from decimal import Decimal
from typing import Optional

import structlog

from src.bot.models.transaction import Transaction
from src.bot.models.user import User
from src.bot.repositories.transaction_repository import TransactionRepository
from src.bot.utils.formatters import generate_transaction_id
from src.bot.utils.timezone import get_current_wita_datetime
from src.bot.utils.validators import AmountValidationError
from src.bot.utils.validators import validate_amount


logger = structlog.get_logger(__name__)


class TransactionService:
    """Service for managing financial transactions."""

    # Income category ID (from seed data)
    INCOME_CATEGORY_ID = 1

    # Maximum description length (characters)
    MAX_DESCRIPTION_LENGTH = 500

    # Duplicate detection window (seconds)
    DUPLICATE_WINDOW_SECONDS = 60

    def __init__(self, repository: TransactionRepository):
        """Initialize transaction service.

        Args:
            repository: Transaction repository for data access
        """
        self.repository = repository

    async def record_income(
        self,
        user: User,
        amount: Decimal,
        description: Optional[str] = None,
        skip_duplicate_check: bool = False,
    ) -> Optional[Transaction]:
        """Record income transaction for user.

        Validates amount, checks for duplicates (unless skipped), checks user authorization,
        generates transaction ID, and persists to database. Sends confirmation to user via Telegram.

        Args:
            user: User recording the income
            amount: Transaction amount in Rupiah (must be positive)
            description: Optional transaction description (max 500 chars)
            skip_duplicate_check: If True, skip duplicate detection

        Returns:
            Transaction: Persisted transaction object with generated ID, or None if duplicate found

        Raises:
            AmountValidationError: If amount is invalid (zero, negative, or exceeds limit)
            ValueError: If description exceeds maximum length
            UnauthorizedError: If user is not active
            DuplicateTransactionError: If duplicate found and not confirmed

        Example:
            >>> tx = await service.record_income(
            ...     user=active_user,
            ...     amount=Decimal("500000"),
            ...     description="Client payment"
            ... )
            >>> print(tx.transaction_id)
            TX20251218001
        """
        # Log transaction attempt
        logger.info(
            "Recording income transaction",
            user_id=user.user_id,
            telegram_id=user.telegram_id,
            amount=str(amount),
            has_description=description is not None,
            skip_duplicate_check=skip_duplicate_check,
        )

        # Validate amount
        try:
            validate_amount(amount)
        except AmountValidationError as e:
            logger.warning(
                "Invalid amount for income transaction",
                user_id=user.user_id,
                amount=str(amount),
                error=str(e),
            )
            raise

        # Validate description length
        if description and len(description) > self.MAX_DESCRIPTION_LENGTH:
            error_msg = f"Description too long (max {self.MAX_DESCRIPTION_LENGTH} characters)"
            logger.warning(
                "Description too long",
                user_id=user.user_id,
                description_length=len(description),
                max_length=self.MAX_DESCRIPTION_LENGTH,
            )
            raise ValueError(error_msg)

        # Use default description if none provided
        if not description:
            description = "No description"

        # Verify user is authorized (active status)
        if user.status != "active":
            logger.error(
                "Unauthorized transaction attempt",
                user_id=user.user_id,
                user_status=user.status,
            )
            raise ValueError(f"User is not active (status: {user.status})")

        # Check for duplicates (60-second window)
        if not skip_duplicate_check:
            duplicate = await self.repository.find_duplicate(
                user_id=user.user_id,
                amount=amount,
                description=description,
                category_id=self.INCOME_CATEGORY_ID,
                window_seconds=60,
            )

            if duplicate:
                logger.warning(
                    "Potential duplicate transaction detected",
                    user_id=user.user_id,
                    amount=str(amount),
                    description=description,
                    duplicate_id=duplicate.transaction_id,
                )
                # Return None to signal duplicate found - handler will prompt for confirmation
                return None

        # Get current WITA time
        current_time = get_current_wita_datetime()
        transaction_date = current_time.date()

        # Get daily count for transaction ID sequence
        sequence = await self.repository.get_daily_count(transaction_date)
        sequence += 1  # Next transaction of the day

        # Generate transaction ID
        transaction_id = generate_transaction_id(transaction_date, sequence)

        # Persist to database using repository.create (not Transaction object)
        try:
            persisted_transaction = await self.repository.create(
                transaction_id=transaction_id,
                user_id=user.user_id,
                category_id=self.INCOME_CATEGORY_ID,
                amount=amount,
                transaction_type="income",
                description=description,
                timestamp=current_time,
                transaction_date=transaction_date,
                is_duplicate_confirmed=skip_duplicate_check,
            )

            logger.info(
                "Income transaction recorded successfully",
                transaction_id=transaction_id,
                user_id=user.user_id,
                amount=str(amount),
                category_id=self.INCOME_CATEGORY_ID,
            )

            return persisted_transaction

        except Exception as e:
            logger.exception(
                "Failed to persist income transaction",
                transaction_id=transaction_id,
                user_id=user.user_id,
                error=str(e),
            )
            raise

    async def check_duplicate_income(
        self, user: User, amount: Decimal, description: Optional[str] = None
    ) -> list[Transaction]:
        """Check for duplicate income transactions within 60-second window.

        Per FR-023: Duplicate detection to prevent accidental double-entry.

        Args:
            user: User to check duplicates for
            amount: Transaction amount to check
            description: Optional description to check

        Returns:
            List of potential duplicate transactions (empty if none found)

        Example:
            >>> duplicates = await service.check_duplicate_income(
            ...     user=user,
            ...     amount=Decimal("500000"),
            ...     description="Client payment"
            ... )
            >>> if duplicates:
            ...     # Show warning to user
        """
        return await self.repository.find_duplicates(
            user_id=user.user_id,
            transaction_type="income",
            amount=amount,
            description=description,
            window_seconds=self.DUPLICATE_WINDOW_SECONDS,
        )

    async def check_duplicate_expense(
        self,
        user: User,
        amount: Decimal,
        category_id: int,
        description: Optional[str] = None,
    ) -> list[Transaction]:
        """Check for duplicate expense transactions within 60-second window.

        Per FR-023: Duplicate detection to prevent accidental double-entry.

        Args:
            user: User to check duplicates for
            amount: Transaction amount to check
            category_id: Expense category ID
            description: Optional description to check

        Returns:
            List of potential duplicate transactions (empty if none found)

        Example:
            >>> duplicates = await service.check_duplicate_expense(
            ...     user=user,
            ...     amount=Decimal("250000"),
            ...     category_id=4,
            ...     description="Office supplies"
            ... )
            >>> if duplicates:
            ...     # Show warning to user
        """
        return await self.repository.find_duplicates(
            user_id=user.user_id,
            transaction_type="expense",
            amount=amount,
            category_id=category_id,
            description=description,
            window_seconds=self.DUPLICATE_WINDOW_SECONDS,
        )

    async def record_expense(
        self,
        user: User,
        amount: Decimal,
        category_id: int,
        description: Optional[str] = None,
        is_duplicate_confirmed: bool = False,
    ) -> Transaction:
        """Record expense transaction for user.

        Validates amount and category, generates transaction ID, and persists.

        Args:
            user: User recording the expense
            amount: Transaction amount in Rupiah (must be positive)
            category_id: Expense category ID (2-6)
            description: Optional transaction description (max 500 chars)
            is_duplicate_confirmed: Whether duplicate warning was confirmed

        Returns:
            Transaction: Persisted transaction object with generated ID

        Raises:
            AmountValidationError: If amount is invalid
            ValueError: If category_id is invalid or description too long
        """
        # Log transaction attempt
        logger.info(
            "Recording expense transaction",
            user_id=user.user_id,
            telegram_id=user.telegram_id,
            amount=str(amount),
            category_id=category_id,
            has_description=description is not None,
        )

        # Validate amount
        try:
            validate_amount(amount)
        except AmountValidationError as e:
            logger.warning(
                "Invalid amount for expense transaction",
                user_id=user.user_id,
                amount=str(amount),
                error=str(e),
            )
            raise

        # Validate description length
        if description and len(description) > self.MAX_DESCRIPTION_LENGTH:
            error_msg = f"Description too long (max {self.MAX_DESCRIPTION_LENGTH} characters)"
            logger.warning(
                "Description too long",
                user_id=user.user_id,
                description_length=len(description),
            )
            raise ValueError(error_msg)

        # Use default description if none provided
        if not description:
            description = "Uncategorized expense"

        # Verify user is authorized
        if user.status != "active":
            logger.error(
                "Unauthorized transaction attempt",
                user_id=user.user_id,
                user_status=user.status,
            )
            raise ValueError(f"User is not active (status: {user.status})")

        # Validate category is for expenses (not income)
        if category_id == self.INCOME_CATEGORY_ID:
            raise ValueError("Cannot use income category for expense transaction")

        # Get current WITA time
        current_time = get_current_wita_datetime()
        transaction_date = current_time.date()

        # Get daily sequence number
        sequence = await self.repository.get_daily_sequence(
            user_id=user.user_id, transaction_date=transaction_date
        )

        # Generate transaction ID
        transaction_id = generate_transaction_id(transaction_date, sequence)

        # Create transaction object
        transaction = Transaction(
            transaction_id=transaction_id,
            user_id=user.user_id,
            type="expense",
            amount=amount,
            category_id=category_id,
            description=description,
            timestamp=current_time,
            transaction_date=transaction_date,
            status="completed",
            is_duplicate_confirmed=is_duplicate_confirmed,
        )

        # Persist to database
        try:
            persisted_transaction = await self.repository.create(transaction)

            logger.info(
                "Expense transaction recorded successfully",
                transaction_id=transaction_id,
                user_id=user.user_id,
                amount=str(amount),
                category_id=category_id,
            )

            return persisted_transaction

        except Exception as e:
            logger.exception(
                "Failed to persist expense transaction",
                transaction_id=transaction_id,
                user_id=user.user_id,
                error=str(e),
            )
            raise
