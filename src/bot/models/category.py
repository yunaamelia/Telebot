"""Category model with SQLAlchemy ORM.

Represents transaction categories (Income, Operational, Salaries, etc.).
"""
from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from src.database.session import Base


class Category(Base):
    """Category model for transaction classification.

    Attributes:
        category_id: Primary key
        name: Category name (unique)
        type: Category type ('income' or 'expense')
        emoji: Emoji representation for UI
        sort_order: Display order in category lists
        is_active: Whether category is active
        created_at: Record creation timestamp
    """

    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(20), nullable=False)
    emoji = Column(String(10))
    sort_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (CheckConstraint("type IN ('income', 'expense')", name="chk_category_type"),)

    def display_name(self) -> str:
        """Return formatted display name with emoji.

        Returns:
            Category name with emoji prefix (e.g., "💰 Income")
        """
        if self.emoji:
            return f"{self.emoji} {self.name}"
        return self.name

    def __repr__(self) -> str:
        """Return string representation of Category."""
        return (
            f"<Category(category_id={self.category_id}, "
            f"name='{self.name}', "
            f"type='{self.type}')>"
        )
