"""User model with SQLAlchemy ORM.

Represents authorized bot users with registration approval workflow.
"""
from sqlalchemy import BigInteger
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.session import Base


class User(Base):
    """User model for bot user management and authorization.

    Attributes:
        user_id: Primary key
        telegram_id: Telegram user ID (unique)
        telegram_username: Telegram username (optional)
        display_name: User display name
        employee_id: Company employee ID for registration verification
        status: Registration status ('pending', 'approved', 'rejected')
        role: User role ('staff', 'management', 'admin')
        registration_request_date: When user requested registration
        approved_date: When user was approved
        approved_by_user_id: User ID who approved this user
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255))
    display_name = Column(String(255))
    employee_id = Column(String(100))
    status = Column(String(20), nullable=False, default="pending")
    role = Column(String(20), nullable=False, default="staff")
    registration_request_date = Column(DateTime(timezone=True), server_default=func.now())
    approved_date = Column(DateTime(timezone=True))
    approved_by_user_id = Column(Integer, ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="user", lazy="select")
    approver = relationship("User", remote_side=[user_id], uselist=False)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="chk_status"),
        CheckConstraint("role IN ('staff', 'management', 'admin')", name="chk_role"),
    )

    def is_authorized(self) -> bool:
        """Check if user can access bot features.

        Returns:
            True if user status is 'approved', False otherwise
        """
        return self.status == "approved"

    def is_admin(self) -> bool:
        """Check if user has admin privileges.

        Returns:
            True if user role is 'admin', False otherwise
        """
        return self.role == "admin"

    def is_management(self) -> bool:
        """Check if user has management privileges.

        Returns:
            True if user role is 'management' or 'admin', False otherwise
        """
        return self.role in ("management", "admin")

    def __repr__(self) -> str:
        """Return string representation of User."""
        return (
            f"<User(user_id={self.user_id}, "
            f"telegram_id={self.telegram_id}, "
            f"status='{self.status}', "
            f"role='{self.role}')>"
        )
