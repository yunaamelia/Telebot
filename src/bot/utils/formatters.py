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
