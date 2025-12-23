"""Transaction model with SQLAlchemy ORM.

Represents financial transactions (income and expenses) with comprehensive validation.
"""
from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.session import Base


class Transaction(Base):
    """Transaction model for financial record keeping.

    Attributes:
        transaction_id: Primary key (format: TX20251218001)
        user_id: Foreign key to users table
        category_id: Foreign key to categories table
        amount: Transaction amount (max 10 billion)
        type: Transaction type ('income' or 'expense')
        description: Optional transaction description
        timestamp: UTC timestamp when transaction recorded
        transaction_date: WITA date for daily reports
        status: Transaction status ('recorded', 'archived', 'deleted')
        is_duplicate_confirmed: Whether user confirmed duplicate warning
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """

    __tablename__ = "transactions"

    transaction_id = Column(String(50), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    type = Column(String(20), nullable=False)
    description = Column(Text)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    transaction_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="recorded")
    is_duplicate_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", lazy="joined")  # Always load category with transaction

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_amount_positive"),
        CheckConstraint("amount <= 10000000000", name="chk_amount_max"),
        CheckConstraint("type IN ('income', 'expense')", name="chk_type"),
        CheckConstraint("status IN ('recorded', 'archived', 'deleted')", name="chk_status"),
    )

    @property
    def formatted_amount(self) -> str:
        """Format amount with Rupiah currency formatting.

        Returns:
            Formatted amount string (e.g., "Rp 1,500,000")
        """
        return f"Rp {self.amount:,.0f}"

    def is_active(self) -> bool:
        """Check if transaction is active (not archived or deleted).

        Returns:
            True if status is 'recorded', False otherwise
        """
        return self.status == "recorded"

    def is_income(self) -> bool:
        """Check if transaction is income.

        Returns:
            True if type is 'income', False otherwise
        """
        return self.type == "income"

    def is_expense(self) -> bool:
        """Check if transaction is expense.

        Returns:
            True if type is 'expense', False otherwise
        """
        return self.type == "expense"

    def __repr__(self) -> str:
        """Return string representation of Transaction."""
        return (
            f"<Transaction(transaction_id='{self.transaction_id}', "
            f"type='{self.type}', "
            f"amount={self.amount}, "
            f"date={self.transaction_date})>"
        )
