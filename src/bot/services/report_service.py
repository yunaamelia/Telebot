"""Report service for financial summaries and analytics.

Handles daily summary generation with category breakdown per FR-007.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

import structlog

from src.bot.repositories.transaction_repository import TransactionRepository
from src.bot.utils.timezone import get_current_wita_date


logger = structlog.get_logger(__name__)


@dataclass
class DailySummaryData:
    """In-memory daily summary data structure.

    Used for passing summary data between service and formatter.
    """

    summary_date: date
    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    transaction_count: int
    income_count: int
    expense_count: int
    category_breakdown: dict[int, Decimal]


class ReportService:
    """Service for generating financial reports and summaries."""

    def __init__(self, repository: TransactionRepository):
        """Initialize report service.

        Args:
            repository: Transaction repository for data access
        """
        self.repository = repository

    async def generate_daily_summary(self, summary_date: Optional[date] = None) -> DailySummaryData:
        """Generate daily financial summary for specified date.

        Per FR-007: Daily summary includes total income, total expenses,
        net cash flow, transaction count, and category breakdown.

        Args:
            summary_date: Date to generate summary for (defaults to current WITA date)

        Returns:
            DailySummaryData: Financial summary with aggregated data

        Example:
            >>> summary = await service.generate_daily_summary()
            >>> print(f"Net: {summary.net_cash_flow}")
            Decimal("600000")  # Income 2,500,000 - Expenses 1,900,000
        """
        # Default to current WITA date if not specified
        if summary_date is None:
            summary_date = get_current_wita_date()

        logger.info(
            "Generating daily summary",
            summary_date=summary_date.isoformat(),
        )

        # Get all transactions for the date
        transactions = await self.repository.get_by_date_range(
            start_date=summary_date,
            end_date=summary_date,
        )

        # Calculate totals
        total_income = Decimal("0")
        total_expenses = Decimal("0")
        income_count = 0
        expense_count = 0

        # Category breakdown (category_id -> amount)
        category_breakdown = {}

        for transaction in transactions:
            if transaction.type == "income":
                total_income += transaction.amount
                income_count += 1
            elif transaction.type == "expense":
                total_expenses += transaction.amount
                expense_count += 1

                # Add to category breakdown
                category_id = transaction.category_id
                if category_id not in category_breakdown:
                    category_breakdown[category_id] = Decimal("0")
                category_breakdown[category_id] += transaction.amount

        # Calculate net cash flow
        net_cash_flow = total_income - total_expenses

        # Total transaction count
        transaction_count = income_count + expense_count

        # Create summary object
        summary = DailySummaryData(
            summary_date=summary_date,
            total_income=total_income,
            total_expenses=total_expenses,
            net_cash_flow=net_cash_flow,
            transaction_count=transaction_count,
            income_count=income_count,
            expense_count=expense_count,
            category_breakdown=category_breakdown,
        )

        logger.info(
            "Daily summary generated",
            summary_date=summary_date.isoformat(),
            total_income=float(total_income),
            total_expenses=float(total_expenses),
            net_cash_flow=float(net_cash_flow),
            transaction_count=transaction_count,
        )

        return summary
