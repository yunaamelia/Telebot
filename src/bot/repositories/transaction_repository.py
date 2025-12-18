"""Transaction repository with duplicate detection.

Provides CRUD and query operations for Transaction model.
"""
from datetime import date
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from typing import List
from typing import Optional
from typing import Tuple

from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.models.transaction import Transaction
from src.config.logging import get_logger

logger = get_logger(__name__)


class TransactionRepository:
    """Repository for Transaction model database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize transaction repository.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(
        self,
        transaction_id: str,
        user_id: int,
        category_id: int,
        amount: Decimal,
        transaction_type: str,
        description: Optional[str],
        timestamp: datetime,
        transaction_date: date,
        is_duplicate_confirmed: bool = False,
    ) -> Transaction:
        """Create a new transaction.

        Args:
            transaction_id: Transaction ID (TX20251218001)
            user_id: Foreign key to users table
            category_id: Foreign key to categories table
            amount: Transaction amount
            transaction_type: Transaction type ('income' or 'expense')
            description: Optional description
            timestamp: UTC timestamp
            transaction_date: WITA date
            is_duplicate_confirmed: Whether duplicate was confirmed

        Returns:
            Created Transaction instance
        """
        transaction = Transaction(
            transaction_id=transaction_id,
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            type=transaction_type,
            description=description,
            timestamp=timestamp,
            transaction_date=transaction_date,
            status="recorded",
            is_duplicate_confirmed=is_duplicate_confirmed,
        )

        self.session.add(transaction)
        await self.session.flush()

        logger.info(
            "Transaction created",
            extra={
                "transaction_id": transaction_id,
                "user_id": user_id,
                "type": transaction_type,
                "amount": float(amount),
                "category_id": category_id,
            },
        )

        return transaction

    async def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID.

        Args:
            transaction_id: Transaction primary key

        Returns:
            Transaction instance if found, None otherwise
        """
        result = await self.session.execute(
            select(Transaction).where(Transaction.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def find_duplicate(
        self,
        user_id: int,
        amount: Decimal,
        description: Optional[str],
        category_id: int,
        window_seconds: Optional[int] = None,
    ) -> Optional[Transaction]:
        """Find potential duplicate transaction within time window.

        Args:
            user_id: User ID
            amount: Transaction amount
            description: Transaction description
            category_id: Category ID
            window_seconds: Time window in seconds (default from settings)

        Returns:
            Duplicate Transaction if found, None otherwise
        """
        from src.config.settings import get_settings

        if window_seconds is None:
            window_seconds = get_settings().duplicate_detection_window_seconds

        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)

        # Match on same user, amount, description, category within time window
        result = await self.session.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.amount == amount,
                    Transaction.description == description,
                    Transaction.category_id == category_id,
                    Transaction.timestamp >= cutoff_time,
                    Transaction.status == "recorded",
                )
            )
            .order_by(desc(Transaction.timestamp))
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def get_daily_count(self, transaction_date: date) -> int:
        """Get count of transactions for a specific date.

        Used for generating sequential transaction IDs.

        Args:
            transaction_date: Date to count transactions for

        Returns:
            Number of transactions on that date
        """
        result = await self.session.execute(
            select(func.count(Transaction.transaction_id)).where(
                Transaction.transaction_date == transaction_date
            )
        )
        return result.scalar_one()

    async def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None,
        category_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
    ) -> list[Transaction]:
        """Get transactions within date range with optional filters.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            user_id: Filter by user ID (optional)
            category_id: Filter by category ID (optional)
            transaction_type: Filter by type ('income' or 'expense', optional)

        Returns:
            List of Transaction instances ordered by timestamp DESC
        """
        query = select(Transaction).where(
            and_(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.status == "recorded",
            )
        )

        if user_id is not None:
            query = query.where(Transaction.user_id == user_id)

        if category_id is not None:
            query = query.where(Transaction.category_id == category_id)

        if transaction_type is not None:
            query = query.where(Transaction.type == transaction_type)

        query = query.order_by(desc(Transaction.timestamp))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_history(
        self,
        user_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        """Get transaction history with pagination.

        Args:
            user_id: Filter by user ID (optional)
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Tuple of (transactions list, total count)
        """
        # Base query
        base_query = select(Transaction).where(Transaction.status == "recorded")

        if user_id is not None:
            base_query = base_query.where(Transaction.user_id == user_id)

        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total_count = count_result.scalar_one()

        # Get paginated results
        query = base_query.order_by(desc(Transaction.timestamp)).limit(limit).offset(offset)

        result = await self.session.execute(query)
        transactions = list(result.scalars().all())

        return transactions, total_count

    async def archive_old_transactions(
        self,
        cutoff_date: date,
    ) -> int:
        """Archive transactions older than cutoff date.

        Args:
            cutoff_date: Transactions before this date will be archived

        Returns:
            Number of transactions archived
        """
        result = await self.session.execute(
            select(Transaction).where(
                and_(
                    Transaction.transaction_date < cutoff_date,
                    Transaction.status == "recorded",
                )
            )
        )
        transactions = list(result.scalars().all())

        for transaction in transactions:
            transaction.status = "archived"

        await self.session.flush()

        logger.info(
            "Transactions archived",
            extra={
                "count": len(transactions),
                "cutoff_date": cutoff_date.isoformat(),
            },
        )

        return len(transactions)

    async def delete_old_archived(
        self,
        cutoff_date: date,
    ) -> int:
        """Delete archived transactions older than cutoff date.

        Args:
            cutoff_date: Archived transactions before this date will be deleted

        Returns:
            Number of transactions deleted
        """
        result = await self.session.execute(
            select(Transaction).where(
                and_(
                    Transaction.transaction_date < cutoff_date,
                    Transaction.status == "archived",
                )
            )
        )
        transactions = list(result.scalars().all())

        for transaction in transactions:
            await self.session.delete(transaction)

        await self.session.flush()

        logger.info(
            "Archived transactions deleted",
            extra={
                "count": len(transactions),
                "cutoff_date": cutoff_date.isoformat(),
            },
        )

        return len(transactions)
