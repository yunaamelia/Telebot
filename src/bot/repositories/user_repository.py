"""User repository for database operations.

Provides CRUD operations for User model with authorization helpers.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.models.user import User
from src.config.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository for User model database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize user repository.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(
        self,
        telegram_id: int,
        telegram_username: Optional[str] = None,
        display_name: Optional[str] = None,
        employee_id: Optional[str] = None,
    ) -> User:
        """Create a new user with 'pending' status.

        Args:
            telegram_id: Telegram user ID
            telegram_username: Telegram username (optional)
            display_name: User display name (optional)
            employee_id: Company employee ID (optional)

        Returns:
            Created User instance

        Raises:
            IntegrityError: If telegram_id already exists
        """
        user = User(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            display_name=display_name,
            employee_id=employee_id,
            status="pending",
            role="staff",
        )

        self.session.add(user)
        await self.session.flush()

        logger.info(
            "User created",
            extra={
                "user_id": user.user_id,
                "telegram_id": telegram_id,
                "status": user.status,
            },
        )

        return user

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User instance if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User primary key

        Returns:
            User instance if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_approved_users(self) -> list[User]:
        """Get all approved users.

        Returns:
            List of approved User instances
        """
        result = await self.session.execute(
            select(User).where(User.status == "approved").order_by(User.display_name)
        )
        return list(result.scalars().all())

    async def get_pending_users(self) -> list[User]:
        """Get all users pending approval.

        Returns:
            List of pending User instances
        """
        result = await self.session.execute(
            select(User).where(User.status == "pending").order_by(User.registration_request_date)
        )
        return list(result.scalars().all())

    async def approve_user(
        self,
        user_id: int,
        approved_by_user_id: int,
    ) -> Optional[User]:
        """Approve a pending user.

        Args:
            user_id: User ID to approve
            approved_by_user_id: User ID who is approving

        Returns:
            Updated User instance if found, None otherwise
        """
        user = await self.get_by_id(user_id)

        if user is None:
            return None

        from datetime import datetime

        user.status = "approved"
        user.approved_date = datetime.now()
        user.approved_by_user_id = approved_by_user_id

        await self.session.flush()

        logger.info(
            "User approved",
            extra={
                "user_id": user_id,
                "telegram_id": user.telegram_id,
                "approved_by": approved_by_user_id,
            },
        )

        return user

    async def reject_user(self, user_id: int) -> Optional[User]:
        """Reject a pending user.

        Args:
            user_id: User ID to reject

        Returns:
            Updated User instance if found, None otherwise
        """
        user = await self.get_by_id(user_id)

        if user is None:
            return None

        user.status = "rejected"
        await self.session.flush()

        logger.info(
            "User rejected",
            extra={
                "user_id": user_id,
                "telegram_id": user.telegram_id,
            },
        )

        return user

    async def update_role(
        self,
        user_id: int,
        role: str,
    ) -> Optional[User]:
        """Update user role.

        Args:
            user_id: User ID to update
            role: New role ('staff', 'management', 'admin')

        Returns:
            Updated User instance if found, None otherwise

        Raises:
            ValueError: If role is invalid
        """
        if role not in ("staff", "management", "admin"):
            raise ValueError(f"Invalid role: {role}")

        user = await self.get_by_id(user_id)

        if user is None:
            return None

        old_role = user.role
        user.role = role
        await self.session.flush()

        logger.info(
            "User role updated",
            extra={
                "user_id": user_id,
                "old_role": old_role,
                "new_role": role,
            },
        )

        return user

    async def is_authorized(self, telegram_id: int) -> bool:
        """Check if user is authorized to use the bot.

        Args:
            telegram_id: Telegram user ID

        Returns:
            True if user is approved, False otherwise
        """
        user = await self.get_by_telegram_id(telegram_id)
        return user is not None and user.is_authorized()
