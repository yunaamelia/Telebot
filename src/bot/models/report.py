"""Daily summary and report models with SQLAlchemy ORM.

Represents pre-computed daily financial summaries for fast report generation.
"""
from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Dict
from typing import Optional

from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from src.database.session import Base


class DailySummary(Base):
    """Daily summary model for aggregated financial data.

    Attributes:
        summary_id: Primary key
        summary_date: Date of the summary (unique)
        total_income: Sum of all income transactions
        total_expenses: Sum of all expense transactions
        net_cash_flow: Computed column (total_income - total_expenses)
        transaction_count: Total number of transactions
        income_count: Number of income transactions
        expense_count: Number of expense transactions
        category_breakdown: JSONB with amounts per category
        generated_at: When summary was generated
        report_delivered_at: When daily report was delivered
    """

    __tablename__ = "daily_summaries"

    summary_id = Column(Integer, primary_key=True)
    summary_date = Column(Date, unique=True, nullable=False)
    total_income = Column(Numeric(15, 2), nullable=False, default=0)
    total_expenses = Column(Numeric(15, 2), nullable=False, default=0)
    # net_cash_flow is a computed column in PostgreSQL
    transaction_count = Column(Integer, nullable=False, default=0)
    income_count = Column(Integer, nullable=False, default=0)
    expense_count = Column(Integer, nullable=False, default=0)
    category_breakdown = Column(JSONB)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    report_delivered_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "total_income >= 0 AND total_expenses >= 0", name="chk_amounts_non_negative"
        ),
    )

    @property
    def net_cash_flow(self) -> Decimal:
        """Calculate net cash flow (income - expenses).

        Note: This is also computed by PostgreSQL as a GENERATED column,
        but we provide a Python property for when loading from non-DB sources.

        Returns:
            Net cash flow amount
        """
        return Decimal(self.total_income) - Decimal(self.total_expenses)

    @property
    def formatted_income(self) -> str:
        """Format total income with Rupiah currency.

        Returns:
            Formatted income string (e.g., "Rp 2,500,000")
        """
        return f"Rp {self.total_income:,.0f}"

    @property
    def formatted_expenses(self) -> str:
        """Format total expenses with Rupiah currency.

        Returns:
            Formatted expenses string (e.g., "Rp 1,200,000")
        """
        return f"Rp {self.total_expenses:,.0f}"

    @property
    def formatted_net_cash_flow(self) -> str:
        """Format net cash flow with Rupiah currency and sign.

        Returns:
            Formatted net cash flow with + or - (e.g., "+Rp 1,300,000" or "-Rp 500,000")
        """
        net = self.net_cash_flow
        sign = "+" if net >= 0 else ""
        return f"{sign}Rp {net:,.0f}"

    def is_positive_cash_flow(self) -> bool:
        """Check if net cash flow is positive.

        Returns:
            True if net cash flow >= 0, False otherwise
        """
        return self.net_cash_flow >= 0

    def has_transactions(self) -> bool:
        """Check if summary has any transactions.

        Returns:
            True if transaction_count > 0, False otherwise
        """
        return self.transaction_count > 0

    def get_category_amount(self, category_name: str) -> Decimal:
        """Get amount for specific category from breakdown.

        Args:
            category_name: Name of the category

        Returns:
            Amount for the category, or 0 if not found
        """
        if not self.category_breakdown:
            return Decimal(0)

        return Decimal(self.category_breakdown.get(category_name, 0))

    def __repr__(self) -> str:
        """String representation of DailySummary."""
        return (
            f"<DailySummary(summary_id={self.summary_id}, "
            f"date={self.summary_date}, "
            f"income={self.total_income}, "
            f"expenses={self.total_expenses}, "
            f"net={self.net_cash_flow})>"
        )
