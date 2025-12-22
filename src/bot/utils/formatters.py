"""Currency formatting and transaction ID generation utilities.

Provides Rupiah currency formatting and transaction ID generation.
"""
import re
from datetime import date
from decimal import Decimal
from typing import Union


def format_currency(amount: Union[Decimal, float, int]) -> str:
    """Format amount as Indonesian Rupiah currency.

    Args:
        amount: Amount to format

    Returns:
        Formatted currency string (e.g., "Rp 1,500,000")

    Examples:
        >>> format_currency(1500000)
        'Rp 1,500,000'
        >>> format_currency(Decimal('250000.50'))
        'Rp 250,000'
        >>> format_currency(0)
        'Rp 0'
    """
    # Convert to Decimal for precision
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))

    # Round to nearest integer (no cents in Rupiah)
    amount_int = int(amount)

    # Format with thousand separators
    formatted = f"{amount_int:,}"

    return f"Rp {formatted}"


def format_currency_with_sign(amount: Union[Decimal, float, int]) -> str:
    """Format amount as currency with explicit + or - sign.

    Useful for displaying net cash flow.

    Args:
        amount: Amount to format

    Returns:
        Formatted currency with sign (e.g., "+Rp 1,500,000" or "-Rp 500,000")

    Examples:
        >>> format_currency_with_sign(1500000)
        '+Rp 1,500,000'
        >>> format_currency_with_sign(-500000)
        '-Rp 500,000'
        >>> format_currency_with_sign(0)
        'Rp 0'
    """
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))

    if amount > 0:
        return f"+{format_currency(amount)}"
    elif amount < 0:
        return f"-{format_currency(abs(amount))}"
    else:
        return format_currency(0)


def generate_transaction_id(transaction_date: date, sequence: int) -> str:
    """Generate sequential transaction ID with date prefix.

    Format: TX{YYYYMMDD}{NNN}
    Example: TX20251218001

    Args:
        transaction_date: Date of the transaction
        sequence: Sequential number for the day (1-based)

    Returns:
        Transaction ID string

    Examples:
        >>> from datetime import date
        >>> generate_transaction_id(date(2025, 12, 18), 1)
        'TX20251218001'
        >>> generate_transaction_id(date(2025, 12, 18), 42)
        'TX20251218042'
    """
    date_str = transaction_date.strftime("%Y%m%d")
    return f"TX{date_str}{sequence:03d}"


def parse_transaction_id(transaction_id: str) -> tuple[date, int]:
    """Parse transaction ID to extract date and sequence.

    Args:
        transaction_id: Transaction ID (e.g., "TX20251218001")

    Returns:
        Tuple of (transaction_date, sequence)

    Raises:
        ValueError: If transaction_id format is invalid

    Examples:
        >>> from datetime import date
        >>> parse_transaction_id("TX20251218001")
        (date(2025, 12, 18), 1)
    """
    match = re.match(r"^TX(\d{8})(\d{3})$", transaction_id)

    if not match:
        raise ValueError(f"Invalid transaction ID format: {transaction_id}")

    date_str, sequence_str = match.groups()

    # Parse date
    year = int(date_str[0:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    transaction_date = date(year, month, day)

    # Parse sequence
    sequence = int(sequence_str)

    return transaction_date, sequence


def format_daily_summary(summary) -> str:
    """Format daily summary as HTML message per contracts/messages.yaml.

    Generates formatted summary with:
    - Date header
    - Total income and expenses
    - Net cash flow with positive/negative indicator
    - Category breakdown (for expenses)
    - Transaction count

    Args:
        summary: DailySummary object with financial data

    Returns:
        Formatted HTML message string

    Example:
        >>> from decimal import Decimal
        >>> from datetime import date
        >>> from bot.models.report import DailySummary
        >>> summary = DailySummary(
        ...     summary_date=date(2025, 12, 18),
        ...     total_income=Decimal("2500000"),
        ...     total_expenses=Decimal("1900000"),
        ...     net_cash_flow=Decimal("600000"),
        ...     transaction_count=12,
        ...     income_count=5,
        ...     expense_count=7,
        ...     category_breakdown={2: Decimal("500000"), 3: Decimal("1000000")}
        ... )
        >>> print(format_daily_summary(summary))
        📊 <b>Daily Financial Summary</b>
        <b>Date:</b> 18 Dec 2025
        ...
    """
    # Handle zero-transaction day (per US3 AS2)
    if summary.transaction_count == 0:
        formatted_date = summary.summary_date.strftime("%d %b %Y")
        return (
            f"📊 <b>Daily Financial Summary</b>\n"
            f"<b>Date:</b> {formatted_date}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"ℹ️ No transactions recorded today\n\n"
            f"Use /income or /expense to record transactions\n"
            f"Or tap the buttons below ⬇️"
        )

    # Format date
    formatted_date = summary.summary_date.strftime("%d %b %Y")

    # Format amounts
    formatted_income = format_currency(summary.total_income)
    formatted_expenses = format_currency(summary.total_expenses)
    formatted_net = format_currency(abs(summary.net_cash_flow))

    # Determine net cash flow indicator (per T076)
    if summary.net_cash_flow >= 0:
        net_indicator = "📈"
        net_sign = "+"
    else:
        net_indicator = "📉"
        net_sign = "-"

    # Build category breakdown (per T071, T077)
    category_lines = []
    if summary.category_breakdown:
        # Need to fetch category details for emoji and name
        # For now, use hardcoded mapping (TODO: fetch from DB in production)
        category_map = {
            2: ("🏢", "Operational"),
            3: ("👔", "Salaries"),
            4: ("📦", "Supplies"),
            5: ("📢", "Marketing"),
            6: ("➕", "Other"),
        }

        for category_id, amount in sorted(summary.category_breakdown.items()):
            emoji, name = category_map.get(category_id, ("📁", "Unknown"))
            formatted_amount = format_currency(amount)
            category_lines.append(f"{emoji} <b>{name}:</b> <code>{formatted_amount}</code>")

    category_breakdown_text = "\n".join(category_lines) if category_lines else "No expenses"

    # Build full message
    message = (
        f"📊 <b>Daily Financial Summary</b>\n"
        f"<b>Date:</b> {formatted_date}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Total Income:</b> <code>{formatted_income}</code>\n"
        f"💸 <b>Total Expenses:</b> <code>{formatted_expenses}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{net_indicator} <b>Net Cash Flow:</b> <code>{net_sign}{formatted_net}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Expense Breakdown:</b>\n"
        f"{category_breakdown_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 <b>Transactions:</b> {summary.transaction_count} total "
        f"({summary.income_count} income, {summary.expense_count} expenses)"
    )

    return message
